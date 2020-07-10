"""Tests for generating time-series data."""
import pandas as pd

from clogstats.stats.gather_stats import ChannelsWanted
from clogstats.stats.time_series import aggregate_all_timeseries_data


def test_aggregate_all_timeseries_data(large_date_range, log_path):
    channels_wanted = ChannelsWanted(
        include_channels=["freenode.#go-nuts_big", "freenode.#node.js_big"],
    )
    actual = aggregate_all_timeseries_data(
        date_range=large_date_range,
        channels_wanted=channels_wanted,
        log_dir=str(log_path),
        intervals=int(
            (large_date_range.end_time - large_date_range.start_time)
            / pd.Timedelta("1H"),
        ),
    )
    for channel_name in channels_wanted.include_channels:
        timeseries_df = actual[actual["name"] == channel_name]
        assert pd.infer_freq(timeseries_df.index) == "H"
        assert actual.shape == (212, 5)
