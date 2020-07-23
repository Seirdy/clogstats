"""Run triple-exponential smoothing forecasts, pre-fitted over activity stats."""

from typing import Any, Mapping

import pandas as pd
from darts import TimeSeries
from darts.models.exponential_smoothing import ExponentialSmoothing


def hw_analyzed_log(
    gathered_stats: TimeSeries,
    seasonal_periods: int = 0,
    seasonal_length: pd.Timedelta = None,
    component_index: int = 0,
    **exponential_smoothing_kwargs: Mapping[str, Any],
) -> ExponentialSmoothing:
    """Create a pre-fitted ExponentialSmoothing object from IRC log stats.

    gathered_stats should just hold a single channel's time-series data.
    """
    if seasonal_length:
        seasonal_periods = max(
            seasonal_periods, int(gathered_stats.duration() / seasonal_length),
        )
    model = ExponentialSmoothing(
        seasonal_periods=seasonal_periods, **exponential_smoothing_kwargs,
    )
    model.fit(gathered_stats, component_index=component_index)
    return model
