import unittest

from query_build import QueryBuilder, parse_query, get_all, get_first


class TestQueryBuilder(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(QueryBuilder().build(), "")

    def test_single(self):
        self.assertEqual(QueryBuilder().add("a", 1).build(), "a=1")

    def test_multiple_distinct_keys(self):
        self.assertEqual(QueryBuilder().add("a", 1).add("b", 2).build(), "a=1&b=2")

    def test_repeated_key_preserved(self):
        self.assertEqual(QueryBuilder().add("a", 1).add("a", 2).build(), "a=1&a=2")

    def test_order_preserved(self):
        b = QueryBuilder().add("b", 1).add("a", 2).add("b", 3)
        self.assertEqual(b.build(), "b=1&a=2&b=3")

    def test_int_value_coerced(self):
        self.assertEqual(QueryBuilder().add("n", 42).build(), "n=42")

    def test_space_encoded_as_plus(self):
        self.assertEqual(QueryBuilder().add("q", "hello world").build(), "q=hello+world")

    def test_special_chars_encoded(self):
        self.assertEqual(QueryBuilder().add("k", "a/b&c=d").build(), "k=a%2Fb%26c%3Dd")

    def test_empty_value(self):
        self.assertEqual(QueryBuilder().add("a", "").build(), "a=")


class TestParseQuery(unittest.TestCase):

    def test_empty_string(self):
        self.assertEqual(parse_query(""), [])

    def test_leading_question_mark_stripped(self):
        self.assertEqual(parse_query("?a=1&b=2"), [("a", "1"), ("b", "2")])

    def test_double_question_mark(self):
        # Explicit interpretation: all leading '?' are stripped. We do not
        # preserve a literal '?' key. This is the documented decision.
        self.assertEqual(parse_query("??a=1"), [("a", "1")])

    def test_single_pair(self):
        self.assertEqual(parse_query("a=1"), [("a", "1")])

    def test_repeated_key_kept(self):
        self.assertEqual(parse_query("a=1&a=2"), [("a", "1"), ("a", "2")])

    def test_key_without_value(self):
        self.assertEqual(parse_query("flag"), [("flag", "")])

    def test_empty_value_kept(self):
        self.assertEqual(parse_query("a="), [("a", "")])

    def test_plus_decodes_to_space(self):
        self.assertEqual(parse_query("q=hello+world"), [("q", "hello world")])

    def test_percent_decoding(self):
        self.assertEqual(parse_query("k=a%2Fb%26c%3Dd"), [("k", "a/b&c=d")])

    def test_double_ampersand_skipped(self):
        # Empty chunks (from "a=1&&b=2") are skipped rather than surfaced as
        # ('', ''). This matches the documented behaviour.
        self.assertEqual(parse_query("a=1&&b=2"), [("a", "1"), ("b", "2")])

    def test_order_preserved(self):
        self.assertEqual(parse_query("b=1&a=2&b=3"),
                         [("b", "1"), ("a", "2"), ("b", "3")])


class TestGetHelpers(unittest.TestCase):

    def test_get_all_returns_every_occurrence(self):
        pairs = parse_query("a=1&a=2&b=3")
        self.assertEqual(get_all(pairs, "a"), ["1", "2"])

    def test_get_all_missing_key_empty_list(self):
        self.assertEqual(get_all(parse_query("a=1"), "z"), [])

    def test_get_first_returns_first(self):
        self.assertEqual(get_first(parse_query("a=1&a=2"), "a"), "1")

    def test_get_first_missing_returns_none_by_default(self):
        self.assertIsNone(get_first(parse_query("a=1"), "z"))

    def test_get_first_missing_returns_default(self):
        self.assertEqual(get_first(parse_query("a=1"), "z", default="x"), "x")

    def test_get_first_distinguishes_empty_from_missing(self):
        # "a=" means the key IS present with an empty value; we must not
        # substitute the default. This is the awkward edge.
        self.assertEqual(get_first(parse_query("a="), "a"), "")


if __name__ == "__main__":
    unittest.main()
