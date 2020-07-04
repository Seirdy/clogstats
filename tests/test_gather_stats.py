"""Tests for the accuracy of the stats read from IRC logs."""
from collections import Counter

from clogstats.stats.gather_stats import IRCChannel, analyze_all_logs


def test_analyze_all_logs(date_range, log_path):
    log_dir = str(log_path)
    actual = analyze_all_logs(date_range=date_range, log_dir=log_dir)
    expected = [
        IRCChannel(
            name="freenode.#firefox",
            topwords=Counter(
                {
                    "EdePopede": 6,
                    "guestkato": 5,
                    "nemo": 4,
                    "Seirdy": 4,
                    "Caspy7": 2,
                    "micr0": 1,
                },
            ),
            nicks=6,
            msgs=22,
        ),
        IRCChannel(
            name="freenode.#node.js",
            topwords=Counter({"ThePendulum": 7, "mikey3": 6}),
            nicks=2,
            msgs=13,
        ),
        IRCChannel(
            name="freenode.#gitlab",
            topwords=Counter({"dtrainor": 1, "superteece": 1}),
            nicks=2,
            msgs=2,
        ),
        IRCChannel(
            name="freenode.#minetest", topwords=Counter({"Seirdy": 1}), nicks=1, msgs=1,
        ),
        IRCChannel(name="freenode.#go-nuts", topwords=Counter(), nicks=0, msgs=0),
    ]
    assert expected == actual
