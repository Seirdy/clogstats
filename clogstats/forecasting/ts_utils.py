"""Common utilities for time-series manipulation."""

from typing import List

import pandas as pd

from darts import TimeSeries


def create_timeseries(
    ts_data: pd.DataFrame, freq: str = None, value_cols: List[str] = None,
) -> TimeSeries:
    """Create a darts TimeSeries from a dataframe.

    The resulting TimeSeries has two columns. Column 0 is nick counts
    and column 1 is message count.
    """
    if not value_cols:
        value_cols = ["nicks", "msgs"]
    return TimeSeries.from_dataframe(
        ts_data, time_col=None, value_cols=value_cols, freq=freq,
    )
