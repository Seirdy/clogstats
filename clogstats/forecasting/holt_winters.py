"""Run Holt-Winters triple-exponential smoothing over activity stats."""

import pandas as pd  # type: ignore

from statsmodels.tsa.holtwinters import ExponentialSmoothing  # type: ignore


def hw_analyzed_log(gathered_stats: pd.DataFrame) -> ExponentialSmoothing:
    """Create an ExponentialSmoothing object from IRC log stats.

    gathered_stats should just hold a single channel's data.
    """
    gathered_stats.index.freq = 'MS'
    model = ExponentialSmoothing(gathered_stats, seasonal="mul", seasonal_periods=7).fit()
    return model
