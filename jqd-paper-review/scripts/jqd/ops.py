"""Pure transformations of the registry used by the consistency and read-back steps."""
from __future__ import annotations

import copy
import re
from difflib import SequenceMatcher

from . import refs
from .common import ROW_ORDER


def all_gaps(rows):
    """Yield (row_code, gap) in fixed row order."""
    for code in ROW_ORDER:
        for gap in (rows.get(code) or {}).get("gaps", []):
            yield code, gap


def all_plus(rows):
    for code in ROW_ORDER:
        for p in (rows.get(code) or {}).get("plus", []):
            yield code, p


def find_gap(rows, gap_id):
    for code, gap in all_gaps(rows):
        if gap["id"] == gap_id:
            return code, gap
    return None, None


def find_plus(rows, plus_id):
    for code, p in all_plus(rows):
        if p["id"] == plus_id:
            return code, p
    return None, None


def low_share(rows):
    """(number of rows scored ≤ 1, number of scored rows)."""
    scored = [r["score"] for r in rows.values() if r.get("score") in (0, 1, 2, 3)]
    return sum(1 for s in scored if s <= 1), len(scored)


def needs_calibration(rows) -> bool:
    low, n = low_share(rows)
    return n > 0 and low > n / 3   # every 0 or 1 requires an author response


def _sim(a: str, b: str) -> float:
    def n(s):
        return " ".join(re.findall(r"\w+", s.lower()))
    return SequenceMatcher(None, n(a), n(b), autojunk=False).ratio()


def routed_row(gap):
    """Row the routing table assigns to this gap, with the topic. (None, None) if undecided."""
    table = refs.routing()
    topic = gap.get("topic")
    if topic in table:
        return table[topic]["row"], topic
    for name, entry in table.items():
        for pat in entry.get("patterns", []):
            if re.search(pat, gap["text"], re.I):
                return entry["row"], name
    return None, None


def _same_problem(ga, gb) -> bool:
    """Two gaps in different criteria that probably describe one problem: similar text on the same page,
    the same quote, or fairly similar text bearing on the same headline claim."""
    same_doc = ga.get("doc", "manuscript") == gb.get("doc", "manuscript")
    sim = _sim(ga["text"], gb["text"])
    if same_doc and ga["page"] == gb["page"] and sim >= 0.6:
        return True
    if same_doc and ga.get("quote") and ga.get("quote") == gb.get("quote"):
        return True
    shared = bool(set(ga.get("affects") or []) & set(gb.get("affects") or []))
    if same_doc and shared and ga["page"] == gb["page"] and _word_overlap(ga["text"], gb["text"]) >= 0.15:
        return True
    return shared and sim >= 0.45


_STOP = set("the a an of and or in on to for is are not no with as by from at its it this that be than "
            "their which".split())


def _word_overlap(a: str, b: str) -> float:
    """Jaccard overlap of content words (length > 2, minus stop words)."""
    A = {w for w in re.findall(r"[a-z0-9]+", a.lower()) if w not in _STOP and len(w) > 2}
    B = {w for w in re.findall(r"[a-z0-9]+", b.lower()) if w not in _STOP and len(w) > 2}
    return len(A & B) / max(1, len(A | B))


def consistency_issues(rows):
    """Possible misroutings (V12) and duplicates (V13), in a fixed order, with IDs K1…"""
    issues = []
    for code, gap in all_gaps(rows):
        target, topic = routed_row(gap)
        if target and target != code:
            issues.append({"type": "route", "gap": gap["id"], "row": code, "target": target,
                           "topic": topic, "key": f"route|{gap['id']}"})
    gaps = list(all_gaps(rows))
    for i, (ra, ga) in enumerate(gaps):
        for rb, gb in gaps[i + 1:]:
            if ra != rb and _same_problem(ga, gb):
                issues.append({"type": "dup", "gaps": [ga["id"], gb["id"]], "rows": [ra, rb],
                               "page": ga["page"], "key": f"dup|{ga['id']}|{gb['id']}"})
    for n, issue in enumerate(issues, 1):
        issue["id"] = f"K{n}"
    return issues


def _next_gap_id(row, code):
    used = {int(g["id"].split("-")[1]) for g in row.get("gaps", [])}
    n = 1
    while n in used:
        n += 1
    return f"{code}-{n}"


def apply_consistency(rows, issues, answer):
    """Return (new_rows, kept_keys, touched_rows). Does not validate."""
    rows = copy.deepcopy(rows)
    by_id = {i["id"]: i for i in issues}
    kept, touched = [], set()
    for d in answer.get("decisions", []):
        issue = by_id.get(d["issue"])
        if not issue:
            continue
        if d["action"] == "keep":
            kept.append(issue["key"])
        elif d["action"] == "move" and issue["type"] == "route":
            src, gap = find_gap(rows, issue["gap"])
            if gap is None or issue["target"] not in rows:
                continue
            rows[src]["gaps"].remove(gap)
            gap = dict(gap, id=_next_gap_id(rows[issue["target"]], issue["target"]), topic=issue["topic"])
            rows[issue["target"]].setdefault("gaps", []).append(gap)
            touched |= {src, issue["target"]}
        elif d["action"] == "merge" and issue["type"] == "dup":
            drop = [g for g in issue["gaps"] if g != d.get("keep_gap")]
            for gid in drop[:1]:
                src, gap = find_gap(rows, gid)
                if gap is not None:
                    rows[src]["gaps"].remove(gap)
                    touched.add(src)
    for ch in answer.get("score_changes") or []:
        if ch["row"] in rows:
            rows[ch["row"]]["score"] = ch["score"]
            touched.add(ch["row"])
    return rows, kept, touched


def apply_readback(rows, synthesis, answer):
    """Return (new_rows, new_synthesis, touched_rows, problems as (index, message, fix))."""
    rows, syn = copy.deepcopy(rows), copy.deepcopy(synthesis)
    touched, bad = set(), []
    for i, ch in enumerate(answer.get("changes", [])):
        op, target, value = ch["op"], ch.get("target"), ch.get("value")
        if op == "edit_sentence":
            syn["one_sentence"], syn["one_sentence_stated"] = value, True
        elif op == "set_score":
            if target in rows:
                rows[target]["score"] = value
                touched.add(target)
            else:
                bad.append((i, f"\"{target}\" is not a criterion code.", "Use a criterion code such as P2 as target."))
        elif op == "edit_why":
            entry = next((c for c in syn.get("critical", []) if c["gap"] == target), None)
            if entry:
                entry["why"] = value
            else:
                bad.append((i, f"\"{target}\" is not a critical issue.",
                            "Use the gap ID of a critical issue as target."))
        else:
            code, item = find_gap(rows, target)
            if item is None and op == "edit_text":
                code, item = find_plus(rows, target)
            if item is None:
                bad.append((i, f"No entry with the ID \"{target}\" exists.",
                            "Use an ID from the preview, e.g. D3-1 for a gap or D3+1 for a strength."))
                continue
            if op == "edit_text":
                item["text"] = value
            elif op == "edit_fix_text":
                item["fix"]["text"] = value
            elif op == "set_fix_size":
                item["fix"]["size"] = value
            touched.add(code)
    return rows, syn, touched, bad
