"""Run ARIMA and ARIMA-related forecasts pre-fitted over activity stats."""

from typing import NamedTuple

from darts import TimeSeries
from darts.models.arima import ARIMA


# first determine if the time series is stationary


class ArimaParams(NamedTuple):
    """Container for ARIMA parameters."""

    p: int = 12  # noqa:VNE001,WPS111
    d: int = 1  # noqa:VNE001,WPS111
    q: int = 0  # noqa:VNE001,WPS111


def arima_analyzed_log(
    gathered_stats: TimeSeries,
    arima_params: ArimaParams = None,
    component_index: int = None,
) -> ARIMA:
    """Create a pre-fitted Arima model from IRC log stats.
    gathered_stats should just hold a single channel's time-series data.
    """
    if arima_params is None:
        arima_params = ArimaParams()
    model = ARIMA(
        arima_params.p, arima_params.d, arima_params.q,
    )  # optimize these values?
    model.fit(gathered_stats, component_index=component_index)
    return model
