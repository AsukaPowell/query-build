"""Build and parse query strings with repeated keys.

A single key may legitimately appear more than once in a query string
(?a=1&a=2). Rather than collapse repeats into a single value, this module
keeps every occurrence and exposes both the full ordered list and a scalar
getter that returns the first occurrence (matching how most servers parse
repeated keys).
"""

from __future__ import annotations

from urllib.parse import quote, unquote


def _encode(value: object) -> str:
    """Percent-encode a value using application/x-www-form-urlencoded rules.

    The x-www-form-urlencoded format uses '+' for spaces, which is the form
    browsers submit and servers expect. quote(value, safe='') encodes
    everything (including '/') which is what form-encoding demands.
    """
    return quote(str(value), safe="").replace("%20", "+")


class QueryBuilder:
    """Build a query string from ordered (key, value) pairs.

    Repeated keys are kept in order: a=1&a=2 stays a=1&a=2 rather than being
    merged. This preserves the meaning of repeated params (e.g. multi-select
    lists) the way the receiving server would see them.

    Example:
        >>> QueryBuilder().add("a", 1).add("b", x).build()
        'a=1&b=x'
        >>> QueryBuilder().add("a", 1).add("a", 2).build()
        'a=1&a=2'
    """

    def __init__(self) -> None:
        # A flat list of (key, value) pairs: preserves order AND repeats,
        # which a dict would destroy. This is the central design choice.
        self._pairs: list[tuple[str, str]] = []

    def add(self, key: str, value: object) -> "QueryBuilder":
        """Add a key/value pair. Repeated keys are allowed and kept in order."""
        self._pairs.append((str(key), str(value)))
        return self

    def build(self) -> str:
        """Return the query string (without a leading '?').

        Returns an empty string when no pairs have been added, so the result
        can be safely prefixed with '?' without producing a dangling '?'.
        """
        if not self._pairs:
            return ""
        return "&".join(
            f"{_encode(k)}={_encode(v)}" for k, v in self._pairs
        )


def parse_query(query: str):
    """Parse a query string into a list of (key, value) pairs.

    The list preserves the source order and every occurrence of a repeated
    key. Keys with no '=' are parsed as the key with an empty string value.

    Leading '?' is stripped so the function accepts the common forms
    ("a=1", "?a=1", and even "??a=1" which some routing layers produce).
    This is an explicit, tested decision: we do not attempt to preserve a
    literal '?' key.
    """
    while query.startswith("?"):
        query = query[1:]
    if not query:
        return []
    pairs: list[tuple[str, str]] = []
    for chunk in query.split("&"):
        if not chunk:
            # Skip empty chunks produced by "a=1&&b=2". We do not surface
            # them as ('', '') because that would be inventing a pair the
            # source string did not meaningfully contain.
            continue
        if "=" in chunk:
            key, _, value = chunk.partition("=")
        else:
            key, value = chunk, ""
        pairs.append((unquote(key.replace("+", " ")), unquote(value.replace("+", " "))))
    return pairs


def get_all(pairs: list[tuple[str, str]], key: str) -> list[str]:
    """Return every value for `key` in `pairs`, in order; empty list if none."""
    return [v for k, v in pairs if k == key]


def get_first(pairs: list[tuple[str, str]], key: str, default: str | None = None) -> str | None:
    """Return the first value for `key`, or `default` if the key is absent.

    An empty value (e.g. 'a=' yields '') is returned as-is; only a missing
    key triggers the default. This mirrors how servers distinguish ?a= from
    (no a).
    """
    for k, v in pairs:
        if k == key:
            return v
    return default


__all__ = ["QueryBuilder", "parse_query", "get_all", "get_first"]
