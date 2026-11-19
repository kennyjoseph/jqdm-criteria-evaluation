"""Every validation rule V01–V24 with at least one passing and one failing case."""
import copy
import unittest

from helpers import Workdir, example, fixture_rows, make_row
from jqd import ops, render, validate
from jqd.common import ROW_ORDER, errors_of, warnings_of
from jqd.tasks import Run


def rules(problems, level=None):
    return sorted({p.rule for p in problems if level is None or p.level == level})


class RuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = Workdir()
        cls.w.run_inventory()
        run = Run(cls.w.dir)
        cls.state, cls.ctx = run.state, validate.Ctx(run.docs())

    @classmethod
    def tearDownClass(cls):
        cls.w.close()

    def row(self, code, ans, state=None):
        return validate.check_row(state or self.state, code, copy.deepcopy(ans), self.ctx)

    def full_state(self, rows=None):
        s = copy.deepcopy(self.state)
        s["rows"] = rows or fixture_rows()
        return s

    # V01 ------------------------------------------------------------
    def test_v01_schema(self):
        self.assertEqual(self.row("P2", example("row")), [])
        bad = example("row")
        del bad["score"]
        bad["gaps"][0]["fix"]["size"] = "huge"
        bad["plus"][0]["text"] = "x" * 230
        bad["verdict"] = "fine"
        probs = self.row("P2", bad)
        self.assertEqual(rules(probs), ["V01"])
        self.assertEqual(sorted(p.path for p in probs), ["gaps[0].fix.size", "plus[0].text", "score", "verdict"])
        self.assertTrue(all(p.fix for p in probs), "every error names its fix")

    def test_v01_features_and_check_answers_must_match_the_row_file(self):
        bad = example("row")
        bad["features"].pop("n_for_subgroups")
        bad["features"]["made_up"] = "present"
        bad["checks"] = bad["checks"][:2]
        self.assertEqual(sorted(p.path for p in self.row("P2", bad)),
                         ["checks", "features.made_up", "features.n_for_subgroups"])

    # V02 ------------------------------------------------------------
    def test_v02_ids_and_references(self):
        bad = example("row")
        bad["plus"].append(dict(bad["plus"][0]))
        bad["gaps"][0]["affects"] = ["H5"]
        bad["gaps"][0]["id"] = "D3-1"
        probs = [p for p in self.row("P2", bad) if p.rule != "V08"]
        self.assertEqual(rules(probs), ["V02"])
        self.assertEqual(len(probs), 3)
        claims = example("claims")
        claims["claims"][1]["id"] = "H3"
        self.assertIn("V02", rules(validate.check_claims(self.state, claims, self.ctx)))
        self.assertEqual(errors_of(validate.check_claims(self.state, example("claims"), self.ctx)), [])

    # V03 – V08 ------------------------------------------------------
    def test_v03_score_below_three_needs_a_gap(self):
        ans = make_row("D1")
        self.assertEqual(self.row("D1", ans), [])
        ans["gaps"] = []
        self.assertEqual(rules(self.row("D1", ans)), ["V03"])

    def test_v04_na_needs_a_reason(self):
        ans = make_row("D3", score="NA", na_reason="The paper uses plain counts only; no measure needs validation.")
        self.assertEqual(self.row("D3", ans), [])
        ans["na_reason"] = None
        self.assertEqual(rules(self.row("D3", ans)), ["V04"])

    def test_v05_present_feature_needs_a_strength(self):
        ans = make_row("D1", plus=False)
        ans["features"]["population_and_unit_explicit"] = "present"
        self.assertEqual(rules(self.row("D1", ans)), ["V05"])
        self.assertEqual(self.row("D1", dict(ans, plus=make_row("D1")["plus"])), [])

    def test_v06_score_three_allows_only_small_gaps(self):
        ans = make_row("D1", size="moderate")
        ans["score"] = 3
        self.assertEqual(rules(self.row("D1", ans)), ["V06"])
        ans["gaps"][0]["fix"]["size"] = "small"
        self.assertEqual(self.row("D1", ans), [])

    def test_v07_score_zero_with_present_feature_warns(self):
        ans = make_row("D1", score=0)
        self.assertEqual(self.row("D1", ans), [])
        ans["features"]["scale_in_one_place"] = "present"
        probs = self.row("D1", ans)
        self.assertEqual((rules(probs, "warning"), errors_of(probs)), (["V07"], []))

    def test_v08_number_of_points(self):
        def with_gaps(n):
            ans = make_row("D1")
            ans["gaps"] = [dict(ans["gaps"][0], id=f"D1-{i + 1}", text=f"Specific gap number {i + 1} in the data section.")
                           for i in range(n)]
            return ans
        self.assertEqual(self.row("D1", with_gaps(1)), [])
        self.assertEqual(self.row("D1", with_gaps(2)), [], "3 points in total are allowed without a warning")
        self.assertEqual(rules(self.row("D1", with_gaps(3)), "error"), ["V08"])
        empty = make_row("D1", score=3, plus=False)
        self.assertEqual(rules(self.row("D1", empty), "error"), ["V08"])

    # V23 ------------------------------------------------------------
    def test_v23_a_one_needs_a_headline_gap_or_two_larger_gaps(self):
        ans = make_row("D1", score=1)
        ans["gaps"][0]["affects"] = []
        self.assertEqual(rules(self.row("D1", ans)), ["V23"])
        ans["gaps"][0]["affects"] = ["H1"]
        self.assertEqual(rules(self.row("D1", ans)), [])
        ans["gaps"][0]["affects"] = []
        ans["plus"] = []
        ans["gaps"] = [dict(ans["gaps"][0], id=f"D1-{i + 1}", text=f"Specific gap number {i + 1} in the data section.",
                            fix=dict(ans["gaps"][0]["fix"], size="moderate")) for i in range(2)]
        self.assertEqual(rules(self.row("D1", ans)), [])

    def test_v23_p4_one_needs_a_larger_cut_not_a_headline_claim(self):
        ans = make_row("P4", score=1)
        ans["gaps"][0]["affects"] = []
        ans["gaps"][0]["fix"] = dict(ans["gaps"][0]["fix"], size="small")
        self.assertEqual(rules(self.row("P4", ans)), ["V23"])
        ans["gaps"][0]["fix"] = dict(ans["gaps"][0]["fix"], size="moderate")
        self.assertEqual(rules(self.row("P4", ans)), [])

    # V25 ------------------------------------------------------------
    def test_v25_p1_zero_needs_a_headline_claim(self):
        ans = make_row("P1", score=0, plus=False)
        ans["features"] = {k: "absent" for k in ans["features"]}
        ans["gaps"][0]["affects"] = []
        self.assertIn("V25", rules(self.row("P1", ans)))
        ans["gaps"][0]["affects"] = ["H1"]
        self.assertNotIn("V25", rules(self.row("P1", ans)))

    # V09 ------------------------------------------------------------
    def test_v09_quotes_are_checked_against_the_page(self):
        ans = example("row")
        ans["gaps"][0]["quote"] = "95 % confidence intervals are shown"
        probs = self.row("P2", ans)
        self.assertEqual(rules(probs, "error"), ["V09"])
        self.assertIn("show --pages 3-5", probs[0].fix)
        moved = example("row")
        moved["gaps"][0]["page"] = 1
        probs = validate.check_row(self.state, "P2", moved, self.ctx)
        self.assertEqual((rules(probs, "warning"), errors_of(probs)), (["V09"], []))
        self.assertEqual(moved["gaps"][0]["page"], 4, "the page is corrected in place")
        ans["gaps"][0]["page"] = 99
        self.assertIn("V01", rules(self.row("P2", ans)))

    # V24 ------------------------------------------------------------
    def test_v24_reported_cross_references_must_occur_in_the_manuscript(self):
        ans = make_row("P5")
        ans["minor"] = [{"category": "cross_references", "text": "Figure 9 (p. 4) and Section 8 (p. 2) do not exist."}]
        self.assertEqual(rules(self.row("P5", ans)), [])
        ans["minor"][0]["text"] = "Table 7 (p. 3) does not exist."
        probs = self.row("P5", ans)
        self.assertEqual(rules(probs, "error"), ["V24"])
        self.assertIn("Table 7", probs[0].msg)
        ans["minor"][0]["category"] = "figures"
        self.assertEqual(rules(self.row("P5", ans)), [])

    # V10 ------------------------------------------------------------
    def test_v10_l1_is_na_exactly_without_loi(self):
        self.assertEqual(self.row("L1", make_row("L1")), [])
        na = make_row("L1", score="NA", na_reason="No Letter of Inquiry provided.")
        self.assertEqual(rules(self.row("L1", na)), ["V10"])
        no_loi = copy.deepcopy(self.state)
        no_loi["meta"]["inputs"]["loi"] = False
        self.assertEqual(self.row("L1", na, no_loi), [])
        self.assertEqual(rules(self.row("L1", make_row("L1"), no_loi)), ["V10"])

    # V11 ------------------------------------------------------------
    def test_v11_causal_design_expects_a2_zero(self):
        causal = copy.deepcopy(self.state)
        causal["design"]["kind"] = "diff_in_diff"
        self.assertEqual(self.row("A2", make_row("A2"), self.state), [])
        self.assertEqual(rules(self.row("A2", make_row("A2"), causal), "error"), ["V11"])
        justified = make_row("A2", design_justification="The comparison is reported as a description of two groups only.")
        probs = self.row("A2", justified, causal)
        self.assertEqual((rules(probs, "warning"), errors_of(probs)), (["V11"], []))
        self.assertEqual(self.row("A2", make_row("A2", score=0), causal), [])

    def test_v11_descriptive_matching_and_designs_from_the_loi_are_not_penalized(self):
        s = copy.deepcopy(self.state)
        s["design"]["kind"] = "matched_comparison"
        self.assertEqual(self.row("A2", make_row("A2"), s), [])
        s["design"].update(kind="matched_control", loi_promise="P1")
        self.assertEqual(self.row("A2", make_row("A2"), s), [])
        data = {k: s.get(k, []) for k in ("data_sources", "measures", "subsets")} | {"design": s["design"]}
        self.assertNotIn("V02", rules(validate.check_data(s, copy.deepcopy(data), self.ctx)))
        data["design"] = dict(s["design"], loi_promise="P9")
        self.assertIn("V02", rules(validate.check_data(s, data, self.ctx)))

    # V12, V13 -------------------------------------------------------
    def test_v12_routing(self):
        s = self.full_state()
        routes = [i for i in ops.consistency_issues(s["rows"]) if i["type"] == "route"]
        self.assertEqual([(i["gap"], i["target"]) for i in routes], [("C3-2", "A2")])
        self.assertEqual([r for r in rules(self.row("C3", s["rows"]["C3"]), "warning") if r != "V08"], ["V12"])
        s["synthesis"] = {"one_sentence": "x " * 10, **example("synthesis")}
        self.assertIn("V12", rules(validate.end_problems(s), "warning"))
        s["consistency"] = {"kept": ["route|C3-2", "dup|C3-1|C4-1"]}
        self.assertEqual([r for r in rules(validate.end_problems(s)) if r in ("V12", "V13")], [])
        untagged = fixture_rows()
        untagged["C3"]["gaps"][1].pop("topic")
        untagged["C3"]["gaps"][1]["text"] = "The results use causal wording for the moderation change."
        self.assertEqual([i["gap"] for i in ops.consistency_issues(untagged) if i["type"] == "route"], ["C3-2"])

    def test_v13_duplicates(self):
        rows = fixture_rows()
        dups = [i for i in ops.consistency_issues(rows) if i["type"] == "dup"]
        self.assertEqual([i["gaps"] for i in dups], [["C3-1", "C4-1"]])
        rows["C4"]["gaps"][0]["page"] = 5
        self.assertEqual([i for i in ops.consistency_issues(rows) if i["type"] == "dup"], [])

    # V14 ------------------------------------------------------------
    def test_v14_calibration_justification(self):
        rows = {c: make_row(c, score=1) for c in ROW_ORDER}
        for i, c in enumerate(ROW_ORDER):
            rows[c]["gaps"][0]["page"] = 1 + i % 5
            rows[c]["gaps"][0]["text"] = f"Gap {c}: " + "abcdefghijklmnopqrstuvwxyz"[i:i + 9] * 3
        s = self.full_state(rows)
        probs, _ = validate.check_consistency(s, {"decisions": []})
        self.assertEqual(rules(probs, "error"), ["V14"])
        probs, extra = validate.check_consistency(s, {"decisions": [], "calibration_justification":
                                                      "The manuscript omits validation, robustness and limitations throughout."})
        self.assertEqual(errors_of(probs), [])
        s["synthesis"] = {"one_sentence": "x " * 10, "critical": [], "strengths": ["A1+1", "D1+1"], "other_changes": []}
        self.assertIn("V14", rules(validate.end_problems(s), "error"))

    def test_consistency_decisions_are_applied_and_rows_rechecked(self):
        s = self.full_state()
        ans = example("consistency")
        probs, (rows, kept) = validate.check_consistency(s, ans)
        self.assertEqual(errors_of(probs), [])
        self.assertEqual([g["id"] for g in rows["A2"]["gaps"]], ["A2-1", "A2-2"])
        self.assertEqual([g["id"] for g in rows["C3"]["gaps"]], ["C3-1"])
        self.assertEqual([g["id"] for g in rows["C4"]["gaps"]], ["C4-2"])
        self.assertEqual(rows["C3"]["score"], 3)
        s2 = self.full_state()
        s2["rows"]["C4"]["gaps"] = s2["rows"]["C4"]["gaps"][:1]
        probs, _ = validate.check_consistency(s2, ans)
        self.assertEqual(rules(probs, "error"), ["V03"], "C4 is left without a gap after the merge")

    # V15 – V18 ------------------------------------------------------
    def test_v15_critical_issues(self):
        s = self.full_state()
        self.assertEqual(validate.check_synthesis(s, example("synthesis")), [])
        syn = dict(example("synthesis"), other_changes=[])
        syn["critical"] = [{"gap": "P2-1", "rank": 1, "why": "It matters for the third headline claim."}]
        self.assertEqual(validate.check_synthesis(s, syn), [], "a small fix behind a headline claim may be critical")
        s["rows"]["P2"]["gaps"][0]["affects"] = []
        syn["critical"][0]["rank"] = 2
        self.assertEqual(rules(validate.check_synthesis(s, syn)), ["V15"])
        self.assertEqual(len(validate.check_synthesis(s, syn)), 2, "small fix without a headline claim, and wrong rank")
        syn["critical"] = [{"gap": "X9-1", "rank": 1, "why": "It matters for the third headline claim."}]
        self.assertEqual(rules(validate.check_synthesis(s, syn)), ["V15"])

    def test_v16_strengths(self):
        s = self.full_state()
        syn = example("synthesis")
        syn["strengths"] = ["A1+1"]
        self.assertEqual(rules(validate.check_synthesis(s, syn)), ["V16"])
        syn["strengths"] = ["A1+1", "Z1+1"]
        self.assertEqual(rules(validate.check_synthesis(s, syn)), ["V16"])

    def test_v17_other_changes(self):
        s = self.full_state()
        syn = example("synthesis")
        syn["other_changes"] = [{"gaps": [g], "text": "Change this specific thing."}
                                for g in ("P2-1", "D1-1", "D2-1", "P1-1", "P3-1")]
        self.assertEqual(rules(validate.check_synthesis(s, syn)), ["V17"])
        syn["other_changes"] = [{"gaps": ["D3-1"], "text": "Report the agreement rates."}]
        self.assertEqual(rules(validate.check_synthesis(s, syn)), ["V17"], "gap is already critical")

    def test_v18_one_sentence(self):
        self.assertEqual(validate.check_sentence(self.state, example("sentence")), [])
        self.assertEqual(rules(validate.check_sentence(self.state, {"one_sentence": "word " * 46})), ["V01"])
        self.assertEqual(rules(validate.check_sentence(self.state, {"cannot_be_stated": True})), ["V18"])
        self.assertEqual(validate.check_sentence(self.state, {
            "cannot_be_stated": True, "reason": "No primary descriptive aim can be identified in the manuscript."}), [])
        s = self.full_state()
        s["synthesis"] = dict(example("synthesis"))
        self.assertIn("V18", rules(validate.end_problems(s)))
        s["synthesis"]["one_sentence"] = "word " * 46
        self.assertIn("V18", rules(validate.end_problems(s)))

    # V19 – V21 ------------------------------------------------------
    def test_v19_anonymity(self):
        ans = make_row("D1")
        ans["gaps"][0]["text"] = "Jordan Example selected the 40 prominent accounts without a stated rule."
        self.assertEqual(rules(self.row("D1", ans)), ["V19"])
        ans["gaps"][0]["text"] = "Write to jordan.example@nowhere.example for the inclusion rule of the subset."
        self.assertEqual(rules(self.row("D1", ans)), ["V19"])
        ans["gaps"][0]["text"] = "The file manuscript.txt gives no inclusion rule for the subset."
        self.assertEqual(rules(self.row("D1", ans)), ["V19"])
        s = self.full_state()
        s["synthesis"] = {"one_sentence": "A sentence about the paper and its data.", **example("synthesis")}
        text = "Scorecard text that mentions Riley Sample by name."
        self.assertIn("V19", rules(validate.end_problems(s, rendered_text=text), "error"))
        self.assertNotIn("V19", rules(validate.end_problems(s, rendered_text="Scorecard text about the manuscript.")))

    def test_v19_affiliations_with_places_do_not_block_the_country(self):
        from jqd import anon
        hits = anon.find_identifiers("Exposure to untrustworthy news in Germany",
                                     ["Hertie School, Berlin, Germany", "Goethe University Frankfurt, Germany"])
        self.assertEqual(hits, [])

    def test_v19_surnames_are_matched_on_their_own(self):
        from jqd import anon
        self.assertEqual(anon.surname("Jennifer Golbeck"), "Golbeck")
        self.assertEqual(anon.surname("JENNIFER GOLBECK1"), "Golbeck")
        self.assertEqual(anon.surname("Benjamin Ooghe-Tabanou"), "Ooghe-Tabanou")
        self.assertEqual(anon.surname("Ludwig van Beethoven"), "Beethoven")
        self.assertIsNone(anon.surname("University of Maryland"))
        self.assertIsNone(anon.surname("Golbeck"))
        red = ["Jennifer Golbeck", "Andrea Long"]
        self.assertEqual(anon.find_identifiers("As Golbeck (2024) shows, the archive is complete.", red), ["Golbeck"])
        self.assertEqual(anon.find_identifiers("JENNIFER GOLBECK wrote it.", red), ["Jennifer Golbeck"])
        self.assertEqual(anon.find_identifiers("A long series of posts.", red), [])
        self.assertEqual(anon.find_identifiers("Long et al. (2020) differ.", red), ["Long"])

    def test_v20_decision_words(self):
        for bad in ("We recommend acceptance after these changes are made.",
                    "This needs a major revision before it is ready.",
                    "The paper should be rejected in its current form.",
                    "The overall score of the paper is low."):
            ans = make_row("D1")
            ans["gaps"][0]["text"] = bad
            self.assertEqual(rules(self.row("D1", ans)), ["V20"], bad)
        for fine in ("The paper rejects the null hypothesis of equal shares without a test.",
                     "The accepted Letter of Inquiry names a second platform that is not analysed."):
            ans = make_row("D1")
            ans["gaps"][0]["text"] = fine
            self.assertEqual(self.row("D1", ans), [], fine)
        self.assertEqual(validate.decision_words(render.NOTE), [])

    def test_v21_loaded_words_warn_at_the_end(self):
        s = self.full_state()
        s["synthesis"] = {"one_sentence": "A sentence about the paper and its data.", **example("synthesis")}
        probs = validate.end_problems(s, rendered_text="The validation is sloppy and the paper fails to report it.")
        self.assertEqual([p.level for p in probs if p.rule == "V21"], ["warning", "warning"])
        self.assertNotIn("V21", rules(validate.end_problems(s, rendered_text="The validation rate is not reported.")))

    # V22 ------------------------------------------------------------
    def test_v22_at_least_one_firm_claim(self):
        claims = example("claims")
        self.assertEqual(validate.check_claims(self.state, claims, self.ctx), [])
        for c in claims["claims"]:
            c["status"] = "tentative"
        probs = validate.check_claims(self.state, claims, self.ctx)
        self.assertEqual((rules(probs, "warning"), errors_of(probs)), (["V22"], []))

    # other step answers ---------------------------------------------
    def test_examples_of_all_inventory_steps_are_valid(self):
        self.assertEqual(validate.check_orientation(self.state, example("orientation"), self.ctx), [])
        self.assertEqual(validate.check_loi(self.state, example("loi"), self.ctx), [])
        self.assertEqual(validate.check_data(self.state, example("data"), self.ctx), [])
        self.assertEqual(validate.check_figures(self.state, example("figures"), self.ctx), [])

    def test_figure_map_must_cover_all_main_items(self):
        fig = example("figures")
        fig["map"] = fig["map"][:-1] + [{"figure": "Figure 7", "supports": []}]
        probs = validate.check_figures(self.state, fig, self.ctx)
        self.assertEqual(sorted(p.path for p in probs), ["map", "map[4].figure"])

    def test_readback_changes_are_validated_against_the_rules(self):
        s = self.full_state()
        s["synthesis"] = {"one_sentence": "A sentence about the paper and its data.", **example("synthesis")}
        probs, (rows, syn) = validate.check_readback(s, example("readback"))
        self.assertEqual(probs, [])
        self.assertIn("no agreement or error rate", rows["D3"]["gaps"][0]["text"])
        probs, _ = validate.check_readback(s, {"changes": [
            {"op": "set_fix_size", "target": "D3-1", "value": "small", "reason": "It is a small fix."}]})
        self.assertEqual(rules(probs), [], "a small fix behind a headline claim may stay critical")
        s["rows"]["D3"]["gaps"][0]["affects"] = []
        probs, _ = validate.check_readback(s, {"changes": [
            {"op": "set_fix_size", "target": "D3-1", "value": "small", "reason": "It is a small fix."}]})
        self.assertEqual(rules(probs), ["V15"], "a critical issue with a small fix must bear on a headline claim")
        probs, _ = validate.check_readback(s, {"changes": [
            {"op": "set_score", "target": "D1", "value": 3, "reason": "The criterion is met."},
            {"op": "edit_text", "target": "Q1-1", "value": "A new and specific text for it.", "reason": "Clearer."}]})
        self.assertEqual(rules(probs), ["V02"])


if __name__ == "__main__":
    unittest.main()
