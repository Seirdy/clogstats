"""Plot time-series data with matplotlib."""

import pandas as pd  # type: ignore

from matplotlib import pyplot as plt  # type: ignore


def plot_channel_activity(channel: str, ts_data: pd.DataFrame):
    """Plot a single channel's activity (msgcount) over time."""
    filtered: pd.DataFrame = ts_data.loc[ts_data["name"] == channel]
    plt.figure()
    filtered.plot(x="date_end", y="msgs")
