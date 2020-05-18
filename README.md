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

Weestats only depends on the Python standard library. It supports CPython 3.6+ and
PyPy3 7.3+.

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

Usage
-----

``` text
usage: weestats [-h] [-d DURATION] [-n NUM] [-m MIN_ACTIVITY]

Gather statistics from WeeChat log files.

optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        start analyzing messages from DURATION hours ago
  -n NUM, --num NUM     limit output to the top NUM channels
  -m MIN_ACTIVITY, --min-activity MIN_ACTIVITY
                        limit output to channels with at least this many messages.
```

Example
-------

Print the most active IRC channels from the past 12 hours:

``` text
$ weestats -d 12 -n 10
Analyzing logs from 2020-05-16 03:07:28.351300 till 2020-05-16 15:07:28.351300
total messages: 19641
RANK CHANNEL           MSGS TOPWORDS
1.   snoonet.#gnulag   2400 browndawg: 384, MrNeon: 228, crystalmett: 226
2.   freenode.#python  1715 bjs: 246, ChrisWarrick: 150, nedbat: 89
3.   freenode.##linux  1464 noodlepie: 227, rascul: 107, MrElendig: 97
4.   efnet.#lrh        1371 Dwaine: 371, darkfader: 148, aids: 148
5.   rizon.#chat       1367 dufferz: 187, Moo-Bun: 151, Frogorg: 134
6.   tilde_chat.#meta  1185 kumquat: 186, jan6: 181, tomasino: 131
7.   ircnet.#worldchat 1075 DeusPrometheus: 150, ob1: 132, l3mv: 77
8.   freenode.#music   734  murthy: 242, nativetexan: 168, FireSword: 106
9.   2600net.#2600     728  snowice0: 138, maestro: 112, oxagast: 89
10.  freenode.#anime   711  ImoutoBot: 80, amigojapan: 78, Fenderbassist: 72
```

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
