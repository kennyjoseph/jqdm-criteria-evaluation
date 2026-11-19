"""End-to-end runs through review.py on the fixture manuscript."""
import json
import re
import shutil
import unittest

from helpers import ROOT, Workdir, example, fixture_rows, make_row, run_cli
from jqd import state as st
from jqd.common import GROUPS, ROW_ORDER


class FullRun(unittest.TestCase):
    def setUp(self):
        self.w = Workdir()
        self.addCleanup(self.w.close)

    def test_complete_run_with_loi(self):
        self.assertEqual(self.w.init_code, 0)
        self.assertRegex(self.w.dir.name, r"^run$")
        code, out = self.w.run_all()
        self.assertEqual(code, 0, out)
        s = self.w.state()
        files = sorted(p.name for p in (self.w.dir / "out").iterdir())
        self.assertEqual(files, [f"criteria-evaluation-{s['meta']['run_id']}.html"])
        self.assertTrue(all(v["status"] == "done" for v in s["steps"].values()))
        self.assertEqual(s["headline_claims"][2]["figures"], ["Tab 2", "Fig 3"])
        self.assertEqual(len(s["rows"]), 16)
        self.assertIn("CHAT SUMMARY", out)
        self.assertIn("1 critical issue", out)
        code, out = self.w.cli("finish")           # second finish does not overwrite
        self.assertEqual(code, 0)
        self.assertEqual(len(list((self.w.dir / "out").iterdir())), 2)
        self.assertRegex(out, r"criteria-evaluation-[0-9a-f]{6}-2\.html")

    def test_every_output_starts_with_status_and_ends_with_next_command(self):
        outputs = [self.w.init_out]
        outputs.append(self.w.cli("next")[1])
        outputs.append(self.w.cli("status")[1])
        outputs.append(self.w.cli("show", "--pages", "1")[1])
        outputs.append(self.w.cli("show", "--pages", "77")[1])
        outputs.append(self.w.cli("find", "council")[1])
        outputs.append(self.w.submit(1, {"title": 3})[1])
        outputs.append(self.w.submit(1, example("orientation"))[1])
        outputs.append(self.w.cli("redo", 1)[1])
        outputs.append(self.w.cli("finish")[1])
        outputs.append(run_cli("--version")[1])
        for text in outputs:
            lines = text.strip().split("\n")
            self.assertIn(lines[0], ("OK", "ERROR", "WARNING"), text[:200])
            self.assertTrue(lines[-1].startswith("NEXT COMMAND"), text[-300:])

    def test_run_id_and_paths_do_not_come_from_the_file_name(self):
        s = self.w.state()
        self.assertRegex(s["meta"]["run_id"], r"^[0-9a-f]{6}$")
        other = Workdir()
        self.addCleanup(other.close)
        self.assertNotEqual(other.state()["meta"]["run_id"], s["meta"]["run_id"])

    def test_errors_are_instructions(self):
        code, out = self.w.submit(1, dict(example("orientation"), layout="classic"))
        self.assertEqual(code, 1)
        self.assertRegex(out, r"ERROR 1 of 1 · .*1\.json · layout · V01")
        self.assertIn("FIX: Use exactly one of: \"standard\"", out)
        self.assertEqual(self.w.state()["steps"]["1"]["attempts"], 1)
        (self.w.dir / "answers" / "1.json").write_text("{not json", encoding="utf-8")
        code, out = self.w.cli("submit", 1)
        self.assertIn("not valid JSON", out)
        fenced = "```json\n" + json.dumps(example("orientation")) + "\n```"
        (self.w.dir / "answers" / "1.json").write_text(fenced, encoding="utf-8")
        code, out = self.w.cli("submit", 1)
        self.assertEqual(code, 0, out)

    def test_steps_must_be_done_in_order(self):
        code, out = self.w.submit(3, example("claims"))
        self.assertEqual(code, 1)
        self.assertIn("not the next open step", out)
        self.w.submit(1, example("orientation"))
        code, out = self.w.submit(1, example("orientation"))
        self.assertIn("already done", out)
        code, out = self.w.cli("finish")
        self.assertEqual(code, 1)
        self.assertIn("still open", out)

    def test_simplified_answer_is_offered_after_three_failures(self):
        self.w.run_inventory()
        bad = make_row("L1")
        bad["gaps"][0]["quote"] = "words that are not in the manuscript at all"
        for attempt in (1, 2, 3):
            code, out = self.w.submit(6, bad)
            self.assertEqual(code, 1)
            self.assertEqual("SIMPLIFY" in out, attempt == 3, out)
        self.assertIn('"id": "L1+1"', out)
        stats = self.w.state()["steps"]["6"]["stats"]
        self.assertEqual((stats["quotes_not_found"], stats["submit_errors"]), (3, 3))

    def test_resume_and_redo_with_dependencies(self):
        self.w.run_inventory()
        self.w.run_rows()
        code, out = self.w.cli("next")              # a fresh process resumes at the first open step
        self.assertIn("STEP 22 of 26 · Consistency check", out)
        for no, kind in ((22, "consistency"), (23, "synthesis"), (24, "sentence")):
            self.assertEqual(self.w.submit(no, example(kind))[0], 0)
        before = self.w.state()
        self.assertEqual([g["id"] for g in before["rows"]["A2"]["gaps"]], ["A2-1", "A2-2"])
        code, out = self.w.cli("redo", 13)          # row P2
        s = self.w.state()
        open_steps = [int(n) for n, v in s["steps"].items() if v["status"] == "open"]
        self.assertEqual(sorted(open_steps), [13, 22, 23])
        self.assertNotIn("P2", s["rows"])
        self.assertEqual([g["id"] for g in s["rows"]["A2"]["gaps"]], ["A2-1"], "consistency moves are undone")
        self.assertEqual([g["id"] for g in s["rows"]["C3"]["gaps"]], ["C3-1", "C3-2"])
        self.assertIn("one_sentence", s["synthesis"], "step 24 does not depend on a row")
        self.assertIn("STEP 13 of 26", self.w.cli("next")[1])
        self.assertEqual(self.w.submit(13, example("row"))[0], 0)
        code, out = self.w.cli("redo", 3)           # headline claims: everything built on them reopens
        s = self.w.state()
        self.assertEqual(s["steps"]["1"]["status"], "done")
        self.assertEqual(s["steps"]["2"]["status"], "done")
        self.assertTrue(all(s["steps"][str(n)]["status"] == "open" for n in range(3, 25)))
        self.assertEqual(s["rows"], {})

    def test_task_blocks_stay_within_the_context_budget(self):
        self.w.run_inventory()
        rows = fixture_rows()
        sizes = {}
        for i, c in enumerate(ROW_ORDER):
            block = self.w.cli("next")[1]
            # Absolute paths depend on where the folder is installed; count them as a short placeholder.
            sizes[c] = len(block.replace(str(ROOT), "<skill>").replace(str(self.w.tmp), "<tmp>"))
            for part in ("TASK:", "CONTEXT:", "RULES", "SCALE:", "EVIDENCE", "READ", "ANSWER FORMAT:",
                         "EXAMPLE", "NEXT COMMAND:"):
                self.assertIn(part, block, f"{c}: {part}")
            self.assertLess(block.index("RULES"), block.index("EVIDENCE"))
            self.assertIn("ANCHORS", block, f"{c}: agreed anchors are shown")
            self.assertLess(block.index("ANCHORS"), block.index("EVIDENCE"))
            self.assertEqual(self.w.submit(6 + i, rows[c])[0], 0)
        self.assertLess(max(sizes.values()), 12500, sizes)   # ≈ 3,000 tokens

    def test_show_is_limited_to_8000_characters(self):
        shutil.copy(self.w.dir / "text" / "manuscript.txt", self.w.dir / "text" / "appendix.txt")
        big = "⟨p.1⟩\n" + ("A sentence with several words in it. " * 800)
        (self.w.dir / "text" / "appendix.txt").write_text(big, encoding="utf-8")
        code, out = self.w.cli("show", "--doc", "appendix", "--pages", "1")
        self.assertLess(len(out), 8600)
        self.assertIn("part 1 of 4", out)
        self.assertIn("--part 2", out)
        code, out = self.w.cli("show", "--doc", "appendix", "--pages", "1", "--part", "5")
        self.assertTrue(out.startswith("ERROR") and "Part 5 does not exist" in out, out[:200])
        code, out = self.w.cli("show", "--pages", "1", "--part", "2")
        self.assertTrue(out.startswith("ERROR"), "a short text has no part 2")

    def test_find_says_how_the_pattern_was_read(self):
        self.assertIn("regular expression, case-insensitive", self.w.cli("find", "council")[1])
        self.assertIn("searched as plain text", self.w.cli("find", "share (")[1])

    def test_answer_format_states_limits_and_criterion_specific_examples(self):
        self.w.run_inventory()
        out = self.w.cli("next")[1]
        self.assertIn("LIMITS", out)
        self.assertIn("gaps[].text: at most 180 characters", out)
        self.assertIn("plus and gaps together: at most 3", out)


