import unittest

import helpers  # noqa: F401  (sets the import path)
from jqd import quotes

PAGES = [
    "We describe the plat-\nform and its users. The “top one percent” wrote most posts.",
    "The classiﬁer reached high agreement – as expected – with the coders.\nIt isn’t a census of all users.",
    "The share was 6.1% before the change and 8.3% afterwards, a diffe-\nrence of two points.",
]


class QuoteTests(unittest.TestCase):
    def test_finds_quote_despite_hyphenation(self):
        self.assertEqual(quotes.find_quote("We describe the platform and its users", PAGES, 1), ("ok", 1))
        self.assertEqual(quotes.find_quote("a difference of two points", PAGES, 3), ("ok", 3))

    def test_line_break_hyphens_are_removed_from_text_and_stored_quotes(self):
        from jqd.common import dehyphenate, page_sentences
        self.assertEqual(dehyphenate("neither suﬀi- ciently measured"), "neither sufficiently measured")
        self.assertEqual(dehyphenate("pre- and post-treatment"), "pre- and post-treatment")
        self.assertEqual(dehyphenate("COVID- 19 and Twitter/X- Facebook"), "COVID- 19 and Twitter/X- Facebook")
        self.assertIn("sufficiently measured", page_sentences("It is not suffi-\nciently measured.")[0][1])

    def test_finds_quote_despite_ligatures_and_typographic_marks(self):
        self.assertEqual(quotes.find_quote("The classifier reached high agreement - as expected", PAGES, 2), ("ok", 2))
        self.assertEqual(quotes.find_quote('The "top one percent" wrote most posts', PAGES, 1), ("ok", 1))
        self.assertEqual(quotes.find_quote("It isn't a census of all users", PAGES, 2), ("ok", 2))

    def test_page_plus_minus_one_is_accepted(self):
        self.assertEqual(quotes.find_quote("The share was 6.1% before the change", PAGES, 2), ("ok", 2))

    def test_quote_on_distant_page_is_moved(self):
        self.assertEqual(quotes.find_quote("The share was 6.1% before the change", PAGES, 1), ("moved", 3))

    def test_ellipsis_joins_two_parts(self):
        self.assertEqual(quotes.find_quote("The share was 6.1% … a difference of two points", PAGES, 3), ("ok", 3))

    def test_small_typo_is_tolerated_but_invented_quotes_are_rejected(self):
        self.assertEqual(quotes.find_quote("The clasifier reached high agreement as expected with the coders", PAGES, 2)[0], "ok")
        self.assertEqual(quotes.find_quote("95 % confidence intervals are shown", PAGES, 2), ("missing", None))
        self.assertEqual(quotes.find_quote("The share was 9.9% before the change and 1.2% afterwards", PAGES, 3)[0], "missing")

    def test_quote_spanning_a_page_break(self):
        self.assertEqual(quotes.find_quote("wrote most posts. The classifier reached", PAGES, 1)[0], "ok")


if __name__ == "__main__":
    unittest.main()
