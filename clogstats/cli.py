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


def result_table() -> List[Row]:
    """Run clogstats_forecasting from the CLI and dump the results."""
    # get user-supplied parameters
    args = parse_args()
    end_time = datetime.now()
    date_range = DateRange(
        start_time=end_time - timedelta(hours=args.duration), end_time=end_time,
    )
    print(f"Analyzing logs from {date_range.start_time} till {date_range.end_time}")

    nick_blacklists: Optional[Dict[str, Set[str]]] = None
    if args.disable_bot_filters:
        nick_blacklists = {}

    # collect the stats.
    # convert channels to include/exclude to sets for better lookup.
    collected_stats = analyze_all_logs(
        date_range=date_range,
        include_channels=set(args.include_channels),
        exclude_channels=set(args.exclude_channels),
        nick_blacklists=nick_blacklists,
        sortkey=args.sort_by,
        log_dir=args.log_dir,
    )

    # display total message count
    msgs_allchans = sum(channel.msgs for channel in collected_stats)
    print(f"total messages: {msgs_allchans}")

    # make a table to display per-channel stats
    # filter channels
    collected_stats = [
        channel
        for channel in collected_stats
        if channel.msgs >= args.min_activity and channel.nicks >= args.min_nicks
    ]
    column_headings: Row = ("RANK", "CHANNEL", "MSGS", "NICKS", "TOPWORDS")
    table_rows: List[Row] = [
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
                    for nick, score in channel.topwords.most_common(args.max_topwords)
                ),
            ),
        )
        for ranking, channel in enumerate(collected_stats, start=1)
        if args.num is None or ranking <= args.num
    ]
    return [column_headings] + table_rows


def calculate_padding_size(table: List[Row]) -> Iterator[int]:
    """Calculate padding to add to each cell in a table for alignment."""
    for col_number, col in enumerate(zip(*table)):
        if (col_number + 1) % 5 != 0:  # don't add padding to last column
            yield max(map(len, col))
        else:
            yield 0


def main():
    """Generate a table of results and pretty-print them."""
    full_table: List[Row] = result_table()
    # pretty-print that table with aligned columns
    # like `column -t` from BSD and util-linux
    padding_sizes = list(calculate_padding_size(full_table))
    for row in full_table:
        print(" ".join((cell.ljust(width) for cell, width in zip(row, padding_sizes))))