class RunWithoutLoi(unittest.TestCase):
    def test_l1_is_na_and_loi_step_is_skipped(self):
        w = Workdir(loi=False)
        self.addCleanup(w.close)
        self.assertEqual(w.submit(1, example("orientation"))[0], 0)
        self.assertEqual(w.state()["steps"]["2"]["status"], "skipped")
        for no, kind in ((3, "claims"), (4, "data"), (5, "figures")):
            code, out = w.submit(no, example(kind))
            self.assertEqual(code, 0, out)
        self.assertIn("criterion L1) set to N/A", out)
        s = w.state()
        self.assertEqual(s["rows"]["L1"]["score"], "NA")
        self.assertIn("STEP 7 of 26", w.cli("next")[1])
        rows = fixture_rows()
        for i, c in enumerate(ROW_ORDER[1:], 7):
            self.assertEqual(w.submit(i, rows[c])[0], 0)
        for no, kind in ((22, "consistency"), (23, "synthesis"), (24, "sentence"), (25, "readback")):
            code, out = w.submit(no, example(kind))
            self.assertEqual(code, 0, out)
        code, out = w.cli("finish")
        self.assertEqual(code, 0, out)
        page = next((w.dir / "out").glob("*.html")).read_text(encoding="utf-8")
        self.assertIn("No Letter of Inquiry was provided; the accepted question was inferred", page)
        self.assertIn("No Letter of Inquiry provided.", page)

    def test_consistency_step_is_automatic_when_nothing_is_found(self):
        w = Workdir(loi=False)
        self.addCleanup(w.close)
        w.run_inventory()
        rows = fixture_rows()
        rows["C3"]["gaps"] = rows["C3"]["gaps"][:1]
        rows["C4"]["gaps"] = rows["C4"]["gaps"][1:]
        w.run_rows(rows)
        s = w.state()
        self.assertEqual(s["steps"]["22"], {"status": "done", "attempts": 0, "auto": True})
        self.assertIn("STEP 23 of 26", w.cli("next")[1])


