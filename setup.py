"""Package weestats."""

from pathlib import Path

from setuptools import setup

PROJECT_ROOT = Path(__file__).parent


def get_long_description() -> str:
    """Read README.rst."""
    with PROJECT_ROOT.joinpath("README.rst").open() as file_contents:
        return file_contents.read()


setup(
    name="weestats",
    version="0.0.0",
    author="Rohan Kumar",
    description="Gather statistics from WeeChat log files.",
    long_description=get_long_description(),
    long_description_content_type="text/x-rst",
    url="https://git.sr.ht/~seirdy/weestats",
    packages=["weestats"],
    license="AGPLv3+",
    entry_points={
        "console_scripts": ["weestats=weestats.cli:main"],
    }
)
