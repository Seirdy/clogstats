"""Gather stats across discrete time intervals.

Collecting stats across discrete many small time intervals allows for
the creation of simple time-series data.

For more advanced time-series manipulation and analysis, see
clogstats.forecasting.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterator, List, Mapping, Optional, Set

import numpy as np
import pandas as pd

from clogstats.stats.gather_stats import (
    ChannelsWanted,
    DateRange,
    IRCChannel,
    NickBlacklist,
    ParsedLogs,
    analyze_multiple_logs,
    parse_all_logs,
)


def ircchannel_to_dict(ircchannel: IRCChannel) -> Dict[str, Any]:
    """Convert an IRCChannel to a dict.

    IRCChannel.topwords is usually a Counter, which gets mangled by
    dataclasses.asdict(). This function prevents that from happening
    """
    ircchannel_dict = asdict(ircchannel)
    ircchannel_dict["topwords"] = ircchannel.topwords
    return ircchannel_dict


def data_to_dataframe(
    gathered_stats: List[IRCChannel], date_range: DateRange,
) -> pd.DataFrame:
    """Convert the list of IRCChannels into a single DataFrame."""
    dataframe_stats: pd.DataFrame = pd.DataFrame(
        [ircchannel_to_dict(channel) for channel in gathered_stats],
    )
    dataframe_stats = dataframe_stats.assign(
        date_start=date_range.start_time, date_end=date_range.end_time,
    )
    return dataframe_stats.set_index("date_start")


@dataclass
class AnalyzeMultipleLogsArgs:
    """Arguments to pass to AnalyzeAllLogs, excluding date_range."""

    parsed_logs: ParsedLogs
    sortkey: str = "msgs"
    nick_blacklists: Optional[NickBlacklist] = None


def divide_date_range(date_range: DateRange, intervals: int) -> List[DateRange]:
    """Divide date_range into a number of equal intervals."""
    delta = (date_range.end_time - date_range.start_time) / intervals
    deltas = np.arange(intervals) * np.array([delta] * intervals)
    dates = date_range.start_time + deltas
    date_pairs = np.column_stack((dates[:-1], dates[1:]))
    return [DateRange(*interval) for interval in date_pairs]


def rerun_analysis_across_intervals(
    analyze_all_logs_args: AnalyzeMultipleLogsArgs,
    date_range: DateRange,
    intervals: int = 0,
) -> Iterator[pd.DataFrame]:
    """Lazily re-run analyze_all_logs across multiple time intervals."""
    date_ranges = divide_date_range(date_range, intervals)
    for small_date_range in date_ranges:
        gathered_stats = analyze_multiple_logs(
            date_range=small_date_range, **asdict(analyze_all_logs_args),
        )
        yield data_to_dataframe(gathered_stats, small_date_range)


def aggregate_timeseries_data(
    analyze_all_logs_args: AnalyzeMultipleLogsArgs,
    date_range: DateRange,
    intervals: int = 0,
) -> pd.DataFrame:
    """Run IRC analyses across time intervals to create a time-series DataFrame.

    Collect the output in a DataFrame with a leading column for the date
    range for each run.
    """
    return pd.concat(
        rerun_analysis_across_intervals(analyze_all_logs_args, date_range, intervals),
    )


def aggregate_all_timeseries_data(  # this is a wrapper function
    date_range: DateRange,
    channels_wanted: ChannelsWanted = None,
    log_dir: str = None,
    nick_blacklists: Mapping[str, Set[str]] = None,
    sortkey: str = "msgs",
    intervals: int = 0,
) -> pd.DataFrame:
    """Wrap functions to parse logfiles and generate timeseries data from them."""
    parsed_logs = parse_all_logs(channels_wanted=channels_wanted, log_dir=log_dir)
    analyze_multiple_logs_args = AnalyzeMultipleLogsArgs(
        parsed_logs=parsed_logs, sortkey=sortkey, nick_blacklists=nick_blacklists,
    )
    return aggregate_timeseries_data(
        date_range=date_range,
        analyze_all_logs_args=analyze_multiple_logs_args,
        intervals=intervals,
    )
