"""The command-line interface for clogstats_forecasting."""
import argparse

from datetime import datetime, timedelta
from typing import Dict, Iterator, List, Optional, Set, Tuple

from clogstats.gather_stats import DateRange, analyze_all_logs


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(
        description="Gather statistics from WeeChat log files.",
    )
    parser.add_argument(
        "-d",
        "--duration",
        help="start analyzing messages from DURATION hours ago",
        action="store",
        type=float,
        default=24,
        required=False,
    )
    parser.add_argument(
        "-n",
        "--num",
        help="limit output to the top NUM channels",
        action="store",
        type=int,
        default=None,
        required=False,
    )
    parser.add_argument(
        "--min-activity",
        help="limit output to channels with at least MIN_ACTIVITY messages.",
        action="store",
        type=int,
        default=0,
        required=False,
    )
    parser.add_argument(
        "--min-nicks",
        help="limit output to channels with at least MIN_NICKS nicks",
        action="store",
        type=int,
        default=0,
        required=False,
    )
    parser.add_argument(
        "--max-topwords",
        help="show the nicks and message counts for the MAX_TOPWORDS most active nicks",
        action="store",
        type=int,
        default=3,
        required=False,
    )
    parser.add_argument(
        "-s",
        "--sort-by",
        help="key to sort channels by",
        choices=["msgs", "nicks"],
        action="store",
        type=str,
        default="msgs",
        required=False,
    )
    parser.add_argument(
        "--include-channels",
        help='only analyze these channels. format: "network.#channel"',
        action="store",
        type=str,
        nargs="*",
        default=set(),
        required=False,
    )
    parser.add_argument(
        "--exclude-channels",
        help='list of channels to exclude. format: "network.#channel"',
        action="store",
        type=str,
        nargs="*",
        default=set(),
        required=False,
    )
    parser.add_argument(
        "--disable-bot-filters",
        help="disable filtering of some known bots",
        action="store_true",
    )
    parser.add_argument(
        "--log-dir",
        help="directory from which to read logs; defaults to $WEECHAT_HOME",
        action="store",
        type=str,
        default=None,
        required=False,
    )
    return parser.parse_args()


# a row in the output table containing five columns
Row = Tuple[str, str, str, str, str]

PerChannelValues = Dict[str, Set[str]]


def result_table(parsed_args: argparse.Namespace) -> List[Row]:
    """Run clogstats_forecasting from the CLI and dump the results."""
    # get user-supplied parameters
    end_time = datetime.now()
    date_range = DateRange(
        start_time=end_time - timedelta(hours=parsed_args.duration), end_time=end_time,
    )
    print(f"Analyzing logs from {date_range.start_time} till {date_range.end_time}")

    nick_blacklists: Optional[PerChannelValues] = None
    if parsed_args.disable_bot_filters:
        nick_blacklists = {}

    # collect the stats.
    # convert channels to include/exclude to sets for better lookup.
    collected_stats = analyze_all_logs(
        date_range=date_range,
        include_channels=set(parsed_args.include_channels),
        exclude_channels=set(parsed_args.exclude_channels),
        nick_blacklists=nick_blacklists,
        sortkey=parsed_args.sort_by,
        log_dir=parsed_args.log_dir,
    )

    # display total message count
    print(f"total messages: {sum(channel.msgs for channel in collected_stats)}")

    # make a table to display per-channel stats
    # filter channels
    collected_stats = [
        channel
        for channel in collected_stats
        if channel.msgs >= parsed_args.min_activity
        and channel.nicks >= parsed_args.min_nicks
    ]
    return [("RANK", "CHANNEL", "MSGS", "NICKS", "TOPWORDS")] + [
        (
            # channel ranking when sorting channels by # of messages (descending)
            f"{ranking}.",
            channel.name,
            str(channel.msgs),
            str(channel.nicks),
            # TopWords: channel's most active members with msgcount
            ", ".join(
                (
                    f"{nick}: {score}"
                    for nick, score in channel.topwords.most_common(
                        parsed_args.max_topwords,
                    )
                ),
            ),
        )
        for ranking, channel in enumerate(collected_stats, start=1)
        if parsed_args.num is None or ranking <= parsed_args.num
    ]


def padding_sizes(table: List[Row]) -> Iterator[int]:
    """Calculate padding to add to each cell in a table for alignment."""
    for col_number, col in enumerate(zip(*table)):
        if (col_number + 1) % 5:  # don't add padding to last column
            yield max(map(len, col))
        else:
            yield 0


def main():
    """Generate a table of results and print it with aligned columns.

    Alignment mimics the `column` utility from BSD and util-linux.
    """
    full_table: List[Row] = result_table(parse_args())
    for row in full_table:
        row_cells = (
            cell.ljust(width)
            for cell, width in zip(row, list(padding_sizes(full_table)))
        )
        print(" ".join(row_cells))
