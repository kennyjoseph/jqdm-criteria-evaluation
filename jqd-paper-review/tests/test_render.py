import copy
import re
import unittest

from helpers import Workdir, example
from jqd import render, validate


class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = Workdir(manuscript="manuscript.pdf")
        cls.code, cls.out = cls.w.run_all()
        cls.state = cls.w.state()
        cls.page = next((cls.w.dir / "out").glob("*.html")).read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.w.close()

    def html(self, state):
        return render.render_html(render.build_view(state))

    def test_identical_registry_gives_byte_identical_output(self):
        a = self.html(copy.deepcopy(self.state)).encode("utf-8")
        b = self.html(copy.deepcopy(self.state)).encode("utf-8")
        self.assertEqual(a, b)
        self.assertEqual(a, self.page.encode("utf-8"), "file on disk equals a fresh rendering")
        self.assertNotIn(b"\r", a)

    def test_no_external_resources_and_no_script(self):
        for pattern in (r"https?://", r"<script", r"<link", r"@import", r"url\(", r"<img", r"<iframe", r"\{\{"):
            self.assertIsNone(re.search(pattern, self.page, re.I), pattern)
        self.assertIn("prefers-color-scheme: dark", self.page)
        self.assertIn("@media print", self.page)

    def test_response_section_lists_low_rows_and_critical_gaps(self):
        view = render.build_view(copy.deepcopy(self.state))
        crit = {c["id"] for c in view["critical"]}
        expect = [(r["code"], [x["id"] for x in r["gaps"] if r["score"] in (0, 1) or x["id"] in crit])
                  for g in view["groups"] for r in g["rows"]]
        expect = [e for e in expect if e[1]]
        got = [(x["label"].split()[0], [i["label"] for i in x["items"]]) for x in view["responses"]]
        self.assertEqual(got, expect)
        self.assertTrue(crit)
        self.assertTrue(all(i["why"] for x in view["responses"] for i in x["items"] if i["label"] in crit))
        self.assertNotIn("Critical issue", self.page)
        self.assertIn("Why it matters:", self.page)
        self.assertIn("One potential fix:", self.page)
        gid = view["groups"][0]["rows"][0]["gaps"][0]["id"] if view["groups"][0]["rows"][0]["gaps"] else None
        if gid:
            self.assertIn(f'<strong class="gid">{gid}</strong>', self.page)
        s = copy.deepcopy(self.state)
        s["synthesis"]["critical"] = []
        for r in s["rows"].values():
            if r["score"] in (0, 1):
                r["score"] = 2
        self.assertIn("Nothing requires a response.", self.html(s))

    def test_text_is_escaped(self):
        s = copy.deepcopy(self.state)
        s["rows"]["D1"]["gaps"][0]["text"] = "Shares <5% & >95% are pooled in <b>one</b> group."
        s["orientation"]["title"] = "A <script>alert(1)</script> & B"
        page = self.html(s)
        self.assertIn("Shares &lt;5% &amp; &gt;95% are pooled in &lt;b&gt;one&lt;/b&gt; group.", page)
        self.assertIn("A &lt;script&gt;alert(1)&lt;/script&gt; &amp; B", page)
        self.assertNotIn("<script>", page)

    def test_sections_in_order_and_sixteen_rows(self):
        heads = re.findall(r"<h2>(.*?)</h2>", self.page)
        self.assertEqual(heads, ["The paper in one sentence", "Strengths", "Response required at submission", "Size", "Scores by criterion",
                                 "What JQD:DM papers tend to have that this one may not",
                                 "Other changes that would strengthen the paper", "Smaller fixes"])
        self.assertEqual(len(re.findall(r'<td class="code">', self.page)), 16)
        self.assertEqual(len(re.findall(r'<tr class="group">', self.page)), 5)

    def test_badges_signs_and_tags_read_without_colour(self):
        self.assertIn('<span class="badge s2">2</span> Mostly', self.page)
        self.assertIn('<span class="badge s3">3</span> Fully', self.page)
        self.assertIn('<span class="sign">+</span>', self.page)
        self.assertIn('<span class="sign">−</span>', self.page)
        self.assertIn('<span class="tag">analysis · moderate</span>', self.page)
        s = copy.deepcopy(self.state)
        s["rows"]["D2"].update(score=1)
        s["rows"]["L1"].update(score="NA", na_reason="No Letter of Inquiry provided.", gaps=[], plus=[])
        page = self.html(s)
        self.assertIn('<span class="badge s1">1</span> Partly', page)
        self.assertIn('<span class="badge sna">N/A</span>', page)
        self.assertIn("Every gap in this criterion has a small fix", page)
        s["rows"]["D2"].update(score=0)
        self.assertNotIn("Every gap in this criterion has a small fix", self.html(s))
        s["rows"]["C2"]["gaps"] = s["rows"]["C2"]["gaps"] or [copy.deepcopy(s["rows"]["D2"]["gaps"][0])]
        self.assertIn(render.LIT_NOTE, render.html_to_text(self.html(s)))
        s["rows"]["C2"]["gaps"] = []
        self.assertNotIn(render.LIT_NOTE, render.html_to_text(self.html(s)))

    def test_printed_page_numbers_and_claim_ids(self):
        self.assertEqual(self.state["meta"]["page_offset"], 10)
        self.assertIn("(p. 14)", self.page)       # marker page 4 → printed page 14
        self.assertNotRegex(render.html_to_text(self.page), r"\bH[1-5]\b")
        self.assertIn("“7.4% of posts are uncivil; share rose after 2021”", render.html_to_text(self.page))

    def test_no_overall_score_no_names_no_file_name(self):
        text = render.html_to_text(self.page)
        self.assertEqual(validate.decision_words(text), [])
        for forbidden in ("Jordan", "Riley", "Nowhere", "manuscript.pdf", "@"):
            self.assertNotIn(forbidden, text)
        self.assertRegex(self.page, r"Run [0-9a-f]{6} · jqd-paper-review 2026\.11\.17 · model: unknown")

    def test_features_section_is_built_by_rule(self):
        s = copy.deepcopy(self.state)
        for code in ("D3", "P1", "C4", "C5"):
            for key in s["rows"][code]["features"]:
                s["rows"][code]["features"][key] = "absent"
        feats = render.build_view(s)["features"]
        self.assertEqual(len(feats), 5)
        self.assertTrue(feats[0]["loc"].startswith("D3"), "rows whose gaps bear on headline claims come first")
        self.assertEqual(feats, render.build_view(copy.deepcopy(s))["features"])

    def test_cross_reference_candidates_are_not_printed_but_qq_markers_are(self):
        s = copy.deepcopy(self.state)
        self.assertTrue(s["metrics"]["broken_crossrefs"], "fixture has candidates")
        self.assertNotIn("Figure 9", render.html_to_text(self.html(s)))
        s["metrics"]["unresolved_markers"] = ["Figure ?? (p. 3)"]
        self.assertIn("Figure ?? (p. 3)", render.html_to_text(self.html(s)))

    def test_manual_mode_note(self):
        s = copy.deepcopy(self.state)
        s["meta"]["mode"] = "manual"
        self.assertIn("Created without validation", self.html(s))
        self.assertNotIn("Created without validation", self.page)

    def test_plain_text_preview_has_ids(self):
        text = render.render_text(render.build_view(self.state))
        self.assertIn("[D3-1]", text)
        self.assertNotIn("<", text)


if __name__ == "__main__":
    unittest.main()
