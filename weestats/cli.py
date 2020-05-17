"""The command-line interface for weestats."""
import argparse
from datetime import datetime, timedelta

from weestats.gather_stats import DateRange, analyze_all_logs


def parse_args() -> argparse.Namespace:
    """Parse CLI options."""
    parser = argparse.ArgumentParser(description="Gather statistics from WeeChat log files.")
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
        "-m",
        "--min-activity",
        help="limit output to channels with at least this many messages.",
        action="store",
        type=int,
        default=0,
        required=False,
    )
    return parser.parse_args()


def main():
    """Run weestats from the CLI and dump the results."""
    # get user-supplied parameters
    args = parse_args()
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=args.duration)
    date_range = DateRange(start_time=start_time, end_time=end_time)
    print(f"Analyzing logs from {date_range.start_time} till {date_range.end_time}")

    # collect the stats
    collected_stats = analyze_all_logs(date_range)

    # display total message count
    total_msgs_allchans = sum(channel.total_msgs for channel in collected_stats)
    print(f"total messages: {total_msgs_allchans}")

    # make a table to display per-channel stats
    COLUMN_HEADINGS = ("RANK", "CHANNEL", "MSGS", "TOPWORDS")
    table_rows = [
        (
            # channel ranking when sorting channels by # of messages (descending)
            f"{ranking}.",
            channel.name,
            str(channel.total_msgs),
            # TopWords: the top 3 most active members of a channel with their # of messages
            ", ".join(
                (
                    f"{nick}: {score}"
                    for nick, score in channel.nick_counts.most_common(3)
                )
            ),
        )
        for ranking, channel in enumerate(collected_stats, start=1)
        if channel.total_msgs >= args.min_activity and (args.num is None or ranking <= args.num)
    ]
    full_table = [COLUMN_HEADINGS] + table_rows
    # pretty-print that table with aligned columns; like `column -t` from BSD and util-linux
    column_widths = [max(map(len, col)) for col in zip(*full_table)]
    for line in full_table:
        print(" ".join((val.ljust(width) for val, width in zip(line, column_widths))))
