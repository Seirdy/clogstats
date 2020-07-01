"""Gather and plot stats across discrete time intervals."""

from dataclasses import asdict, dataclass
from typing import Collection, Iterator, List, Mapping, Optional, Set

import numpy as np  # type: ignore
import pandas as pd  # type: ignore

from clogstats.gather_stats import (
    IRCChannel,
    ParsedLogs,
    analyze_multiple_logs,
    parse_all_logs,
)
from clogstats.parse import DateRange


def data_to_dataframe(
    gathered_stats: List[IRCChannel], date_range: DateRange,
) -> pd.DataFrame:
    """Convert the list of IRCChannels into a single DataFrame."""
    dataframe_stats: pd.DataFrame = pd.DataFrame(
        [asdict(channel) for channel in gathered_stats],
    )
    dataframe_stats = dataframe_stats.assign(date_start=date_range.start_time)
    dataframe_stats = dataframe_stats.assign(date_end=date_range.end_time)
    dataframe_stats.set_index("date_start")
    return dataframe_stats


@dataclass
class AnalyzeAllLogsArgs:
    """Arguments to pass to AnalyzeAllLogs, excluding date_range."""

    parsed_logs: ParsedLogs
    sortkey: str = "msgs"
    nick_blacklists: Optional[Mapping[str, Set[str]]] = None


def divide_date_range(date_range: DateRange, intervals: int) -> List[DateRange]:
    """Divide date_range into a number of equal intervals."""
    delta = (date_range.end_time - date_range.start_time) / intervals
    dates = date_range.start_time + range(0, intervals) * np.array([delta] * intervals)
    return [
        DateRange(*interval) for interval in np.column_stack((dates[:-1], dates[1:]))
    ]


def rerun_analysis_across_intervals(
    analyze_all_logs_args: AnalyzeAllLogsArgs,
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
    analyze_all_logs_args: AnalyzeAllLogsArgs,
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


def aggregate_all_timeseries_data(
    date_range: DateRange,
    exclude_channels: Collection[str] = None,
    include_channels: Collection[str] = None,
    log_dir: str = None,
    nick_blacklists: Mapping[str, Set[str]] = None,
    sortkey: str = "msgs",
    intervals: int = 0,
) -> pd.DataFrame:
    """Wrap functions to parse logfiles and generate timeseries data from them."""
    parsed_logs = parse_all_logs(
        include_channels=include_channels,
        exclude_channels=exclude_channels,
        log_dir=log_dir,
    )
    analyze_multiple_logs_args = AnalyzeAllLogsArgs(
        parsed_logs=parsed_logs, sortkey=sortkey, nick_blacklists=nick_blacklists,
    )
    return aggregate_timeseries_data(
        date_range=date_range,
        analyze_all_logs_args=analyze_multiple_logs_args,
        intervals=intervals,
    )
