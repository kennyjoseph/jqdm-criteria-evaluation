"""Reference files, examples and portability rules."""
import ast
import re
import sys
import unittest

from helpers import ROOT, example
from jqd import refs, schemas
from jqd.common import ROW_ORDER, read_text

STDLIB = set(sys.stdlib_module_names)


def sentences(text):
    text = re.sub(r"`[^`]*`|\"[^\"]*\"|\([^)]*\)", " x ", text)
    return [s for s in re.split(r"(?<=[.!?:;])\s+|\n", text) if s.strip()]


class ReferenceFiles(unittest.TestCase):
    def test_row_files_follow_the_common_structure(self):
        for code in ROW_ORDER:
            path = ROOT / "references" / "criteria" / f"{code}.md"
            self.assertLessEqual(len(read_text(path).splitlines()), 60, code)
            row = refs.row(code)
            self.assertTrue(3 <= len(row["questions"]) <= 6, code)
            self.assertTrue(3 <= len(row["features"]) <= 6, code)
            self.assertTrue(row["not_here"] and row["search_hints"], code)
            for part in ("## What this criterion checks", "## Check questions", "## Score decision"):
                self.assertIn(part, row["body"], code)
            for score in ("- 3:", "- 2:", "- 1:", "- 0:"):
                self.assertIn(score, row["body"], code)
            for pat in row["search_hints"]:
                re.compile(pat)

    def test_anchors_two_to_four_per_row_with_the_2_1_boundary(self):
        for code in ROW_ORDER:
            text = refs.anchors(code, include_drafts=True)
            scores = [int(x) for x in re.findall(rf"\*\*{code} · Score (\d)\.\*\*", text)]
            self.assertTrue(2 <= len(scores) <= 4, code)
            self.assertTrue({1, 2} <= set(scores), f"{code}: needs anchors at 2 and 1")
            self.assertEqual(text.count("*Justification:*"), len(scores))
            self.assertEqual(refs.anchors(code), text, "agreed anchors are shown to the model")

    def test_routing_table_assigns_each_topic_to_one_existing_row(self):
        table = refs.routing()
        for topic, entry in table.items():
            self.assertIn(entry["row"], ROW_ORDER, topic)
            for pat in entry.get("patterns", []):
                re.compile(pat)
        self.assertEqual(table["background_never_narrows"]["row"], "C2")
        self.assertEqual(table["tool_comparison_as_finding"]["row"], "P4")
        self.assertEqual(table["group_difference_without_variation"]["row"], "P2")
        self.assertEqual(table["causal_language"]["row"], "A2")
        self.assertEqual(table["text_figure_mismatch"]["row"], "C3")
        for code in ROW_ORDER:
            self.assertTrue(refs.topics_for(code), f"{code} has no topic")

    def test_step_instructions_are_short_and_complete(self):
        for kind, name in refs.STEP_FILES.items():
            secs = refs.step(kind)
            for part in ("Task", "Rules", "Fields"):
                self.assertIn(part, secs, name)
            self.assertLessEqual(len(read_text(ROOT / "references" / "steps" / name).splitlines()), 60, name)
            self.assertEqual((len(secs["Task"].splitlines()), secs["Task"].count(". ")), (1, 0), name)

    def test_instruction_sentences_stay_under_25_words(self):
        files = list((ROOT / "references" / "steps").glob("*.md")) + list((ROOT / "references" / "criteria").glob("*.md"))
        long = []
        for path in files:
            _, body = refs.parse_frontmatter(read_text(path))
            for s in sentences(body):
                if len(s.split()) > 25:
                    long.append(f"{path.name}: {s[:90]}")
        self.assertEqual(long, [])

    def test_examples_match_their_schemas(self):
        for kind in ("orientation", "loi", "claims", "data", "figures", "row", "consistency", "synthesis",
                     "sentence", "readback"):
            self.assertEqual(schemas.check(example(kind), schemas.BY_KIND[kind]), [], kind)

    def test_scale_and_journal(self):
        self.assertIn("sloppy", refs.scale()["loaded_words"])
        self.assertEqual(len(refs.scale()["short"].splitlines()), 8)
        self.assertEqual(sorted(refs.journal()["layouts"]), sorted(schemas.LAYOUTS))
        self.assertEqual(refs.journal()["norms"]["full_words"], [6000, 14000])


class Portability(unittest.TestCase):
    def test_skill_md_frontmatter_and_length(self):
        text = read_text(ROOT / "SKILL.md")
        self.assertLessEqual(len(text.splitlines()), 120)
        self.assertLessEqual(len(text), 6500, "about 1,500 tokens")
        head = text.split("---")[1].strip().splitlines()
        self.assertEqual([l.split(":")[0] for l in head], ["name", "description"])
        self.assertEqual(head[0], "name: jqd-paper-review")
        desc = head[1].split(":", 1)[1].strip()
        self.assertLessEqual(len(desc), 500)
        self.assertNotIn(": ", desc, "a colon-space would break plain YAML")
        self.assertIn("review.py --version", text)
        self.assertIn("references/manual-mode.md", text)
        self.assertLessEqual(len(read_text(ROOT / "AGENTS.md").strip().splitlines()), 5)

    def test_scripts_use_only_the_standard_library(self):
        files = [ROOT / "scripts" / "review.py"] + sorted((ROOT / "scripts" / "jqd").glob("*.py"))
        for path in files:
            tree = ast.parse(read_text(path))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module]
                for name in names:
                    top = name.split(".")[0]
                    self.assertTrue(top in STDLIB or top in ("jqd", "pypdf"), f"{path.name}: {name}")
                    self.assertNotIn(top, ("urllib", "http", "socket", "requests", "ftplib"), path.name)

    def test_pypdf_is_vendored_with_its_licence(self):
        vendor = ROOT / "scripts" / "jqd" / "vendor"
        self.assertTrue((vendor / "pypdf" / "__init__.py").is_file())
        self.assertTrue((vendor / "LICENSE-pypdf.txt").is_file())

    def test_template_placeholders_are_all_filled(self):
        from jqd import render
        names = set(re.findall(r"\{\{(\w+)\}\}", read_text(ROOT / "assets" / "template.html")))
        view = render.build_view({"meta": {}, "rows": {}})
        self.assertNotIn("{{", render.render_html(view))
        self.assertEqual(len(names), 15)


if __name__ == "__main__":
    unittest.main()


class ManualModeFiles(unittest.TestCase):
    """Manual mode writes the evaluation by hand; its fixed wording must match the HTML report."""

    def test_manual_template_uses_report_wording(self):
        import re as _re
        from jqd import render
        text = read_text(ROOT / "references" / "manual-mode.md")
        self.assertIn(render.NOTE, text)
        template = read_text(ROOT / "assets" / "template.html")
        lead = _re.search(r'<p class="loc">(Address each item.*?)</p>', template).group(1)
        self.assertIn(lead, text)
        for title in ("## The paper in one sentence", "## Strengths", "## Response required at submission",
                      "## Size", "## Scores by criterion", "## Other changes that would strengthen the paper",
                      "## Smaller fixes"):
            self.assertIn(title, text)

    def test_single_file_bundle_is_up_to_date(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("bundle", ROOT / "tests" / "tools" / "build_manual_bundle.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not mod.OUT.exists():
            self.skipTest("bundle not present (skill folder installed on its own)")
        self.assertEqual(mod.OUT.read_text(encoding="utf-8"), mod.build(),
                         "run python tests/tools/build_manual_bundle.py")
        self.assertNotIn("search_hints", mod.OUT.read_text(encoding="utf-8"))
