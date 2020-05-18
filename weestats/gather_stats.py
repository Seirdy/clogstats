"""Components for reading WeeChat logs and gathering statistics from them."""
from datetime import datetime
from itertools import dropwhile, takewhile
from multiprocessing import Pool
from os import environ
from pathlib import Path
from typing import Container, Counter, Iterator, List, NamedTuple, Optional, Tuple

from weestats.parse import IRCMessage


class DateRange(NamedTuple):
    """A time range used to select the part of a log file we want to analyze."""

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


def log_paths() -> Iterator[Path]:
    """Get all the .weechatlog paths for the current user."""
    try:
        weechat_home = Path(environ["WEECHAT_HOME"])
    except KeyError:
        weechat_home = Path.home() / ".weechat"
    log_dir = weechat_home / "logs"
    for file in log_dir.glob("irc.*.[#]*.weechatlog"):
        yield file


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


class IRCChannel(NamedTuple):
    """IRCChannel holds the data extracted from a bunch of IRCMessages.

    It does not hold the entire log; it only holds extracted statistics.
    """

    name: str
    nick_counts: Counter[str] = Counter()
    total_msgs: int = 0


def analyze_log(path: Path, date_range: DateRange) -> IRCChannel:
    """Turn a path to a log file into an IRCChannel holding its stats."""
    # the values we'll extract to build the IRCChannel
    name = path.name[4:-11]  # strip off the "irc." prefix and ".weechatlog" suffix
    total_msgs = 0
    nick_counts: Counter[str] = Counter()
    # save the previously-extracted nick as well. Use it to merge
    # multiple consecutive messages from the same nick.
    prev_nick: str = ""
    for message in log_reader(path, date_range):
        if message.nick is not None and message.nick != prev_nick:
            prev_nick = message.nick
            nick_counts[message.nick] += 1
            total_msgs += 1
    return IRCChannel(name=name, nick_counts=nick_counts, total_msgs=total_msgs,)


def analyze_log_wrapper(args: Tuple[Path, DateRange]) -> IRCChannel:
    """Run analyze_log on unpacked arguments.

    This is a global function to make it easier to parallelize.
    """
    return analyze_log(*args)


def analyze_all_logs(
    date_range: DateRange, exclude_channels: Container[str] = ()
) -> List[IRCChannel]:
    """Gather stats on all logs in parallel."""
    analyze_log_args = (
        (path, date_range)
        for path in log_paths()
        if path.name[4:-11] not in exclude_channels
    )
    with Pool() as pool:
        return sorted(
            pool.imap_unordered(analyze_log_wrapper, analyze_log_args, 4),
            key=lambda channel: channel.total_msgs,
            reverse=True,
        )
