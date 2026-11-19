import re
import unittest

from helpers import FIX
from jqd import extract, metrics


def fixture_metrics():
    pages = extract.extract_file(FIX / "manuscript.txt")["pages"]
    return pages, metrics.compute(pages, extract.detect_sections(pages))


class MetricsTests(unittest.TestCase):
    def test_word_count_within_three_percent_of_manual_count(self):
        raw = (FIX / "manuscript.txt").read_text(encoding="utf-8")
        main = raw.split("\nReferences\n")[0]
        manual = len([t for t in main.split() if re.search(r"\w", t)])
        _, m = fixture_metrics()
        self.assertLessEqual(abs(m["words_main"] - manual) / manual, 0.03, (m["words_main"], manual))

    def test_figures_and_tables_are_exact(self):
        _, m = fixture_metrics()
        self.assertEqual((m["figures"], m["tables"]), (3, 2))
        self.assertEqual([x["label"] for x in m["items"]], ["Tab 1", "Fig 1", "Fig 2", "Tab 2", "Fig 3"])
        self.assertIn("N = 18,902 accounts", m["items"][1]["caption"])

    def test_sentences_about_figures_are_not_captions(self):
        pages = ["Results\n\nFigure 4 shows the trend over time.\n\nFig. 5: Share by year.\n\n"
                 "Abbildung 6: Anteil nach Jahr.\n\nTabelle 2. Übersicht der Daten.\n\nTable 3 is discussed below."]
        m = metrics.compute(pages, extract.detect_sections(pages))
        self.assertEqual(sorted(x["label"] for x in m["items"]), ["Fig 5", "Fig 6", "Tab 2"])

    @unittest.skipUnless(metrics.CITATION_CHECK, "citation check is switched off")
    def test_citations_against_reference_list(self):
        _, m = fixture_metrics()
        self.assertTrue(m["references_found"])
        self.assertEqual(m["citations_missing_in_refs"], ["Tanaka 2019"])
        self.assertEqual(m["refs_never_cited"], ["Weber 2017"])

    def test_broken_cross_references(self):
        _, m = fixture_metrics()
        self.assertEqual(m["broken_crossrefs"], ["Section 8 (p. 2)", "Figure 9 (p. 4)"])
        self.assertEqual(m["unresolved_markers"], [])

    def test_supplementary_mentions_are_not_candidates_and_qq_markers_are_found(self):
        pages, _ = fixture_metrics()
        extra = "\nSee Supplementary Table 14 and Online Figure 7. As Figure ?? and Section ?? show, it holds.\n"
        pages2 = pages[:2] + [pages[2] + extra] + pages[3:]
        m = metrics.compute(pages2, extract.detect_sections(pages2))
        self.assertEqual(m["broken_crossrefs"], ["Section 8 (p. 2)", "Figure 9 (p. 4)"])
        self.assertEqual(m["unresolved_markers"], ["Figure ?? (p. 3)", "Section ?? (p. 3)"])

    def test_abstract_and_appendix_status(self):
        pages, m = fixture_metrics()
        self.assertTrue(95 <= m["abstract_words"] <= 103, m["abstract_words"])
        self.assertEqual(m["appendix"], "none")
        pages2 = pages[:4] + [pages[4].replace("Our study has limitations.", "Details are in the online appendix.")]
        self.assertEqual(metrics.compute(pages2, extract.detect_sections(pages2))["appendix"], "referenced_elsewhere")
        m3 = metrics.compute(pages, extract.detect_sections(pages), ["Figure A1: Extra plot of the same data by year."])
        self.assertEqual(m3["appendix"], "present")
        self.assertIn("Fig A1", [x["label"] for x in m3["items"]])

    def test_size_line_is_rule_based(self):
        line, norms = metrics.size_summary({"words_main": 8140, "figures": 7, "tables": 2, "abstract_words": 212,
                                            "appendix": "referenced_elsewhere"}, "full")
        self.assertEqual(line, "~8,100 words main text · 7 figures · 2 tables · appendix referenced elsewhere")
        self.assertIn("within the typical range for full papers", norms)
        _, norms = metrics.size_summary({"words_main": 16000, "figures": 30, "tables": 0, "abstract_words": 300,
                                         "appendix": "none"}, "full")
        self.assertIn("above", norms)
        self.assertIn("number of figures", norms)
        self.assertIn("abstract (300 words)", norms)


if __name__ == "__main__":
    unittest.main()
