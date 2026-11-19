import os
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import FIX
from jqd import extract


class ExtractTests(unittest.TestCase):
    def test_text_with_form_feeds_gives_pages_and_markers(self):
        doc = extract.extract_file(FIX / "manuscript.txt")
        self.assertEqual(len(doc["pages"]), 5)
        self.assertFalse(doc["synthetic"])
        marked = extract.to_marked(doc["pages"])
        self.assertIn("⟨p.3⟩\n3 Measures", marked)
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "m.txt").write_text(marked, encoding="utf-8")
            self.assertEqual(extract.load_marked(tmp / "m.txt"), doc["pages"])
        finally:
            shutil.rmtree(tmp)

    def _check_pdf(self, doc):
        self.assertEqual(len(doc["pages"]), 5)
        self.assertEqual(doc["page_offset"], 10, "printed page numbers start at 11")
        joined = "\n".join(doc["pages"])
        self.assertNotIn("manuscript draft", joined, "running header must be removed")
        self.assertIn("4.3 Incivility", doc["pages"][3])

    def test_pdf_with_vendored_pypdf(self):
        os.environ["JQD_NO_PDFTOTEXT"] = "1"
        try:
            doc = extract.extract_file(FIX / "manuscript.pdf")
        finally:
            del os.environ["JQD_NO_PDFTOTEXT"]
        self.assertEqual(doc["tool"], "pypdf")
        self._check_pdf(doc)

    @unittest.skipUnless(shutil.which("pdftotext"), "pdftotext not installed")
    def test_pdf_with_pdftotext(self):
        doc = extract.extract_file(FIX / "manuscript.pdf")
        self.assertEqual(doc["tool"], "pdftotext")
        self._check_pdf(doc)

    def test_scanned_pdf_is_an_error_with_instruction(self):
        with self.assertRaises(extract.ExtractError) as cm:
            extract.extract_file(FIX / "scanned.pdf")
        self.assertIn("OCR", cm.exception.fix)

    def test_zones_separate_main_text_references_and_appendix(self):
        pages = extract.extract_file(FIX / "manuscript.txt")["pages"]
        pages = pages + ["Appendix A: Codebook\n\nThe codebook lists every category with two examples each."]
        sections = extract.detect_sections(pages)
        zones = extract.zone_texts(pages, sections)
        self.assertIn("Network Press", zones["references"])
        self.assertNotIn("Network Press", zones["main"])
        self.assertIn("codebook lists", zones["appendix"])
        self.assertIn("7 Conclusion", zones["main"])
        titles = [s["title"] for s in sections]
        for expected in ("Abstract", "1 Introduction", "4.1 Posting is concentrated", "References"):
            self.assertIn(expected, titles)

    def test_abstract_without_heading_above_keywords_across_a_page_break(self):
        title = ("Journal of Quantitative Description: Digital Media 6(2026), 1–20\n\n"
                 "        A Study of Something Online\n\n            ANNE AUTHOR\n        Some University, USA\n\n")
        part1 = " ".join(["The first part of the abstract describes the data and the main measure in plain words."] * 3)
        part2 = " ".join(["The second part reports the headline finding and what it means for the field."] * 2)
        pages = [title + "\n".join(part1[i:i + 70] for i in range(0, len(part1), 70))
                 + "\n anne@uni.example\n Date submitted: 2025-01-01\n\nCopyright ©2026 (Anne Author). Licensed under CC.",
                 "Author  Journal of Quantitative Description: Digital Media 6(2026) 2\n\n"
                 + "\n".join(part2[i:i + 70] for i in range(0, len(part2), 70))
                 + "\n\nKeywords: online, data\n\nIntroduction\n\nText."]
        page, text = extract.find_abstract(pages, extract.detect_sections(pages))
        self.assertEqual(page, 1)
        self.assertTrue(text.startswith("The first part") and text.rstrip().endswith("for the field."), text)
        self.assertNotIn("Copyright", text)
        self.assertNotIn("ANNE", text)
        labelled = ["Title\n\nAbstract: " + part2 + "\n\nIntroduction\n\nText."]
        self.assertEqual(extract.find_abstract(labelled, extract.detect_sections(labelled))[1].split()[0], "The")
        self.assertIsNone(extract.find_abstract(["Title\n\nIntroduction\n\nText only."], []))

    def test_section_span(self):
        pages = extract.extract_file(FIX / "manuscript.txt")["pages"]
        title, page, text = extract.section_span(pages, extract.detect_sections(pages), "limitations")
        self.assertEqual((title, page), ("6 Limitations", 5))
        self.assertIn("lower bound", text)
        self.assertNotIn("7 Conclusion", text)

    def test_text_without_page_breaks_gets_pseudo_pages(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            para = "This paragraph has a number of words that describe a platform in plain language. " * 8
            (tmp / "m.md").write_text("# Title\n\n" + "\n\n".join([para] * 12), encoding="utf-8")
            doc = extract.extract_file(tmp / "m.md")
            self.assertTrue(doc["synthetic"])
            self.assertGreater(len(doc["pages"]), 1)
            with self.assertRaises(extract.ExtractError):
                extract.extract_file(tmp / "missing.pdf")
            (tmp / "m.xyz").write_text("x", encoding="utf-8")
            with self.assertRaises(extract.ExtractError):
                extract.extract_file(tmp / "m.xyz")
        finally:
            shutil.rmtree(tmp)

    def test_docx_with_headings_and_page_break(self):
        ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
        body = ('<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Introduction</w:t></w:r></w:p>'
                + '<w:p><w:r><w:t>' + "We describe a platform in some detail with enough words. " * 3 + '</w:t></w:r></w:p>'
                + '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
                + '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Results</w:t></w:r></w:p>'
                + '<w:p><w:r><w:t>' + "The share was 12% &amp; rising across the whole period studied. " * 3 + '</w:t></w:r></w:p>')
        tmp = Path(tempfile.mkdtemp())
        try:
            with zipfile.ZipFile(tmp / "m.docx", "w") as zf:
                zf.writestr("word/document.xml", f'<w:document {ns}><w:body>{body}</w:body></w:document>')
            doc = extract.extract_file(tmp / "m.docx")
            self.assertEqual(len(doc["pages"]), 2)
            self.assertIn("12% & rising", doc["pages"][1])
            self.assertEqual([s["title"] for s in extract.detect_sections(doc["pages"])], ["Introduction", "Results"])
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
