"""Components for reading WeeChat logs and gathering statistics from them."""
import re
from dataclasses import dataclass
from datetime import datetime
from multiprocessing import Pool
from os import environ
from pathlib import Path
from typing import (Collection, Counter, Dict, Iterator, List, Mapping,
                    NamedTuple, Optional, Set)

import pandas as pd  # type: ignore  # mypy doesn't have type stubs for pandas yet.

from clogstats.parse import ANSI_ESCAPE, msg_type, strip_nick_prefix

BOT_BLACKLISTS: Dict[str, Set[str]] = {
    "2600net": {"jarvis", "gbot"},
    "darkscience": {"zeta"},
    "efnet": {"pelosi"},
    "freenode": {"mockturtle", "weebot", "imoutobot", "wlb1"},
    "gitter": {"gitter"},
    "gotham": {"mafalda", "southbay", "damon"},
    "rizon": {"internets", "chanstat", "yt-info"},
    "tilde_chat": {"bitbot"},
    "snoonet": {"gonzobot", "jesi", "shinymetal", "subwatch", "nsa"},
    "supernets": {"scroll", "cancer", "faggotxxx", "fuckyou"},
}


class DateRange(NamedTuple):
    """A time range used to select the part of a log file we want to analyze."""

    start_time: datetime = datetime.min  # IRC didn't exist on 0001-01-01 CE [citation needed]
    end_time: datetime = datetime.max  # if civilization is a thing at that time, I hope nobody runs this.


CHANNEL_REGEX = re.compile(r"(?:^irc\.)(?P<network>.*)(?:\.#.*\.weechatlog$)")


def log_paths(
    exclude_channels: Collection[str] = None, include_channels: Collection[str] = None
) -> Iterator[Path]:
    """Get all the .weechatlog paths to analyze for the current user."""
    try:
        weechat_home = Path(environ["WEECHAT_HOME"])
    except KeyError:
        weechat_home = Path.home() / ".weechat"
    log_dir = weechat_home / "logs"
    for path in log_dir.glob("irc.*.[#]*.weechatlog"):
        if (exclude_channels is None or path.name[4:-11] not in exclude_channels) and (
            include_channels is None
            or len(include_channels) == 0
            or path.name[4:-11]  # strip out leading "irc.", trailing ".weechatlog"
            in include_channels
        ):
            yield path


def read_all_lines(path: Path) -> pd.DataFrame:
    """Convert a WeeChat log file to a DataFrame with the relevant information."""
    logfile_df = pd.read_csv(
        path,
        sep="\t",
        error_bad_lines=False,
        names=("timestamps", "prefixes", "bodies"),
        dtype={"prefixes": str},
    )
    # convert timestamp column to pandas datetime
    logfile_df["timestamps"] = pd.to_datetime(
        logfile_df["timestamps"], format="%Y-%m-%d %H:%M:%S"
    )
    # remove ANSI color escape codes from prefix column
    # logfile_df["prefixes"] = logfile_df["prefixes"].str.replace(ANSI_ESCAPE, "")
    logfile_df["prefixes"] = logfile_df["prefixes"].str.replace(ANSI_ESCAPE, "")
    # this is time-series data. set timestamp column to index
    logfile_df.set_index("timestamps")
    # save message type of each line
    logfile_df["msg_types"] = logfile_df["prefixes"].apply(msg_type)
    # nick column
    # rows with msgtype "message" have the nick in the "prefix" column.
    # Rows with msgtype join/leave/action have nick as the first word of the msg body.
    logfile_df["nicks"] = logfile_df["prefixes"]
    logfile_df.loc[logfile_df["msg_types"] != "message", "nicks"] = None
    logfile_df["nicks"] = logfile_df["nicks"].apply(
        strip_nick_prefix
    )  # strip nick prefixes like "+", "@"
    # add nicks to msgtypes join, leave, and action
    is_join_leave_action: pd.Series = logfile_df["msg_types"].isin(
        {"join", "leave", "action"}
    )
    # join_leave_action_nicks: pd.DataFrame = logfile_df.loc[is_join_leave_action, "nicks"]
    # join_leave_action_bodies: pd.DataFrame = logfile_df.loc[is_join_leave_action, "bodies"]
    logfile_df.loc[is_join_leave_action, "nicks"] = (
        logfile_df.loc[is_join_leave_action, "bodies"]
        .apply(lambda body: body.split()[0])
        .str.replace(ANSI_ESCAPE, "")
    )
    return logfile_df


