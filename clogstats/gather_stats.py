"""Parse and aggregate statistics from all desired WeeChat logs."""
import re

from dataclasses import dataclass
from multiprocessing import Pool
from os import environ
from pathlib import Path
from types import MappingProxyType
from typing import Collection, Counter, Iterator, List, Mapping, NamedTuple, Set

import pandas as pd  # type: ignore

from clogstats.parse import DateRange, read_in_range


BOT_BLACKLISTS: Mapping[str, Set[str]] = MappingProxyType(
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
    }
)

# example logfile: "irc.freenode.#python.weechatlog"
LOGFILE_REGEX: re.Pattern = re.compile(
    r"(?:^irc\.)(?P<network>.*)(?:\.#.*\.weechatlog$)"
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
    path: Path, date_range: DateRange, nick_blacklist: Set[str] = None,
) -> IRCChannel:
    """Turn a path to a log file into an IRCChannel holding its stats.

    This function takes multiple arguments, which makes calling it in a
    single-variable multithreaded map() function tricky. It gets wrapped
    by analyze_log_wrapper which unpacks a single arument into this
    function.
    """
    if not nick_blacklist:
        nick_blacklist = set()
    # the values we'll extract to build the IRCChannel
    name = path.name[4:-11]  # strip off the "irc." prefix and ".weechatlog" suffix
    logfile_df = read_in_range(path, date_range)

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
        path=args.path, date_range=args.date_range, nick_blacklist=args.nick_blacklist,
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
                LOGFILE_REGEX.search(path.name).group(1),  # type: ignore[union-attr]
                set(),
            ),
        )
        for path in log_paths(
            exclude_channels=exclude_channels,
            include_channels=include_channels,
            log_dir=log_dir,
        )
    )
    with Pool() as pool:
        return sorted(
            pool.imap_unordered(analyze_log_wrapper, analyze_log_args, 4),
            key=lambda channel: channel.__getattribute__(sortkey),
            reverse=True,
        )
