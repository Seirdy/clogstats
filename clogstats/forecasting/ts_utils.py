"""Common utilities for time-series manipulation."""

from typing import Any, Callable, Dict, List, Mapping, NamedTuple

import numpy as np
import pandas as pd
from darts.metrics import metrics
from darts.models.forecasting_model import UnivariateForecastingModel  # for typing
from darts.preprocessing.scaler_wrapper import ScalerWrapper
from darts.timeseries import TimeSeries
from sklearn.preprocessing import PowerTransformer
from typing_extensions import Protocol


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


class ModelParams(NamedTuple):
    """Contains a function to create a model and its arguments."""

    prediction_function: Callable[..., UnivariateForecastingModel]
    prediction_kwargs: Mapping[str, Any]


ModelsToMake = Mapping[str, ModelParams]


def make_forecasts(
    train: TimeSeries, n_pred: int, predictions_to_make: ModelsToMake,
) -> Dict[str, TimeSeries]:
    """Run all the implemented predictions on a time series."""
    models: Dict[str, UnivariateForecastingModel] = {
        name: model.prediction_function(gathered_stats=train, **model.prediction_kwargs)
        for (name, model) in predictions_to_make.items()
    }
    return {name: model.predict(n_pred) for name, model in models.items()}


def make_forecasts_ensure_positive(
    train: TimeSeries, n_pred: int, predictions_to_make: ModelsToMake,
) -> Dict[str, TimeSeries]:
    """Wrap transfomations around make_transform() to ensure positive forecasts.

    Avoids negative values in forecasts by adding 1 to all values
    (ensuring no zeros) and applying a Box-Cox transformation/inversion
    before/after forecasting.
    """
    scaler_wrapper = ScalerWrapper(  # type: ignore
        scaler=PowerTransformer(method="box-cox"),
    )
    # box-cox doesn't like the number "0", so add one to everything
    scaled_train = scaler_wrapper.fit_transform(train + 1)
    forecasts = make_forecasts(scaled_train, n_pred, predictions_to_make)
    # invert the transformation
    return {
        name: scaler_wrapper.inverse_transform(forecast) - 1
        for (name, forecast) in forecasts.items()
    }


Reduction = Callable[[np.ndarray], float]


class Metric(Protocol):  # noqa: R0903  # this is just a Callable with an optional type
    """Protocol for type-checking functions serving as error metrics.

    Error metrics are typically provided by darts.metrics; see
    its documentation for more information.
    """

    def __call__(
        self,
        series1: TimeSeries,
        series2: TimeSeries,
        intersect: bool = True,
        reduction: Reduction = np.mean,
    ) -> float:
        ...  # noqa: WPS428


def compare_predictions(
    actual: TimeSeries, predictions: Dict[str, TimeSeries], metric: Metric,
) -> Dict[str, float]:
    """Compare multiple predictions and sort them by the given error metric."""
    prediction_metrics = {
        name: metric(actual, prediction) for (name, prediction) in predictions.items()
    }
    return dict(sorted(prediction_metrics.items(), key=lambda pair: pair[1]))


class PredictionEvaluations(NamedTuple):
    """Container for predictions and their accuracies."""

    predictions: Mapping[str, TimeSeries]
    evaluations: Mapping[str, float]


_ONE_DAY: pd.Timedelta = pd.Timedelta("1D")


def make_and_compare_predictions(
    gathered_stats: TimeSeries,
    predictions_to_make: ModelsToMake,
    prediction_duration_past: pd.Timedelta = _ONE_DAY,
    prediction_duration_future: pd.Timedelta = None,
    metric: Metric = metrics.coefficient_of_variation,
    transform: bool = False,
) -> PredictionEvaluations:
    """Run multiple forecasts and compare their accuracy."""
    train, actual = gathered_stats.split_after(
        gathered_stats.end_time() - prediction_duration_past,
    )
    n_pred: int = len(actual)
    if prediction_duration_future:
        n_pred += int(prediction_duration_future / gathered_stats.freq())
    if transform:
        forecasts = make_forecasts_ensure_positive(
            train=train, n_pred=n_pred, predictions_to_make=predictions_to_make,
        )
    else:
        forecasts = make_forecasts(
            train=train, n_pred=n_pred, predictions_to_make=predictions_to_make,
        )
    return PredictionEvaluations(
        predictions=forecasts,
        evaluations=compare_predictions(actual, forecasts, metric),
    )