class CompactRun(unittest.TestCase):
    def test_compact_depth_uses_eleven_steps_and_the_same_rules(self):
        w = Workdir(depth="compact")
        self.addCleanup(w.close)
        self.assertEqual(len(st.plan("compact")), 11)
        self.assertEqual(len(st.plan("full")), 27)
        block = w.cli("next")[1]
        self.assertIn("STEP 1 of 10 · Inventory", block)
        inventory = {"orientation": example("orientation"), "loi": example("loi"), "claims": example("claims"),
                     "data": example("data"), "figures": example("figures")}
        bad = json.loads(json.dumps(inventory))
        bad["claims"]["claims"][0]["quote"] = "a quote that does not exist anywhere"
        code, out = w.submit(1, bad)
        self.assertIn("claims.claims[0].quote · V09", out)
        self.assertEqual(w.submit(1, inventory)[0], 0)
        rows = fixture_rows()
        for no, (_, _, codes) in enumerate(GROUPS, 2):
            block = w.cli("next")[1]
            self.assertIn(f"=== CRITERION {codes[0]} ===", block)
            if codes[0] == "D1":
                code, out = w.submit(no, {"rows": {c: rows[c] for c in codes[:2]}})
                self.assertIn("The answer for criterion D3 is missing", out)
            code, out = w.submit(no, {"rows": {c: rows[c] for c in codes}})
            self.assertEqual(code, 0, out)
        for no, kind in ((7, "consistency"), (8, "synthesis"), (9, "sentence")):
            code, out = w.submit(no, example(kind))
            self.assertEqual(code, 0, out)
        code, out = w.cli("finish")
        self.assertEqual(code, 0, out)
        self.assertNotIn("readback", [s["kind"] for s in st.plan("compact")])


