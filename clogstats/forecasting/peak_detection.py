"""Detect and list peaks in channel activity.

Listing peaks across a forecast can be a useful way to figure out when
the best time to visit a channel will be.
"""

from dataclasses import dataclass
from typing import List, Mapping, NamedTuple, Optional

import numpy as np
import pandas as pd
import scipy as sp
from darts.timeseries import TimeSeries

from clogstats.stats.gather_stats import DateRange

_SIX_HOURS = pd.Timedelta("6H")


@dataclass
class PeakParams:
    """Container for parameters used to determine presence of peaks."""

    interval: pd.Timedelta
    distance: Optional[int]
    wlen: Optional[int]


def calculate_distance_wlen(series: TimeSeries, peak_params: PeakParams) -> PeakParams:
    """Calculate the distance and wlen parameters for peak-finding.

    These parameters are calculated as a multiple of ``interval/series.freq()``
    """
    if not peak_params.distance:
        peak_params.distance = peak_params.interval / series.freq()
    if not peak_params.wlen:
        peak_params.wlen = peak_params.interval * 3
    return peak_params


class Peaks(NamedTuple):
    """Container for peaks and their properties from SciPy's find_peaks()."""

    peak_indices: np.ndarray
    properties: Mapping[str, np.array]


def find_peak_indices(series: TimeSeries, peak_params: PeakParams) -> Peaks:
    """List the timestamps at which channel activity peaks."""
    peak_params = calculate_distance_wlen(series, peak_params)
    # pandas-vet thinks `series` is a pandas data structure with
    # ambiguous behavior for values()
    indices: np.ndarray
    properties: Mapping[str, np.array]
    indices, properties = sp.signal.find_peaks(
        series.values().flatten(),  # noqa: PD011
        distance=peak_params.distance,
        wlen=peak_params.wlen,
        height=series.mean(),
    )
    return Peaks(indices, properties)


def intervals_with_activity(
    time_series: TimeSeries,
    interval: pd.Timedelta = _SIX_HOURS,
    distance: int = None,
    wlen: int = None,
) -> List[DateRange]:
    """Specify the intervals across which a channel will be most active."""
    timestamps = time_series.pd_series().index.to_numpy()
    pairs: np.ndarray = np.array((timestamps[:-1], timestamps[1:])).T
    indices, _ = find_peak_indices(time_series, PeakParams(interval, distance, wlen))
    # create DateRange objects from time intervals corresponding to peaks
    # pylint false positive: pylint claims pairs is unsubscriptable
    return [DateRange(*pair) for pair in pairs[indices]]  # noqa: E1136
