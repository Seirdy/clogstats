"""Components for reading WeeChat logs and gathering statistics from them."""

from datetime import datetime
from pathlib import Path
from typing import NamedTuple, Optional

import pandas as pd  # type: ignore  # mypy doesn't have type stubs for pandas yet.


ANSI_ESCAPE = r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]"
NICK_PREFIXES = frozenset(("+", "%", "@", "~", "&"))


def strip_nick_prefix(nick: Optional[str]) -> Optional[str]:
    """Strip out nick prefixes showing enabled modes."""
    if nick is not None:
        nick = str(nick)  # someone on gitter haa the nick "nan". https://xkcd.com/327/
        if nick[0] in NICK_PREFIXES:
            return nick[1:]
    return nick


def msg_type(prefix: str) -> str:
    """Type of IRC message, determined by the message prefix.

    See WeeChat Plugin API docs for prefixes and their meanings.
    """
    # if the prefix string isn't a nick, it's a special kind of message.
    # otherwise, it's a regular message
    try:
        return {
            "=!=": "error",
            "--": "network",
            " *": "action",
            "-->": "join",
            "<--": "quit",
            "": "other",  # empty string = no prefix: other. rarely occurs in the wild.
        }[prefix]
    except KeyError:
        # the prefix is a nick
        return "message"


class DateRange(NamedTuple):
    """A time range used to select the part of a log file we want to analyze."""

    # IRC didn't exist on 0001-01-01 CE [citation needed]
    start_time: datetime = datetime.min
    # if civilization is a thing at datetime.max, I hope nobody runs this.
    end_time: datetime = datetime.max


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
        logfile_df["timestamps"], format="%Y-%m-%d %H:%M:%S",
    )
    # remove ANSI color escape codes from prefix column
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
        strip_nick_prefix,
    )  # strip nick prefixes like "+", "@"
    # add nicks to msgtypes join, leave, and action
    is_join_leave_action: pd.Series = logfile_df["msg_types"].isin(
        {"join", "leave", "action"},
    )
    logfile_df.loc[is_join_leave_action, "nicks"] = (
        logfile_df.loc[is_join_leave_action, "bodies"]
        .apply(lambda body: body.split()[0])
        .str.replace(ANSI_ESCAPE, "")
    )
    return logfile_df


def read_in_range(path: Path, date_range: DateRange) -> pd.DataFrame:
    """Find all IRC messages within date_range for path."""
    logfile_df: pd.DataFrame = read_all_lines(path)
    return logfile_df[
        (logfile_df["timestamps"] > date_range.start_time)
        & (logfile_df["timestamps"] < date_range.end_time)
    ]