class ManualMode(unittest.TestCase):
    def setUp(self):
        self.w = Workdir()
        self.addCleanup(self.w.close)
        self.assertEqual(self.w.run_all()[0], 0)
        s = self.w.state()
        self.registry = {k: s[k] for k in ("schema_version", "orientation", "loi_promises", "headline_claims",
                                           "data_sources", "measures", "design", "rows", "consistency", "synthesis")}
        self.registry["meta"] = {"run_id": "abc123", "mode": "manual", "model": "small-model", "created": "2026-11-12",
                                 "inputs": {"manuscript": True, "loi": True, "appendix": False}, "redact": []}
        self.path = self.w.tmp / "manual" / "state.json"
        self.path.parent.mkdir()

    def write(self):
        self.path.write_text(json.dumps(self.registry), encoding="utf-8")

    def test_render_from_registry_without_manuscript(self):
        self.write()
        code, out = run_cli("render", "--from", self.path)
        self.assertEqual(code, 0, out)
        page = (self.path.parent / "out" / "criteria-evaluation-abc123.html").read_text(encoding="utf-8")
        self.assertIn("Created without validation of quotes", page)
        self.assertIn("Not counted", page)
        self.assertIn("model: small-model", page)

    def test_render_from_registry_checks_quotes_when_the_manuscript_is_given(self):
        self.write()
        from helpers import FIX
        code, out = run_cli("render", "--from", self.path, "--manuscript", FIX / "manuscript.txt")
        self.assertEqual(code, 0, out)
        page = (self.path.parent / "out" / "criteria-evaluation-abc123.html").read_text(encoding="utf-8")
        self.assertNotIn("Created without validation", page)
        self.assertIn("~800 words main text", page)
        self.registry["rows"]["D3"]["gaps"][0]["quote"] = "an invented quote about validation"
        self.write()
        code, out = run_cli("render", "--from", self.path, "--manuscript", FIX / "manuscript.txt")
        self.assertEqual(code, 1)
        self.assertIn("rows.D3.gaps[0].quote · V09", out)

    def test_render_from_registry_applies_the_rules(self):
        self.registry["rows"]["D1"]["gaps"] = []
        self.registry["synthesis"]["critical"][0]["gap"] = "P2-1"
        self.registry["rows"]["P2"]["gaps"][0]["affects"] = []
        del self.registry["rows"]["C5"]
        self.write()
        code, out = run_cli("render", "--from", self.path)
        self.assertEqual(code, 1)
        self.assertIn("V03", out)
        self.registry["rows"]["C5"] = make_row("C5")
        self.registry["rows"]["D1"] = make_row("D1")
        self.write()
        code, out = run_cli("render", "--from", self.path)
        self.assertEqual(code, 1)
        self.assertIn("V15", out)
        self.assertFalse((self.path.parent / "out").exists(), "nothing is rendered while errors remain")


if __name__ == "__main__":
    unittest.main()
