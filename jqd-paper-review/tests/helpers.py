"""Shared helpers for the unit tests. Standard library only."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "scripts"))

import review  # noqa: E402
from jqd import refs  # noqa: E402
from jqd.common import ROW_ORDER  # noqa: E402

GAP_TEXTS = {
    "L1": ("The comparison with a second regional platform promised in the LOI is not reported and not mentioned.", 2),
    "A2": ("The results section explains a shift by an outside event in one sentence.", 3),
    "D1": ("The 40 prominent accounts were chosen because the authors knew them; no inclusion rule is given.", 2),
    "D2": ("The share of deleted posts is given, but not whether deletion differs between boards.", 2),
    "D3": ("Agreement between the incivility classifier and the coders is called high without any rate.", 3),
    "P1": ("The 1% cutoff for the most active accounts is not varied.", 3),
    "P3": ("Section 4.2 has no closing takeaway sentence.", 3),
    "P4": ("The pipeline is advertised in abstract and conclusion although it is not described.", 5),
    "P5": ("The caption of Figure 2 does not say what the vertical axis counts.", 3),
    "C1": ("The share of posts following a council decision has no comparison point.", 3),
    "C2": ("The prior estimate for national forums appears only once and is not in the reference list.", 2),
    "C5": ("No data and code availability statement is given.", 5),
}


def run_cli(*argv):
    """Run review.py in-process. Returns (exit code, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            code = review.main([str(a) for a in argv])
        except SystemExit as exc:  # argparse
            code = exc.code
    return code, buf.getvalue()


def example(kind):
    return copy.deepcopy(refs.example(kind))


def make_row(code, score=2, size="small", page=None, text=None, plus=True, **extra):
    """A valid answer for row `code` on the fixture manuscript."""
    row = refs.row(code)
    gap_text, gap_page = GAP_TEXTS.get(code, (f"One element that criterion {code} asks for is not reported.", 4))
    ans = {
        "checks": [f"Answer {i + 1}." for i in range(len(row["questions"]))],
        "score": score,
        "plus": ([{"id": f"{code}+1", "text": f"The manuscript meets a central point of criterion {code} on this page.",
                   "page": 2}] if plus else []),
        "gaps": ([] if score in (3, "NA") else [{
            "id": f"{code}-1", "text": text or gap_text, "page": page or gap_page,
            "fix": {"kind": "writing", "size": size, "text": "Add one sentence that reports the missing element."}}]),
        "features": {k: "partial" for k in row["features"]},
        "minor": [],
    }
    ans.update(extra)
    return ans


def fixture_rows():
    """Row answers for the fixture run: one routing case (K1) and one duplicate (K2)."""
    rows = {c: make_row(c) for c in ROW_ORDER}
    rows["A1"] = make_row("A1", score=3)
    rows["A1"]["plus"][0]["text"] = "The aim is stated on the first page as three descriptive quantities."
    rows["D1"]["plus"][0]["text"] = "Population, unit and non-coverage are explicit: accounts are not people, public posts only."
    rows["D3"] = make_row("D3", size="moderate")
    rows["D3"]["gaps"][0].update(affects=["H3"], quote="the classifier reached high agreement with the coders")
    rows["D3"]["gaps"][0]["fix"]["kind"] = "analysis"
    rows["P2"] = example("row")
    rows["C3"] = make_row("C3", text="The discussion extends the concentration finding from one platform to local forums in general.", page=4)
    rows["C3"]["gaps"].append({
        "id": "C3-2", "text": "The results state that the moderation change \"had an effect\" on tone.", "page": 4,
        "quote": "The moderation change had an effect on the tone", "topic": "causal_language",
        "fix": {"kind": "writing", "size": "small", "text": "Write that the share was higher after the change."}})
    rows["C4"] = make_row("C4", text="The discussion extends the concentration finding from a single platform to local forums in general.", page=4)
    rows["C4"]["gaps"].append({
        "id": "C4-2", "text": "The limitations name measurement error without saying which estimate it would move.", "page": 5,
        "fix": {"kind": "writing", "size": "small", "text": "Say whether classifier error would raise or lower the 7.4% share."}})
    rows["C5"]["minor"] = [{"category": "citations", "text": "One cited work is absent from the reference list", "page": 2}]
    return rows


class Workdir:
    """Temporary working directory with an initialised run on the fixture manuscript."""

    def __init__(self, depth="full", loi=True, manuscript="manuscript.txt"):
        self.tmp = Path(tempfile.mkdtemp(prefix="jqdtest-"))
        self.dir = self.tmp / "run"
        args = ["init", "--manuscript", FIX / manuscript, "--workdir", self.dir, "--depth", depth]
        if loi:
            args += ["--loi", FIX / "loi.txt"]
        self.init_code, self.init_out = run_cli(*args)

    def cli(self, *argv):
        return run_cli("--workdir", self.dir, *argv)

    def state(self):
        return json.loads((self.dir / "state.json").read_text(encoding="utf-8"))

    def submit(self, no, answer):
        (self.dir / "answers").mkdir(exist_ok=True)
        (self.dir / "answers" / f"{no}.json").write_text(json.dumps(answer, ensure_ascii=False), encoding="utf-8")
        return self.cli("submit", no)

    def run_inventory(self):
        """Steps 1–5 of the full depth."""
        for no, kind in ((1, "orientation"), (2, "loi"), (3, "claims"), (4, "data"), (5, "figures")):
            if kind == "loi" and not self.state()["meta"]["inputs"]["loi"]:
                continue
            code, out = self.submit(no, example(kind))
            assert code == 0, out

    def run_rows(self, rows=None):
        rows = rows or fixture_rows()
        for i, c in enumerate(ROW_ORDER):
            if c == "L1" and not self.state()["meta"]["inputs"]["loi"]:
                continue
            code, out = self.submit(6 + i, rows[c])
            assert code == 0, f"criterion {c}: {out}"

    def run_all(self):
        self.run_inventory()
        self.run_rows()
        for no, kind in ((22, "consistency"), (23, "synthesis"), (24, "sentence"), (25, "readback")):
            code, out = self.submit(no, example(kind))
            assert code == 0, f"{kind}: {out}"
        return self.cli("finish")

    def close(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
