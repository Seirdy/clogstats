"""Parse and aggregate statistics from all desired WeeChat logs."""
import re

from dataclasses import dataclass
from multiprocessing import Pool
from os import environ
from pathlib import Path
from types import MappingProxyType
from typing import (
    Collection,
    Counter,
    Iterable,
    Iterator,
    List,
    Mapping,
    NamedTuple,
    Set,
)

import pandas as pd  # type: ignore

from clogstats.stats.parse import DateRange, read_all_lines


NickBlacklist = Mapping[str, Set[str]]
BOT_BLACKLISTS: NickBlacklist = MappingProxyType(
    {
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
    },
)

# example logfile: "irc.freenode.#python.weechatlog"
LOGFILE_REGEX: re.Pattern = re.compile(
    r"(?:^irc\.)(?P<network>.*)(?:\.#.*\.weechatlog$)",
)


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
    logfile_df: pd.DataFrame,
    date_range: DateRange,
    name: str,
    nick_blacklist: Set[str] = None,
) -> IRCChannel:
    """Turn a parsed log file into an IRCChannel holding its stats.

    This function takes multiple arguments, which makes calling it in a
    single-variable multithreaded map() function tricky. It gets wrapped
    by analyze_log_wrapper which unpacks a single arument into this
    function.
    """
    # filter date range
    logfile_df = logfile_df[
        (logfile_df["timestamps"] > date_range.start_time)
        & (logfile_df["timestamps"] < date_range.end_time)
    ]
    if not nick_blacklist:
        nick_blacklist = set()
    # the values we'll extract to build the IRCChannel

    # topwords
    # we want nicks for messages and actions.
    nicks: pd.DataFrame = logfile_df.loc[
        logfile_df["msg_types"].isin({"message", "action"}), "nicks",
    ]
    # multiple consecutive messages from one nick should be grouped together
    nicks = nicks.loc[nicks.shift(1) != nicks]
    # remove blacklisted nicks. Nicks are case-insensitive
    nicks = nicks[~nicks.str.lower().isin(nick_blacklist)]
    nick_counts: pd.Series = nicks.value_counts()
    topwords: Counter[str] = Counter(nick_counts.to_dict())

    # total messages
    msgs = nick_counts.sum()
    return IRCChannel(name=name, topwords=topwords, nicks=len(topwords), msgs=msgs)


class AnalyzeLogArgs(NamedTuple):
    """Container for the args to unpack and pass to analyze_log."""

    logfile_df: pd.DataFrame
    date_range: DateRange
    name: str
    nick_blacklist: Set[str] = set()


def analyze_log_wrapper(args: AnalyzeLogArgs) -> IRCChannel:
    """Run analyze_log on unpacked arguments.

    This is a global function to make it easier to parallelize.
    """
    return analyze_log(
        logfile_df=args.logfile_df,
        date_range=args.date_range,
        name=args.name,
        nick_blacklist=args.nick_blacklist,
    )


# ParsedLogs is a mapping of a channel name to its parsed DataFrame
ParsedLogs = Mapping[str, pd.DataFrame]


def analyze_multiple_logs(  # noqa: R0913
    date_range: DateRange,
    parsed_logs: ParsedLogs,
    nick_blacklists: Mapping[str, Set[str]] = None,
    sortkey: str = "msgs",
) -> List[IRCChannel]:
    """Gather stats on multiple parsed logs in parallel."""
    # set default values for optional arguments
    if nick_blacklists is None:
        nick_blacklists = BOT_BLACKLISTS

    # set the arguments for each run of analyze_log_wrapper
    # for all the channels we want to analyze
    analyze_log_args: Iterator[AnalyzeLogArgs] = (
        AnalyzeLogArgs(
            logfile_df=parsed_logs[channel_name],
            date_range=date_range,
            name=channel_name,
            nick_blacklist=nick_blacklists.get(channel_name.split(".#", 1)[0], set()),
        )
        for channel_name in parsed_logs
    )
    with Pool() as pool:
        output_data = sorted(
            pool.imap_unordered(analyze_log_wrapper, analyze_log_args, 4),
            key=lambda channel: channel.__getattribute__(sortkey),
            reverse=True,
        )
        # explicitly call close() and join() for coverage.py to work
        # otherwise redundant due to `with` statement
        pool.close()
        pool.join()
        return output_data


def log_paths(
    exclude_channels: Collection[str] = None,
    include_channels: Collection[str] = None,
    log_dir: str = None,
) -> Iterator[Path]:
    """Get all the .weechatlog paths to analyze for the current user."""
    if log_dir:
        log_path = Path(log_dir)
    else:
        try:
            weechat_home = Path(environ["WEECHAT_HOME"])
        except KeyError:
            weechat_home = Path.home() / ".weechat"
        log_path = weechat_home / "logs"
    for path in log_path.glob("irc.*.[#]*.weechatlog"):
        if (exclude_channels is None or path.name[4:-11] not in exclude_channels) and (
            not include_channels or path.name[4:-11] in include_channels
        ):
            yield path


def parse_multiple_logs(paths: Iterable[Path]) -> ParsedLogs:
    """Return a dict mapping each channel name to its parsed DataFrame."""
    return {path.name[4:-11]: read_all_lines(path) for path in paths}


def parse_all_logs(
    include_channels: Collection[str] = None,
    exclude_channels: Collection[str] = None,
    log_dir: str = None,
) -> ParsedLogs:
    """Parse every log on the system."""
    # maybe parallelize this in the future.
    return parse_multiple_logs(
        log_paths(
            exclude_channels=exclude_channels,
            include_channels=include_channels,
            log_dir=log_dir,
        ),
    )


def analyze_all_logs(  # noqa: R0913
    date_range: DateRange,
    include_channels: Collection[str] = None,
    exclude_channels: Collection[str] = None,
    nick_blacklists: Mapping[str, Set[str]] = None,
    sortkey: str = "msgs",
    log_dir: str = None,
) -> List[IRCChannel]:
    """Gather stats on all logs in parallel."""
    # set default values for optional arguments
    parsed_logs = parse_multiple_logs(
        log_paths(
            exclude_channels=exclude_channels,
            include_channels=include_channels,
            log_dir=log_dir,
        ),
    )
    # set the arguments for each run of analyze_log_wrapper
    # for all the channels we want to analyze
    return analyze_multiple_logs(
        date_range=date_range,
        parsed_logs=parsed_logs,
        nick_blacklists=nick_blacklists,
        sortkey=sortkey,
    )
