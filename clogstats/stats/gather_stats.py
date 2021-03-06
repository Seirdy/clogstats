"""Parse and aggregate statistics from all desired WeeChat logs."""
from dataclasses import dataclass
from datetime import datetime
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
    Optional,
    Set,
)

import numpy as np
import pandas as pd

from clogstats.stats.parse import read_all_lines

NickBlacklist = Mapping[str, Set[str]]
BOT_BLACKLISTS: NickBlacklist = MappingProxyType(
    {
        "2600net": {"jarvis", "gbot", "bitbot"},
        "darkscience": {"djbot", "zeta"},
        "efnet": {"pelosi"},
        "installgentoo": {"gtrackerbot5"},
        "freenode": {
            "buttsbot",
            "fedbot",
            "imoutobot",
            "jellobot",
            "machabot",
            "minetestbot",
            "mockturtle",
            "reddit-bot",
            "weebot",
            "wlb1",
            "zero1",
        },
        "gitter": {"gitter"},
        "gotham": {"mafalda", "southbay", "damon"},
        "rizon": {"internets", "chanstat", "yt-info"},
        "tilde_chat": {"bitbot", "tildebot"},
        "snoonet": {"gonzobot", "jesi", "shinymetal", "subwatch", "nsa"},
        "supernets": {"scroll", "cancer", "faggotxxx", "fuckyou"},
    },
)


class DateRange(NamedTuple):
    """A time range used to select the part of a log file we want to analyze."""

    # IRC didn't exist on 0001-01-01 CE [citation needed]
    start_time: np.datetime64 = np.datetime64(datetime.min)
    # if civilization is a thing at datetime.max, I hope nobody runs this.
    end_time: np.datetime64 = np.datetime64(datetime.max)


class ChannelsWanted(NamedTuple):
    """Contains lists of channels to include/exclude.

    These are always passed to functions together, so it makes sense to group them.
    """

    include_channels: Optional[Collection[str]] = None
    exclude_channels: Optional[Collection[str]] = None


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
        & (logfile_df["timestamps"] < date_range.end_time)  # noqa: S101 # no comma here
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
    return IRCChannel(
        name=name, topwords=topwords, nicks=len(topwords), msgs=nick_counts.sum(),
    )


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


def analyze_multiple_logs(
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
    return sorted(
        map(analyze_log_wrapper, analyze_log_args),
        key=lambda channel: getattr(channel, sortkey),
        reverse=True,
    )


def channel_name(path: Path) -> str:
    """Extract the channel name from its logfile's path."""
    # strip the "irc." prefix and ".weechatlog" suffix
    # in py39 strings will get the removeprefix() and removesuffix() methods.
    # will probably make clogstats py39+ in like 2022 or something lol
    return path.name[len("irc.") : -len(".weechatlog")]


def path_is_wanted(path: Path, channels_wanted: ChannelsWanted = None) -> bool:
    """Determine if the given path is to be analyzed or ignored."""
    # Analyze all paths if no channels to include/exclude are specified
    if channels_wanted is None:
        return True
    path_not_excluded = (
        channels_wanted.exclude_channels is None
        or channel_name(path) not in channels_wanted.exclude_channels
    )
    path_included = (
        not channels_wanted.include_channels
        or channel_name(path) in channels_wanted.include_channels
    )
    return path_not_excluded and path_included


def log_paths(
    channels_wanted: ChannelsWanted = None, log_dir: str = None,
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
        if path_is_wanted(path, channels_wanted):
            yield path


def parse_multiple_logs(paths: Iterable[Path]) -> ParsedLogs:
    """Return a dict mapping each channel name to its parsed DataFrame."""
    paths = list(paths)  # collect paths into a list so we can iterate multiple times
    with Pool() as pool:
        log_contents: Iterable[pd.DataFrame] = pool.imap(read_all_lines, paths, 4)
        # explicitly call close() and join() for coverage.py to work
        # otherwise redundant due to `with` statement
        pool.close()
        pool.join()
    log_names = (channel_name(path) for path in paths)
    return dict(zip(log_names, log_contents))


def parse_all_logs(
    channels_wanted: ChannelsWanted = None, log_dir: str = None,
) -> ParsedLogs:
    """Parse every log on the system."""
    # maybe parallelize this in the future.
    return parse_multiple_logs(
        log_paths(channels_wanted=channels_wanted, log_dir=log_dir),
    )


def analyze_all_logs(
    date_range: DateRange,
    channels_wanted: ChannelsWanted = None,
    nick_blacklists: NickBlacklist = None,
    sortkey: str = "msgs",
    log_dir: str = None,
) -> List[IRCChannel]:
    """Gather stats on all logs in parallel."""
    # set default values for optional arguments
    parsed_logs = parse_all_logs(channels_wanted=channels_wanted, log_dir=log_dir)
    # set the arguments for each run of analyze_log_wrapper
    # for all the channels we want to analyze
    return analyze_multiple_logs(
        date_range=date_range,
        parsed_logs=parsed_logs,
        nick_blacklists=nick_blacklists,
        sortkey=sortkey,
    )