def log_reader(path: Path, date_range: DateRange) -> pd.DataFrame:
    """Find all IRC messages within date_range for path."""
    logfile_df: pd.DataFrame = read_all_lines(path)
    logfile_df = logfile_df[
        (logfile_df["timestamps"] > date_range.start_time)
        & (logfile_df["timestamps"] < date_range.end_time)
    ]
    # logfile_df = logfile_df.loc[pd.Timestamp(date_range.start_time):pd.Timestamp(date_range.end_time)]
    return logfile_df


@dataclass
class IRCChannel:
    """IRCChannel holds the data extracted from a bunch of IRCMessages.

    It does not hold the entire log; it only holds extracted statistics.
    """

    name: str
    topwords: Counter[str]
    nicks: int
    msgs: int


def analyze_log(
    path: Path, date_range: DateRange, nick_blacklist: Optional[Set[str]] = None
) -> IRCChannel:
    """Turn a path to a log file into an IRCChannel holding its stats.

    This function takes multiple arguments, which makes calling it in a
    single-variable multithreaded map() function tricky. It gets wrapped
    by analyze_log_wrapper which unpacks a single arument into this
    function.
    """
    if nick_blacklist is None:
        nick_blacklist = set()
    # the values we'll extract to build the IRCChannel
    name = path.name[4:-11]  # strip off the "irc." prefix and ".weechatlog" suffix
    logfile_df = log_reader(path, date_range)

    # topwords
    # we want nicks for messages and actions.
    nicks: pd.DataFrame = logfile_df.loc[
        logfile_df["msg_types"].isin({"message", "action"}), "nicks"
    ]
    # multiple consecutive messages from one nick should be grouped together
    nicks = nicks.loc[nicks.shift(1) != nicks]
    # remove blacklisted nicks. Nicks are case-insensitive
    nicks = nicks[~nicks.str.lower().isin(nick_blacklist)]
    nick_counts: pd.Series = nicks.value_counts()
    topwords: Counter[str] = Counter(nick_counts.to_dict())

    # total messages
    msgs = nick_counts.sum()
    return IRCChannel(name=name, topwords=topwords, nicks=len(topwords), msgs=msgs,)


class AnalyzeLogArgs(NamedTuple):
    """Container for the args to unpack and pass to analyze_log."""

    path: Path
    date_range: DateRange
    nick_blacklist: Set[str] = set()


def analyze_log_wrapper(args: AnalyzeLogArgs) -> IRCChannel:
    """Run analyze_log on unpacked arguments.

    This is a global function to make it easier to parallelize.
    """
    return analyze_log(
        path=args.path, date_range=args.date_range, nick_blacklist=args.nick_blacklist
    )


def analyze_all_logs(
    date_range: DateRange,
    include_channels: Collection[str] = None,
    exclude_channels: Collection[str] = None,
    nick_blacklists: Mapping[str, Set[str]] = None,
    sortkey: str = "msgs",
) -> List[IRCChannel]:
    """Gather stats on all logs in parallel."""
    # set default values for optional arguments
    if nick_blacklists is None:
        nick_blacklists = BOT_BLACKLISTS

    # set the arguments for each run of analyze_log_wrapper
    # for all the channels we want to analyze
    analyze_log_args: Iterator[AnalyzeLogArgs] = (
        AnalyzeLogArgs(
            path=path,
            date_range=date_range,
            nick_blacklist=nick_blacklists.get(
                # mypy false positive: log_paths() filters paths against
                # a glob equivalent to our regex; we are guaranteed a match.
                CHANNEL_REGEX.search(path.name).group(1),  # type: ignore[union-attr]
                set(),
            ),
        )
        for path in log_paths(
            exclude_channels=exclude_channels, include_channels=include_channels
        )
    )
    # return [analyze_log_wrapper(args) for args in analyze_log_args]
    with Pool() as pool:
        return sorted(
            pool.imap_unordered(analyze_log_wrapper, analyze_log_args, 4),
            key=lambda channel: channel.__getattribute__(sortkey),
            reverse=True,
        )
