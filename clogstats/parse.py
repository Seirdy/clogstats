"""Extract raw data from a single IRC message."""

import re

# precompiled regexes
ANSI_ESCAPE = r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]"
_ANSI_ESCAPE_RE = re.compile(ANSI_ESCAPE)
_TAB = re.compile("\t")
NICK_PREFIXES = {"+", "%", "@", "~", "&"}


def strip_nick_prefix(nick: str) -> str:
    """Strip out nick prefixes showing enabled modes."""
    if nick[0] in NICK_PREFIXES:
        return nick[1:]
    return nick


def msg_type(prefix: str) -> str:
    """Type of IRC message.

    See WeeChat Plugin API docs for prefixes and their meanings.
    """
    # if the prefix string isn't a nick, it's a special kind of message.
    # otherwise, it's a regular message
    try:
        return {
            "=!=": "error",
            "--": "network",
            " *": "action",
            "-->": "join",
            "<--": "quit",
            "": "other",
        }[prefix]
    except KeyError:
        return "message"


def escape_ansi(line: str) -> str:
    """Remove ANSI escape sequences logged by WeeChat."""
    return _ANSI_ESCAPE_RE.sub("", line)
