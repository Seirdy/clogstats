weestats
========

[![sourcehut](https://img.shields.io/badge/repository-sourcehut-lightgrey.svg?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZlcnNpb249IjEuMSINCiAgICB3aWR0aD0iMTI4IiBoZWlnaHQ9IjEyOCI+DQogIDxkZWZzPg0KICAgIDxmaWx0ZXIgaWQ9InNoYWRvdyIgeD0iLTEwJSIgeT0iLTEwJSIgd2lkdGg9IjEyNSUiIGhlaWdodD0iMTI1JSI+DQogICAgICA8ZmVEcm9wU2hhZG93IGR4PSIwIiBkeT0iMCIgc3RkRGV2aWF0aW9uPSIxLjUiDQogICAgICAgIGZsb29kLWNvbG9yPSJibGFjayIgLz4NCiAgICA8L2ZpbHRlcj4NCiAgICA8ZmlsdGVyIGlkPSJ0ZXh0LXNoYWRvdyIgeD0iLTEwJSIgeT0iLTEwJSIgd2lkdGg9IjEyNSUiIGhlaWdodD0iMTI1JSI+DQogICAgICA8ZmVEcm9wU2hhZG93IGR4PSIwIiBkeT0iMCIgc3RkRGV2aWF0aW9uPSIxLjUiDQogICAgICAgIGZsb29kLWNvbG9yPSIjQUFBIiAvPg0KICAgIDwvZmlsdGVyPg0KICA8L2RlZnM+DQogIDxjaXJjbGUgY3g9IjUwJSIgY3k9IjUwJSIgcj0iMzglIiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjQlIg0KICAgIGZpbGw9Im5vbmUiIGZpbHRlcj0idXJsKCNzaGFkb3cpIiAvPg0KICA8Y2lyY2xlIGN4PSI1MCUiIGN5PSI1MCUiIHI9IjM4JSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSI0JSINCiAgICBmaWxsPSJub25lIiBmaWx0ZXI9InVybCgjc2hhZG93KSIgLz4NCjwvc3ZnPg0KCg==)](https://git.sr.ht/~seirdy/weestats)
[![GitLab
mirror](https://img.shields.io/badge/mirror-GitLab-orange.svg?logo=gitlab)](https://gitlab.com/Seirdy/weestats)
[![GitHub
mirror](https://img.shields.io/badge/mirror-GitHub-black.svg?logo=github)](https://github.com/Seirdy/weestats)

Weestats tells you statistics about your WeeChat channels by reading your chat logs.
It can currently tell you the most active IRC channels and nicks across a given
duration (the last 24 hours by default).

The motivation for writing weestats was to overcome the limitations of its
predecessor, [chattiest-channels](https://git.sr.ht/~seirdy/chattiest-channels);
chattiest-channels served mostly as a proof-of-concept and had *very* messy date/time
handling.

Dependencies
------------

Weestats supports CPython 3.6+ and PyPy3 7.3+.

Python 3.7+: no 3rd-party dependencies.

Python 3.6: the only 3rd-party dependency is [a
backport](https://pypi.org/project/dataclasses/) of Python 3.7's `dataclasses`
library.

Installation
------------

Install with `pip`:

``` sh
python3 -m pip install git+https://git.sr.ht/~seirdy/weestats
```

Flood mitigation
----------------

Mitigating the effects of spam and flooding continues to be an ongoing challenge.
Flood mitigation measures include:

- Merging consecutive messages from the same nick

Planned areas of improvement for flood mitigation primarily involve filtering out
messages by user-configurable per-network regular expressions and nick blacklists.

Features and Usage
------------------

Weestats can sort channels by their number of messages or number of non-lurkers
(i.e., the number of nicks that actually sent a message). It can also display the top
most active nicks for each channel. It can also display the top most active nicks for
each channel.

Full usage:

``` text
usage: weestats [-h] [-d DURATION] [-n NUM] [--min-activity MIN_ACTIVITY] [--min-nicks MIN_NICKS] [--max-topwords MAX_TOPWORDS] [-s {msgs,nicks}]
                [--exclude-channels [EXCLUDE_CHANNELS [EXCLUDE_CHANNELS ...]]]

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
  --exclude-channels [EXCLUDE_CHANNELS [EXCLUDE_CHANNELS ...]]
                        list of channels to exclude. format: "network.#channel"
```

Examples
--------

Print the 10 most active IRC channels from the past 24 hours that have at least 40
chatters, along with the top 4 most active nicks per channel:

``` sh
$ weestats -n 10 --sort-by msgs -d 24 --min-nicks 40 --max-topwords 4
```

Output:

``` text
Analyzing logs from 2020-05-17 15:40:40.375215 till 2020-05-18 15:40:40.375215
total messages: 37955
RANK CHANNEL              MSGS NICKS TOPWORDS
1.   tilde_chat.#meta     4072 58    kumquat: 517, jan6: 474, brendo: 332, cyberia: 267
2.   freenode.##linux     3418 181   FloridaMan: 268, pjt_014: 179, quartz12: 173, lukey: 173
3.   snoonet.#gnulag      3122 49    browndawg: 596, RadiantBastard: 239, k33k: 209, audron: 200
4.   freenode.#python     2298 144   grym: 144, celphi: 130, graingert: 121, _habnabit: 110
5.   freenode.#anime      2231 47    sentionics: 308, amigojapan: 256, ImoutoBot: 248, dfch: 230
6.   efnet.#lrh           2143 80    Dwaine: 352, rondito: 284, WeEatnKid: 101, aids: 88
7.   rizon.#chat          1665 60    DORKMUND: 179, Frogorg: 119, Piba: 116, sushi-chan: 113
8.   quakenet.#quarantine 1635 56    chenko: 228, olli: 222, redzain: 180, toxik: 141
9.   freenode.##chat      1444 54    mijowh_: 184, Gus_van_Ekelenbu: 165, yuken: 128, jordansinn: 114
10.  ircnet.#worldchat    1241 53    Miri: 238, rud0lf: 121, Flowergirl42: 78, FinFury: 72
```

Another example: say I finished an anime episode that just came out and want to talk
about it. Weestats can filter my anime channels to just those that were active in the
past 30 minutes:

``` sh
weestats -d 0.5 --include-channels "freenode.##anime" "freenode.#anime" "freenode.#reddit-anime" "quakenet.#anime" "rizon.#anime" "tilde_chat.#anime" --sort-by msgs --min-activity 1
```

Output:

``` text
Analyzing logs from 2020-05-18 16:03:07.055394 till 2020-05-18 16:33:07.055394
total messages: 58
RANK CHANNEL         MSGS NICKS TOPWORDS                               
1.   freenode.#anime 58   11    MootPoot: 18, BillyZane: 11, S_T_A_N: 8
```

Looks like `freenode.#anime` was the only one with recent activity.

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
