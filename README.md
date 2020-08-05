clogstats
=========

[![sourcehut](https://img.shields.io/badge/repository-sourcehut-lightgrey.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZlcnNpb249IjEuMSINCiAgICB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCI+DQogIDxkZWZzPg0KICAgIDxmaWx0ZXIgaWQ9InNoYWRvdyIgeD0iLTEwJSIgeT0iLTEwJSIgd2lkdGg9IjEyNSUiIGhlaWdodD0iMTI1JSI+DQogICAgICA8ZmVEcm9wU2hhZG93IGR4PSIwIiBkeT0iMCIgc3RkRGV2aWF0aW9uPSIxLjUiDQogICAgICAgIGZsb29kLWNvbG9yPSJibGFjayIgLz4NCiAgICA8L2ZpbHRlcj4NCiAgICA8ZmlsdGVyIGlkPSJ0ZXh0LXNoYWRvdyIgeD0iLTEwJSIgeT0iLTEwJSIgd2lkdGg9IjEyNSUiIGhlaWdodD0iMTI1JSI+DQogICAgICA8ZmVEcm9wU2hhZG93IGR4PSIwIiBkeT0iMCIgc3RkRGV2aWF0aW9uPSIxLjUiDQogICAgICAgIGZsb29kLWNvbG9yPSIjQUFBIiAvPg0KICAgIDwvZmlsdGVyPg0KICA8L2RlZnM+DQogIDxjaXJjbGUgY3g9IjUwJSIgY3k9IjUwJSIgcj0iMzglIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQlIg0KICAgIGZpbGw9Im5vbmUiIGZpbHRlcj0idXJsKCNzaGFkb3cpIiAvPg0KICA8Y2lyY2xlIGN4PSI1MCUiIGN5PSI1MCUiIHI9IjM4JSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0JSINCiAgICBmaWxsPSJub25lIiBmaWx0ZXI9InVybCgjc2hhZG93KSIgLz4NCjwvc3ZnPg0KCg==)](https://git.sr.ht/~seirdy/clogstats)
[![GitLab
mirror](https://img.shields.io/badge/mirror-GitLab-orange.svg?logo=gitlab)](https://gitlab.com/Seirdy/clogstats)
[![GitHub
mirror](https://img.shields.io/badge/mirror-GitHub-black.svg?logo=github)](https://github.com/Seirdy/clogstats)

Clogstats tells you statistics about your WeeChat channels by reading your chat logs.
It can currently tell you the most active IRC channels and nicks across a given
duration (the last 24 hours by default).

The motivation for writing clogstats was to overcome the limitations of its
predecessor, [chattiest-channels](https://git.sr.ht/~seirdy/chattiest-channels);
chattiest-channels served mostly as a proof-of-concept and had *very* messy date/time
handling.

Dependencies
------------

Clogstats requires at least Python 3.6.1.

Without any extras, it supports both CPython and PyPy 7.3.1+.

On Python 3.7+, the only 3rd-party dependency is Pandas.

Python 3.6 users also need [a backport](https://pypi.org/project/dataclasses/) of
Python 3.7's `dataclasses` library.

For advanced time-series manipulation and forecasting, clogstats can optionally use
[darts](https://pypi.org/project/u8darts/). darts has [many large 3rd-party
dependencies](https://github.com/unit8co/darts/blob/0.2.0/requirements/main.txt) of
its own, most of which do not support PyPy.

Installation
------------

Install with `pip`:

``` sh
python3 -m pip install --user git+https://git.sr.ht/~seirdy/clogstats
```

Install clogstats with support for advanced time-series forecasting (no PyPy
support):

``` sh
python3 -m pip install --user git+https://git.sr.ht/~seirdy/clogstats#egg=clogstats[forecasting]
```

I recommend trying out [pipx](https://pipxproject.github.io/pipx/) to auto-create
virtual environments for Python executables and add them to your `$PATH`:

``` sh
python3 -m pip install --user pipx
# use --system-site-packages if your distro offers packages for pandas/numpy so you don't have to build them yourself
pipx install --system-site-packages git+https://git.sr.ht/~seirdy/clogstats
```

Flood mitigation
----------------

Mitigating the effects of spam and flooding continues to be an ongoing challenge.
Flood mitigation measures include:

- Merging consecutive messages from the same nick.
- Filtering out a small list of known bot nicks. This filtering happens on a
  per-network basis and matches blacklisted nicks against a server name. This only
  works if the server names in your WeeChat configs match the server names specified
  by `BOT_BLACKLISTS` in `clogstats/gather_stats.py`

Planned areas of improvement for flood mitigation primarily involve filtering out
messages by user-configurable per-network regular expressions and nick blacklists. I
might automate generating nick blacklists with a WeeChat script that runs
`/msg botserv botlist` on a list of IRC server buffers and saves the output to a
file.

Features and Usage
------------------

Clogstats can sort channels by their number of messages or number of non-lurkers
(i.e., the number of nicks that actually sent a message). It can also display the top
most active nicks for each channel.

### Time-series analysis and forecasting

Time-series modelling and forecasting requires installation with the "forecasting"
dependency. Forecasts are a work in progress; as of right now, they require a lot of
tuning to be accurate.

Charting channel activity in Matplotlib, comparing two different forecasts with the
actual output:

![Channel activity for quakenet.\#anime](https://u.teknik.io/JJbjl.png)

### Command-line stats aggregation

``` text
usage: clogstats [-h] [-d DURATION] [-n NUM] [--min-activity MIN_ACTIVITY] [--min-nicks MIN_NICKS] [--max-topwords MAX_TOPWORDS] [-s {msgs,nicks}]
                [--include-channels [INCLUDE_CHANNELS [INCLUDE_CHANNELS ...]]] [--exclude-channels [EXCLUDE_CHANNELS [EXCLUDE_CHANNELS ...]]]
                [--disable-bot-filters]

Gather statistics from WeeChat log files.

optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        start analyzing messages from DURATION hours ago
  -n NUM, --num NUM     limit output to the top NUM channels
  --min-activity MIN_ACTIVITY
                        limit output to channels with at least MIN_ACTIVITY messages.
  --min-nicks MIN_NICKS
                        limit output to channels with at least MIN_NICKS nicks
  --max-topwords MAX_TOPWORDS
                        show the nicks and message counts for the MAX_TOPWORDS most active nicks
  -s {msgs,nicks}, --sort-by {msgs,nicks}
                        key to sort channels by
  --include-channels [INCLUDE_CHANNELS [INCLUDE_CHANNELS ...]]
                        only analyze these channels. format: "network.#channel"
  --exclude-channels [EXCLUDE_CHANNELS [EXCLUDE_CHANNELS ...]]
                        list of channels to exclude. format: "network.#channel"
  --disable-bot-filters
                        disable filtering of some known bots
```

#### Examples

Print the 10 most active IRC channels from the past 24 hours that have at least 40
chatters, along with the top 4 most active nicks per channel:

``` sh
clogstats -n 10 --sort-by msgs -d 24 --min-nicks 40 --max-topwords 4
```

Output:

``` text
Analyzing logs from 2020-05-18 15:58:14.626763 till 2020-05-19 15:58:14.626763
total messages: 33146
RANK CHANNEL                  MSGS NICKS TOPWORDS
1.   tilde_chat.#meta         2897 63    kumquat: 417, jan6: 410, brendo: 207, ben: 130
2.   snoonet.#gnulag          2838 50    browndawg: 592, ldlework: 172, mrneon: 140, iamidly: 134
3.   freenode.##linux         2753 147   floridaman: 346, phogg: 245, rascul: 189, lukey: 85
4.   freenode.#python         2491 145   corvus-corax: 214, snoopjedi: 191, teut: 167, _habnabit: 145
5.   efnet.#lrh               2024 81    rondito: 349, jupedbird: 236, butth0le: 80, \\\\\: 77
6.   freenode.#anime          1931 53    luke-jr: 198, amigojapan: 191, emmeka: 140, butternoodle: 129
7.   ircnet.#worldchat        1233 62    kanasta: 118, flowergirl42: 104, miri: 97, klywilen: 97
8.   quakenet.#quarantine     1149 51    olli: 149, redzain_: 142, chenko: 135, `sun357: 105
9.   darkscience.#darkscience 992  44    workinggoose: 145, sun-light: 108, dijit: 76, exusser: 68
10.  rizon.#chat              953  51    dorkmund: 113, dfx: 94, irish666: 84, piba: 70
```

Another example: say I finished an anime episode that just came out and want to talk
about it. Clogstats can filter my anime channels to just those that were active in
the past 30 minutes:

``` sh
clogstats -d 0.5 --sort-by msgs --min-activity 1 --include-channels \
	"freenode.##anime" "freenode.#anime" "freenode.#reddit-anime" \
	"quakenet.#anime" "rizon.#anime" "tilde_chat.#anime"
```

Output:

``` text
Analyzing logs from 2020-05-18 17:08:07.076732 till 2020-05-18 17:38:07.076732
total messages: 66
RANK CHANNEL         MSGS NICKS TOPWORDS
1.   freenode.#anime 65   11    MootPoot: 16, emmeka: 13, ButterNoodle: 13
2.   quakenet.#anime 1    1     Fanen: 1
```

Looks like the `#anime` channels on Freenode and QuakeNet are the only one with
recent activity.

FAQ
---

### Q: Is "clogstats" pronounced "see-log-stats" or "clog-stats"?

A: Yes.

License
-------

Copyright (C) 2020 Rohan Kumar

This program is free software: you can redistribute it and/or modify it under the
terms of the GNU Affero General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.

<!--
vi:ft=markdown.pandoc.gfm
-->
