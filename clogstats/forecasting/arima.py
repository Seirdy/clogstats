"""Run ARIMA and ARIMA-related forecasts pre-fitted over activity stats."""

from dataclasses import asdict, dataclass
from typing import Optional

import pandas as pd
from darts import TimeSeries
from darts.models.arima import ARIMA, AutoARIMA

# first determine if the time series is stationary


@dataclass
class ArimaParams:
    """Container for ARIMA parameters."""

    # p, d, q are the standard 1-letter variable names for ARIMA.
    # Disable linting for varnames.
    p: int = 6  # noqa: VNE001,WPS111,C0103
    d: Optional[int] = 0  # noqa: VNE001,WPS111,C0103  # assume data is stationary.
    q: int = 0  # noqa: VNE001,WPS111,C0103


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


_ONE_DAY = pd.Timedelta("1D")


# Disabled linting for argcount because this function needs to pass a
# large number of arguments to auto-ARIMA. I simplified what I could.
def auto_arima_analyzed_log(  # noqa: WPS211  # Found too many arguments
    *autoarima_args,
    gathered_stats: TimeSeries,
    start_arima_params: ArimaParams = None,
    max_arima_params: ArimaParams = None,
    component_index: int = None,
    seasonal: bool = False,
    seasonal_length: pd.Timedelta = _ONE_DAY,
    **autoarima_kwargs,
) -> AutoARIMA:
    """ARIMA forecast with atuo-optimized params.

    Wraps darts.models.arima.AutoARIMA.
    """
    if start_arima_params is None:
        start_arima_params = ArimaParams(d=None)
    if max_arima_params is None:
        max_arima_params = start_arima_params
        for param_name, start_value in asdict(max_arima_params).items():
            try:
                setattr(max_arima_params, param_name, max(start_value * 2, 1))
            except TypeError:
                setattr(max_arima_params, param_name, 1)
    model = AutoARIMA(
        start_p=start_arima_params.p,
        d=start_arima_params.d,
        start_q=start_arima_params.q,
        max_p=max_arima_params.p,
        max_d=max_arima_params.d,
        max_q=max_arima_params.q,
        seasonal=seasonal,
        m=int(seasonal_length / gathered_stats.freq()),
        *autoarima_args,
        **autoarima_kwargs,
    )
    model.fit(gathered_stats, component_index=component_index)
    return model


# get to know ARIMA and auto.arima a bit more, look up AIC, BIC. Switch to stats
# try for different channels
