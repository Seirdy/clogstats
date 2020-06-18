"""Package clogstats."""

from pathlib import Path

from setuptools import setup  # type: ignore[import]

PROJECT_ROOT = Path(__file__).parent


def get_long_description() -> str:
    """Read README.rst."""
    with PROJECT_ROOT.joinpath("README.md").open() as file_contents:
        return file_contents.read()


setup(
    name="clogstats",
    author="Rohan Kumar",
    description="Gather statistics from WeeChat log files.",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://git.sr.ht/~seirdy/clogstats",
    packages=["clogstats"],
    license="AGPLv3+",
    python_requires=">=3.6",
    # backport py3's dataclasses
    install_requires=["dataclasses>=0.6; python_version < '3.7'", "pandas>=0.25.3"],
    entry_points={"console_scripts": ["clogstats=clogstats.cli:main"]},
)
