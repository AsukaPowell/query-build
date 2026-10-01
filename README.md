# Query Build

A small, zero-dependency library for building and parsing query strings where repeated keys are kept intact rather than collapsed.

## Usage

```python
from query_build import QueryBuilder, parse_query, get_all, get_first

# Build
q = QueryBuilder().add("a", 1).add("a", 2).build()
# q == "a=1&a=2"

# Parse
pairs = parse_query("?a=1&a=2&b=3")
# pairs == [("a", "1"), ("a", "2"), ("b", "3")]

get_all(pairs, "a")   # ["1", "2"]
get_first(pairs, "a")  # "1"
```

## Why this exists

Most form-encoding libraries collapse repeated keys into a single value or keep them in a dict that loses order and duplicates. Real form submissions (multi-select inputs, repeated checkboxes) send `a=1&a=2`, and servers usually expose the first value as the scalar and all values as a list. This library mirrors that: `QueryBuilder` preserves every added pair in order, `parse_query` returns a list of `(key, value)` tuples, and the `get_first` / `get_all` helpers give the two access patterns callers actually need.

The trade-off is that pairs are returned as a flat list, not a dict. If you want a `{key: [values]}` mapping you call `get_all` per key yourself. This keeps the core API unambiguous about ordering and duplicates.

## Edge cases

- `get_first` distinguishes a present-but-empty key (`?a=` yields `""`) from a missing key (yields the default, `None` by default). This is the one case where a naive `.get()`-style helper goes wrong.
- A leading `?` on the input to `parse_query` is stripped. We do not attempt to preserve a literal `?` as a key character; `??a=1` parses to `[("a", "1")]`.
- Empty chunks from a doubled separator (`a=1&&b=2`) are skipped rather than surfaced as `("", "")`.

## Exported names

- `QueryBuilder` — builder with `.add(key, value)` and `.build()`.
- `parse_query(str) -> list[tuple[str, str]]` — parses (with or without a leading `?`).
- `get_all(pairs, key) -> list[str]` — every value for `key`.
- `get_first(pairs, key, default=None) -> str | None` — first value, or `default` only when the key is absent.
