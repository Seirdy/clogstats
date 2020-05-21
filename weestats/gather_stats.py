"""Components for reading WeeChat logs and gathering statistics from them."""
import re
from dataclasses import dataclass
from datetime import datetime
from itertools import dropwhile, takewhile
from multiprocessing import Pool
from os import environ
from pathlib import Path
from typing import (Collection, Counter, Dict, Iterator, List, Mapping,
                    NamedTuple, Optional, Set)

from weestats.parse import IRCMessage

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

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


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
            or path.name[4:-11] in include_channels
        ):
            yield path


def log_reader(path: Path, date_range: DateRange) -> Iterator[IRCMessage]:
    """Read an IRCMessage from each line of a log file after start_time."""
    all_messages: Iterator[IRCMessage] = (
        IRCMessage(row) for row in path.open(mode="r", encoding="utf-8")
    )
    if date_range.start_time is not None:
        all_messages = dropwhile(
            lambda message: message.timestamp <= date_range.start_time,  # type: ignore[operator]
            all_messages,
        )
    if date_range.end_time is not None:
        all_messages = takewhile(
            lambda message: message.timestamp <= date_range.end_time,  # type: ignore[operator]
            all_messages,
        )
    return all_messages


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
    msgs = 0
    topwords: Counter[str] = Counter()
    # save the previously-extracted nick as well. Use it to merge
    # multiple consecutive messages from the same nick.
    prev_nick: str = ""
    for message in log_reader(path, date_range):
        # mypy false positives: the if-statement ensures that message.nick isn't None
        if message.nick not in nick_blacklist.union({prev_nick, None}):  # type: ignore[arg-type]
            prev_nick = message.nick  # type: ignore[assignment]
            topwords[message.nick] += 1  # type: ignore[index]
            msgs += 1
    return IRCChannel(name=name, topwords=topwords, nicks=len(topwords), msgs=msgs,)


class AnalyzeLogArgs(NamedTuple):
    """Conatiner for the args to unpack and pass to analyze_log."""

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
        for path in log_paths(exclude_channels=exclude_channels, include_channels=include_channels)
    )
    with Pool() as pool:
        return sorted(
            pool.imap_unordered(analyze_log_wrapper, analyze_log_args, 4),
            key=lambda channel: channel.__getattribute__(sortkey),
            reverse=True,
        )
