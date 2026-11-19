"""Registry (state.json): load/save atomically, step plan, apply answers, reset, auto-steps."""
from __future__ import annotations

import copy
import os
import tempfile
from pathlib import Path

from . import ops, refs
from .common import GROUPS, ROW_ORDER, SCHEMA_VERSION, dump_json, read_json
from .validate import norm_label

AREA_OF = {"data_sources": "data", "measures": "data", "design": "data", "subsets": "data"}
INVENTORY_AREAS = ["orientation", "loi_promises", "headline_claims", "data", "figure_map"]


# ---------------------------------------------------------------- files

def load(workdir) -> dict:
    return read_json(Path(workdir) / "state.json")


def save(workdir, state) -> None:
    """Write state.json atomically: temporary file in the same folder, then rename."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(workdir), prefix="state-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(dump_json(state))
        os.replace(tmp, workdir / "state.json")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def new_state(run_id, created, depth, inputs) -> dict:
    return {"schema_version": SCHEMA_VERSION,
            "meta": {"run_id": run_id, "skill_version": None, "model": None, "created": created,
                     "depth": depth, "mode": "pipeline", "inputs": inputs, "redact": []},
            "metrics": {}, "sections": [], "rows": {}, "synthesis": {}, "steps": {}, "warnings": []}


# ---------------------------------------------------------------- step plan

def _row_needs(codes):
    needs = {"headline_claims"}
    for code in codes:
        for dep in refs.row(code)["depends_on"]:
            needs.add(AREA_OF.get(dep, dep))
    needs -= {"metrics", "sections"}
    return needs


def plan(depth: str):
    """Ordered list of steps for a depth. Step numbers are list positions."""
    steps = [dict(kind="init", title="Extract text, metrics, section map", who="script",
                  needs=set(), provides={"init"})]

    def add(kind, title, needs, provides, who="model", **extra):
        steps.append(dict(kind=kind, title=title, who=who, needs=set(needs), provides=set(provides), **extra))

    if depth == "compact":
        add("inventory", "Inventory", [], INVENTORY_AREAS)
        for key, title, codes in GROUPS:
            add("group", f"Criteria {codes[0]}–{codes[-1]} \"{title}\"" if len(codes) > 1
                else f"Criterion {codes[0]} \"{title}\"", _row_needs(codes), ["rows"], rows=codes)
    else:
        add("orientation", "Orientation", [], ["orientation"])
        add("loi", "LOI promises", [], ["loi_promises"])
        add("claims", "Headline claims", [], ["headline_claims"])
        add("data", "Data and measures", ["headline_claims"], ["data"])
        add("figures", "Figure mapping", ["headline_claims"], ["figure_map"])
        for code in ROW_ORDER:
            add("row", f"Criterion {code} \"{refs.row(code)['title']}\"", _row_needs([code]), ["rows"], rows=[code])
    add("consistency", "Consistency check", ["rows"], ["consistency"], who="script + model")
    add("synthesis", "Synthesis", ["rows", "consistency"], ["synthesis"])
    add("sentence", "The paper in one sentence", ["orientation", "headline_claims"], ["sentence"])
    if depth != "compact":
        add("readback", "Read-back as the author", ["rows", "consistency", "synthesis", "sentence"], ["readback"])
    add("finish", "Validate and render", ["rows", "consistency", "synthesis", "sentence", "readback"],
        ["finish"], who="script")
    for no, s in enumerate(steps):
        s["no"] = no
    return steps


def get_plan(state):
    return plan(state["meta"].get("depth", "full"))


def status(state, no) -> str:
    return state["steps"].get(str(no), {}).get("status", "open")


def first_open(state):
    for s in get_plan(state):
        if status(state, s["no"]) == "open":
            return s
    return None


def dependents(state, no):
    """Step numbers that must be reset when step `no` is reset (including `no`)."""
    steps = get_plan(state)
    out = {no}
    changed = True
    while changed:
        changed = False
        for s in steps:
            if s["no"] in out:
                continue
            if any(o < s["no"] and steps[o]["provides"] & s["needs"] for o in out):
                out.add(s["no"])
                changed = True
    return sorted(out)


def mark(state, no, status_, **extra):
    entry = state["steps"].setdefault(str(no), {})
    entry["status"] = status_
    entry.update(extra)


# ---------------------------------------------------------------- apply answers

def _apply_orientation(state, ans):
    state["meta"]["model"] = ans["model"].strip()
    state["meta"]["redact"] = [r.strip() for r in ans["redact"] if r.strip()]
    state["orientation"] = {k: ans[k] for k in ("title", "layout", "paper_type", "primary_aim", "secondary_aims")}


def _apply_data(state, ans):
    state["data_sources"], state["measures"] = ans["data_sources"], ans["measures"]
    state["subsets"], state["design"] = ans.get("subsets") or [], ans["design"]


def _apply_figures(state, ans):
    fmap = [{"figure": norm_label(m["figure"]), "supports": m["supports"]} for m in ans["map"]]
    state["figure_map"] = fmap
    for claim in state.get("headline_claims", []):
        claim["figures"] = [m["figure"] for m in fmap if claim["id"] in m["supports"]]


def _snapshot(state, no):
    state["steps"].setdefault(str(no), {})["snapshot"] = {
        "rows": copy.deepcopy(state["rows"]), "synthesis": copy.deepcopy(state["synthesis"])}


def apply(state, step, ans, extra=None):
    """Write a validated answer into the registry."""
    kind = step["kind"]
    if kind == "orientation":
        _apply_orientation(state, ans)
    elif kind == "loi":
        state["loi_promises"] = ans["promises"]
    elif kind == "claims":
        state["headline_claims"] = ans["claims"]
    elif kind == "data":
        _apply_data(state, ans)
    elif kind == "figures":
        _apply_figures(state, ans)
    elif kind == "inventory":
        _apply_orientation(state, ans["orientation"])
        if ans.get("loi"):
            state["loi_promises"] = ans["loi"]["promises"]
        state["headline_claims"] = ans["claims"]["claims"]
        _apply_data(state, ans["data"])
        _apply_figures(state, ans["figures"])
    elif kind == "row":
        state["rows"][step["rows"][0]] = ans
    elif kind == "group":
        for code in step["rows"]:
            state["rows"][code] = ans["rows"][code]
    elif kind == "consistency":
        _snapshot(state, step["no"])
        new_rows, kept = extra
        state["rows"] = new_rows
        state["consistency"] = {"decisions": ans["decisions"], "kept": kept,
                                "score_changes": ans.get("score_changes") or [],
                                "calibration_justification": ans.get("calibration_justification")}
    elif kind == "synthesis":
        for ch in ans["other_changes"]:
            if not ch.get("raises"):
                ch["raises"] = sorted({ops.find_gap(state["rows"], g)[0] for g in ch["gaps"]},
                                      key=ROW_ORDER.index)
        state["synthesis"].update(critical=sorted(ans["critical"], key=lambda c: c["rank"]),
                                  strengths=ans["strengths"], other_changes=ans["other_changes"])
    elif kind == "sentence":
        if ans.get("cannot_be_stated"):
            state["synthesis"].update(one_sentence=ans["reason"].strip(), one_sentence_stated=False)
        else:
            state["synthesis"].update(one_sentence=ans["one_sentence"].strip(), one_sentence_stated=True)
    elif kind == "readback":
        _snapshot(state, step["no"])
        state["rows"], state["synthesis"] = extra
        state["synthesis"]["readback_changes"] = ans["changes"]


# ---------------------------------------------------------------- reset

def _reset_one(state, step):
    kind, no = step["kind"], step["no"]
    entry = state["steps"].get(str(no), {})
    snap = entry.get("snapshot")
    if kind in ("orientation", "inventory"):
        state.pop("orientation", None)
        state["meta"]["redact"], state["meta"]["model"] = [], None
    if kind in ("loi", "inventory"):
        state.pop("loi_promises", None)
    if kind in ("claims", "inventory"):
        state.pop("headline_claims", None)
    if kind in ("data", "inventory"):
        for k in ("data_sources", "measures", "subsets", "design"):
            state.pop(k, None)
    if kind in ("figures", "inventory"):
        state.pop("figure_map", None)
        for claim in state.get("headline_claims", []):
            claim.pop("figures", None)
    if kind in ("row", "group"):
        for code in step["rows"]:
            state["rows"].pop(code, None)
    if kind == "consistency":
        if snap:
            state["rows"] = {c: r for c, r in snap["rows"].items() if c in state["rows"]}
        state.pop("consistency", None)
    if kind == "synthesis":
        for k in ("critical", "strengths", "other_changes"):
            state["synthesis"].pop(k, None)
    if kind == "sentence":
        state["synthesis"].pop("one_sentence", None)
        state["synthesis"].pop("one_sentence_stated", None)
    if kind == "readback":
        if snap:
            state["rows"], state["synthesis"] = snap["rows"], snap["synthesis"]
        state["synthesis"].pop("readback_changes", None)
    if kind == "finish":
        state.pop("end_warnings", None)
    state["steps"][str(no)] = {"status": "open", "attempts": 0}
    state["warnings"] = [w for w in state.get("warnings", []) if w.get("step") != no]


def reset(state, no):
    """Reset step `no` and every step that depends on it. Returns the affected step numbers."""
    steps = get_plan(state)
    affected = [n for n in dependents(state, no) if status(state, n) != "open" or n == no]
    for n in sorted(affected, reverse=True):
        _reset_one(state, steps[n])
    return sorted(affected)


# ---------------------------------------------------------------- script-only steps

def advance(state):
    """Complete steps that need no model answer. Returns a list of notes for the user."""
    notes = []
    has_loi = state["meta"]["inputs"].get("loi", False)
    while True:
        step = first_open(state)
        if step is None:
            break
        kind, no = step["kind"], step["no"]
        if kind == "loi" and not has_loi:
            mark(state, no, "skipped", attempts=0)
            notes.append(f"Step {no} (LOI promises) skipped: no Letter of Inquiry was provided.")
        elif kind in ("row", "group") and step["rows"] == ["L1"] and not has_loi:
            feats = {k: "not_applicable" for k in refs.row("L1")["features"]}
            state["rows"]["L1"] = {"checks": [], "score": "NA", "na_reason": "No Letter of Inquiry provided.",
                                   "plus": [], "gaps": [], "features": feats, "minor": []}
            mark(state, no, "skipped", attempts=0)
            notes.append(f"Step {no} (criterion L1) set to N/A by the script: no Letter of Inquiry was provided.")
        elif kind == "consistency" and not ops.consistency_issues(state["rows"]) \
                and not ops.needs_calibration(state["rows"]):
            state["consistency"] = {"decisions": [], "kept": [], "score_changes": [],
                                    "calibration_justification": None}
            mark(state, no, "done", attempts=0, auto=True)
            notes.append(f"Step {no} (consistency check) completed by the script: no duplicates, "
                         "no misplaced gaps, no calibration warning.")
        else:
            break
    return notes
