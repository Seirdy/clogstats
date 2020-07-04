"""Set up common values for reading/working with the repo's sample logs."""
from datetime import datetime
from pathlib import Path

import pytest  # type: ignore

from clogstats.stats.parse import DateRange


@pytest.fixture()
def date_range() -> DateRange:
    """Date range for sample logs."""
    start_time = datetime.strptime(
        "2020-06-19 12:46:00", "%Y-%m-%d %H:%M:%S",  # noqa: WPS323
    )
    end_time = datetime.strptime(
        "2020-06-19 13:43:00", "%Y-%m-%d %H:%M:%S",  # noqa: WPS323
    )
    return DateRange(start_time=start_time, end_time=end_time)


@pytest.fixture()
def log_path() -> Path:
    """Path to sample logs in repo."""
    return Path(__file__).parent.joinpath("sample_logs")
