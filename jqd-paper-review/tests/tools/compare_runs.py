#!/usr/bin/env python3
"""Consistency metrics over several runs of the same manuscript (development tool, not used by the skill).

Usage: python tests/tools/compare_runs.py RUN_DIR [RUN_DIR …] [--reference ref.json]
Each RUN_DIR is a working directory with a state.json. The optional reference file has the form
{"rows": {"D3": [1, 2], "P2": [2, 2], …}} with the expected score range per row.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROWS = ["L1", "A1", "A2", "D1", "D2", "D3", "P1", "P2", "P3", "P4", "P5", "C1", "C2", "C3", "C4", "C5"]


def load(path):
    return json.loads((Path(path) / "state.json").read_text(encoding="utf-8"))


def num(score):
    return -1 if score == "NA" else score


def critical_keys(state):
    keys = set()
    for c in state.get("synthesis", {}).get("critical", []):
        row = c["gap"].split("-")[0]
        gap = next((g for g in state["rows"].get(row, {}).get("gaps", []) if g["id"] == c["gap"]), None)
        if gap:
            keys.add((row, gap["page"]))
    return keys


def quote_stats(state):
    kept = sum(1 for r in state.get("rows", {}).values() for g in r.get("gaps", []) if g.get("quote"))
    kept += len(state.get("headline_claims", []))
    missed = sum(s.get("stats", {}).get("quotes_not_found", 0) for s in state.get("steps", {}).values())
    return kept, missed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--reference")
    args = ap.parse_args(argv)
    states = [load(r) for r in args.runs]
    n = len(states)
    done = [s for s in states if s.get("steps") and all(v["status"] != "open" for v in s["steps"].values())]
    print(f"Runs: {n} · completed: {len(done)} ({100 * len(done) / n:.0f}%)")
    if len(done) < 2:
        print("At least two completed runs are needed for the stability metrics.")
        return 0
    per_row = {r: [num(s["rows"][r]["score"]) for s in done if r in s["rows"]] for r in ROWS}
    stable = sum(1 for v in per_row.values() if v and max(v) - min(v) <= 1)
    need = math.ceil(0.8 * len(done))
    exact = sum(1 for v in per_row.values() if v and Counter(v).most_common(1)[0][1] >= need)
    print(f"Run-to-run score stability (range ≤ 1): {100 * stable / len(ROWS):.0f}% of criteria   (target ≥ 95%)")
    print(f"Exact agreement (mode in ≥ {need} of {len(done)} runs): {100 * exact / len(ROWS):.0f}% of criteria   (target ≥ 70%)")
    overlaps = []
    for a, b in itertools.combinations(done, 2):
        ka, kb = critical_keys(a), critical_keys(b)
        overlaps.append(1.0 if not ka and not kb else len(ka & kb) / len(ka | kb))
    print(f"Stability of critical issues (same criterion and page, mean pairwise overlap): "
          f"{100 * sum(overlaps) / len(overlaps):.0f}%   (target ≥ 70%)")
    kept = sum(quote_stats(s)[0] for s in done)
    missed = sum(quote_stats(s)[1] for s in done)
    if kept + missed:
        print(f"Evidence fidelity (quotes found at first submit, approximate): "
              f"{100 * kept / (kept + missed):.0f}%   (target ≥ 95%)")
    errors = Counter()
    for s in done:
        for no, step in s["steps"].items():
            errors[int(no)] += step.get("stats", {}).get("submit_errors", 0)
    worst = [f"step {no}: {c}" for no, c in errors.most_common(5) if c]
    print("Submit errors per step (highest): " + ("; ".join(worst) or "none"))
    if args.reference:
        ref = json.loads(Path(args.reference).read_text(encoding="utf-8"))["rows"]
        inside = total = 0
        for row, (lo, hi) in ref.items():
            for v in per_row.get(row, []):
                total += 1
                inside += lo <= v <= hi
        print(f"Agreement with reference: {100 * inside / max(total, 1):.0f}% of criterion scores in range   (target ≥ 80%)")
    print("Row scores per run: " + " ".join(f"{r}={'/'.join(str(x) if x >= 0 else 'NA' for x in v)}" for r, v in per_row.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
