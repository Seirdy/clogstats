"""Extract raw data from a single IRC message."""

from typing import Optional


# regexes
ANSI_ESCAPE = r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]"
NICK_PREFIXES = {"+", "%", "@", "~", "&"}


def strip_nick_prefix(nick: Optional[str]) -> Optional[str]:
    """Strip out nick prefixes showing enabled modes."""
    if nick is not None:
        nick = str(nick)  # someone on gitter haa the nick "nan". https://xkcd.com/327/
        if nick[0] in NICK_PREFIXES:
            return nick[1:]
    return nick


def msg_type(prefix: str) -> str:
    """Type of IRC message, determined by the message prefix.

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
            "": "other",  # empty string = no prefix: other. rarely occurs in the wild.
        }[prefix]
    except KeyError:
        # the prefix is a nick
        return "message"
