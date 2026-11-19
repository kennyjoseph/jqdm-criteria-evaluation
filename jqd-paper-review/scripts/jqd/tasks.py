"""Task blocks: what `review.py next` prints for each step. Everything a step needs is included."""
from __future__ import annotations

import copy
import json
import os
import re
import sys
from pathlib import Path

from . import anon, metrics as metrics_mod, ops, refs, render, schemas, state as st
from .common import ROW_ORDER, clip, page_sentences
from .extract import find_abstract, line_zone_fn, load_marked, section_span

MAX_SHOW = 8000   # some agent harnesses truncate tool output near 10k characters
READ_SECTIONS = {
    "L1": [], "A1": ["introduction"], "A2": ["results", "discussion"],
    "D1": ["data", "sample", "method"], "D2": ["data", "sample", "method"],
    "D3": ["measure", "method", "data"], "P1": ["robust", "method", "results"],
    "P2": ["results", "findings"], "P3": ["introduction", "results"], "P4": [],
    "P5": [], "C1": ["results", "discussion", "conclusion"],
    "C2": ["background", "related", "literature", "introduction"],
    "C3": ["discussion", "conclusion"], "C4": ["limitation", "discussion"], "C5": [],
}


class Run:
    """One working directory: state plus lazily loaded texts."""

    def __init__(self, workdir, state=None):
        self.workdir = Path(workdir)
        self.state = state if state is not None else st.load(workdir)
        self._docs = {}

    def pages(self, doc="manuscript"):
        if doc not in self._docs:
            self._docs[doc] = load_marked(self.workdir / "text" / f"{doc}.txt")
        return self._docs[doc]

    def docs(self):
        return {d: self.pages(d) for d in ("manuscript", "loi", "appendix")}

    def cmd(self, rest: str) -> str:
        script = Path(__file__).resolve().parent.parent / "review.py"
        wd = Path(self.workdir).resolve()   # absolute: agent shells often reset the current directory
        exe = "python3" if Path(sys.executable).name.lower().startswith("python3") else "python"
        return f'{exe} "{script}" --workdir "{wd}" {rest}'

    def answer_path(self, no) -> Path:
        return self.workdir / "answers" / f"{no}.json"


# ---------------------------------------------------------------- pieces

def show_path(path) -> str:
    """Absolute path: agent shells often reset the current directory between commands."""
    return str(Path(path).resolve())


def _fmt_example(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1)


def row_example(code: str) -> dict:
    """The stored row example (row P2), reshaped to the IDs, features and questions of `code`."""
    ex = copy.deepcopy(refs.example("row"))
    if code == "P2":
        return ex
    row = refs.row(code)
    ex["checks"] = [f"<short answer to check question {i + 1}>" for i in range(len(row["questions"]))]
    for kind, sign in (("plus", "+"), ("gaps", "-")):
        for i, item in enumerate(ex[kind], 1):
            item["id"] = f"{code}{sign}{i}"
    # Text of the stored example belongs to P2; other criteria get placeholders, so its content is not copied.
    for item in ex["plus"]:
        item["text"] = f"<what this manuscript does well on {code}, specific, ≤ 180 characters>"
    for gap in ex["gaps"]:
        gap["text"] = f"<what is missing or unclear for {code}, specific to this manuscript, ≤ 180 characters>"
        gap["quote"] = "<optional: ≤ 15 words copied verbatim from that page>"
        gap["affects"] = ["<IDs of headline claims or LOI promises this gap bears on; [] if none>"]
        gap["fix"]["text"] = "<what the authors could do, ≤ 200 characters>"
    topics = refs.topics_for(code)
    for gap in ex["gaps"]:
        if topics:
            gap["topic"] = topics[0]
        else:
            gap.pop("topic", None)
    ex["features"] = {k: "present | partial | absent | not_applicable" for k in row["features"]}
    return ex


def answer_format(run, step, fields: str, example, note="") -> list:
    shown = show_path(run.answer_path(step["no"]))
    out = [f"ANSWER FORMAT: Write one JSON object to the file {shown} (UTF-8, no other text).",
           "FIELDS:", fields.strip()]
    schema = schemas.BY_KIND.get(step.get("kind"))
    if schema:
        out += ["LIMITS (longer texts are rejected):", "  " + "; ".join(schemas.limits(schema))]
    if note:
        out.append(note)
    out += ["EXAMPLE (shows shape and style; its content comes from another manuscript):",
            _fmt_example(example),
            "NEXT COMMAND: " + run.cmd(f"submit {step['no']}")]
    return out


def claims_lines(state):
    out = []
    for c in state.get("headline_claims", []):
        figs = f" · {', '.join(c['figures'])}" if c.get("figures") else ""
        out.append(f"  {c['id']} [{c['status']}] p.{c['page']} \"{c['short']}\": {c['text']}{figs}")
    return out or ["  (none recorded)"]


def context_lines(run, deps) -> list:
    s, out = run.state, []
    deps = list(deps)
    if "headline_claims" not in deps:
        deps.insert(0, "headline_claims")
    for dep in deps:
        if dep == "headline_claims":
            out += ["Headline claims:"] + claims_lines(s)
        elif dep == "orientation" and s.get("orientation"):
            o = s["orientation"]
            out.append(f"Primary aim (p.{o['primary_aim']['page']}): {o['primary_aim']['text']}")
            for a in o["secondary_aims"]:
                out.append(f"Secondary aim [{a['billing']}] (p.{a['page']}): {a['text']}")
            out.append(f"Layout: {o['layout']} · paper type: {o['paper_type']}")
        elif dep == "loi_promises":
            out.append("LOI promises:")
            out += [f"  {p['id']} [{p['type']}] {p['text']}" for p in s.get("loi_promises", [])] or ["  (none)"]
        elif dep == "data_sources":
            out.append("Data sources:")
            out += [f"  {d['id']} {d['kind']} p.{d['page']}" + (f" ({d['n']})" if d.get("n") else "")
                    + f": {d['text']}" for d in s.get("data_sources", [])] or ["  (none recorded)"]
            out += [f"  Subset p.{d['page']}" + (f" ({d['n']})" if d.get("n") else "") + f": {d['text']}"
                    for d in s.get("subsets", [])]
        elif dep == "measures":
            out.append("Measures:")
            out += [f"  {m['id']} {m['kind']} p.{m['page']} → {', '.join(m['supports']) or 'no headline claim'}: "
                    f"{m['text']}" for m in s.get("measures", [])] or ["  (none recorded)"]
        elif dep == "design" and s.get("design"):
            d = s["design"]
            out.append(f"Analysis design: {d['kind']} (p.{d['page']}): {d['text']}")
            if d.get("loi_promise"):
                out.append(f"  The LOI described this design ({d['loi_promise']}); the editors accepted it at the LOI stage.")
        elif dep == "figure_map":
            items = (s.get("metrics") or {}).get("items", [])
            fmap = {m["figure"]: m["supports"] for m in s.get("figure_map", [])}
            out.append("Figures and tables:")
            out += [f"  {x['label']} p.{x['page']} → {', '.join(fmap.get(x['label'], [])) or '–'}: "
                    f"{clip(x['caption'], 150)}" for x in items] or ["  (none found)"]
        elif dep == "metrics":
            m = s.get("metrics") or {}
            line, norms = metrics_mod.size_summary(m, (s.get("orientation") or {}).get("paper_type", "full"))
            out += [f"Size: {line}", f"  {norms}"]
            if m.get("abstract_words"):
                out.append(f"  Abstract: {m['abstract_words']} words")
            for key, label in (("broken_crossrefs", "Possible broken cross-references (regex candidates; many are "
                                "false positives, so check each with `find` before reporting it)"),
                               ("unresolved_markers", "References shown as \"??\" (already reported; do not repeat)")):
                vals = m.get(key) or []
                out.append(f"  {label}: " + ("; ".join(vals[:8]) + (f"; +{len(vals) - 8} more" if len(vals) > 8 else "")
                                              if vals else "none"))
        elif dep == "sections":
            heads = main_headings(s) or s.get("sections", [])
            out.append("Headings: " + " | ".join(f"p.{h['page']} {clip(h['title'], 50)}" for h in heads[:40]))
    return out


def evidence(run, patterns, max_hits=9, width=210) -> list:
    """Sentences matching the search patterns, spread over the document, with page."""
    pages = run.pages("manuscript") or []
    zone_of = line_zone_fn(run.state.get("sections", []))
    per_pattern, total = [], 0
    for pat in patterns:
        try:
            rx = re.compile(pat, re.I)
        except re.error:
            continue
        hits, seen = [], set()
        for pno, page in enumerate(pages, 1):
            for line_no, sent in page_sentences(page):
                m = rx.search(sent)
                if not m or sent in seen or zone_of(pno, line_no) == "references":
                    continue
                seen.add(sent)
                lo = max(0, m.start() - width // 2)
                snippet = ("…" if lo else "") + sent[lo:lo + width] + ("…" if lo + width < len(sent) else "")
                hits.append((pno, snippet))
        total += len(hits)
        per_pattern.append(hits)
    quota = max(1, max_hits // max(1, len([h for h in per_pattern if h])))
    chosen = []
    for hits in per_pattern:
        if len(hits) <= quota:
            chosen += hits
        else:
            step = (len(hits) - 1) / (quota - 1) if quota > 1 else 0
            chosen += [hits[round(i * step)] for i in range(quota)]
    chosen = sorted(set(chosen))[:max_hits]
    out = [f"  p.{p} · {t}" for p, t in chosen]
    if not out:
        return ["  (no hits for this criterion's search patterns; use `find` with your own words)"]
    if total > len(chosen):
        out.append(f"  ({len(chosen)} of {total} hits shown. More: " + run.cmd('find "<word or pattern>"') + ")")
    return out


def main_headings(state) -> list:
    """Headings of the main text. Unnumbered headings detected only by layout ("weak") are included
    when fewer than three strong headings were found there, as in papers without numbered sections."""
    heads = [h for h in state.get("sections", []) if h["zone"] == "main"]
    strong = [h for h in heads if not h["weak"]]
    return strong if len(strong) >= 3 else heads


def last_text_pages(run) -> str:
    """Page range of the last pages before the reference list (the conclusion, usually)."""
    n = len(run.pages("manuscript") or [""])
    ref = next((h["page"] for h in run.state.get("sections", []) if h["zone"] == "references" and not h["weak"]), None)
    end = ref or n
    return f"{max(1, end - 2)}-{end}"


def read_suggestions(run, keywords, extra=()) -> list:
    out, seen = [], set()
    strong = main_headings(run.state) + [h for h in run.state.get("sections", [])
                                         if h["zone"] == "appendix" and not h["weak"]]
    for kw in keywords:
        for h in strong:
            if kw in h["title"].lower() and h["title"] not in seen:
                seen.add(h["title"])
                out.append("  " + run.cmd(f'show --section "{h["title"]}"'))
                break
    out += ["  " + run.cmd(x) for x in extra]
    out.append("  " + run.cmd('find "<word or pattern>"') + "   (full-text search; the pattern is a regular expression)")
    return out[:6]


def row_parts(run, code) -> list:
    """RULES, ANCHORS and EVIDENCE of one row."""
    row = refs.row(code)
    out = [f"RULES for criterion {code} \"{row['title']}\":", row["body"],
           "Where this score decision says 1, the general rule for a 1 still applies; otherwise score 2.",
           "FEATURES (set a status for each):"]
    out += [f"  {k}: {v}" for k, v in row["features"].items()]
    topics = refs.topics_for(code)
    out.append("TOPICS of this criterion (optional field \"topic\"): " + (", ".join(topics) or "none"))
    out.append("NOT HERE (these belong to other criteria):")
    out += [f"  {x}" for x in row["not_here"]]
    if refs.anchors(code):
        out += [f"ANCHORS for criterion {code} (calibration examples from other papers):", refs.anchors(code)]
    out += ["EVIDENCE (passages preselected by the script; page markers as in `show`):"]
    out += evidence(run, row["search_hints"])
    return out


def _row_read(run, code):
    s = run.state
    extra = []
    n = len(run.pages("manuscript") or [])
    if code == "L1":
        extra.append("show --doc loi --pages 1-3")
    if code == "P5":
        figs = [m["figure"] for m in s.get("figure_map", []) if m["supports"]][:3]
        extra += [f"show --{'table' if f.startswith('Tab') else 'figure'} {f.split()[1]}" for f in figs]
    if code in ("C5", "P4") and n:
        extra.append(f"show --pages {max(1, n - 1)}-{n}")
    if code in ("P3", "C3", "A1"):
        extra.append("show --pages 1-2")
    return read_suggestions(run, READ_SECTIONS[code], extra)


# ---------------------------------------------------------------- blocks per kind

def _orientation_input(run) -> list:
    s = run.state
    pages = run.pages("manuscript") or [""]
    m = s.get("metrics") or {}
    cand = anon.detect_candidates(pages)
    out = ["INPUT:",
           f"Key figures: {m.get('pages')} pages · {m.get('words_main')} words main text · "
           f"{m.get('figures')} figures · {m.get('tables')} tables · abstract "
           f"{m.get('abstract_words') or 'not found'} words",
           "Title page (⟨p.1⟩, first 2,500 characters):", pages[0][:2500].rstrip()]
    found = find_abstract(pages, s.get("sections", []))
    if found:
        tail = " ".join(found[1].split()[-8:])
        if " ".join(tail.split()) not in " ".join(pages[0][:2500].split()):
            out += [f"Abstract as detected by the script (from p.{found[0]}; it continues past the excerpt above):",
                    found[1][:3600].rstrip()]
    heads = s.get("sections", [])
    out.append("Headings found by the script: " + (" | ".join(f"p.{h['page']} {clip(h['title'], 50)}"
                                                              for h in heads[:45]) or "none"))
    out.append("Figures and tables found by the script:")
    out += [f"  {x['label']} p.{x['page']}: {clip(x['caption'], 120)}" for x in m.get("items", [])] or ["  none"]
    out.append("Institution lines detected on the title page (candidates for \"redact\"): "
               + ("; ".join(cand["institutions"]) or "none"))
    return out


def _layouts() -> list:
    return ["LAYOUTS:"] + [f"  {k}: {v}" for k, v in refs.journal()["layouts"].items()]


def _loi_input(run) -> list:
    pages = run.pages("loi") or []
    text = "".join(f"⟨p.{i}⟩\n{p}\n" for i, p in enumerate(pages, 1))
    out = ["INPUT (Letter of Inquiry):", text[:9000].rstrip()]
    if len(text) > 9000:
        out.append("(LOI text cut after 9,000 characters. Read on with: " + run.cmd("show --doc loi --pages 1-9 --part 2") + ")")
    return out


def _claims_input(run) -> list:
    s = run.state
    pages = run.pages("manuscript") or [""]
    found = find_abstract(pages, s.get("sections", []))
    if found:
        out = [f"INPUT (abstract, from p.{found[0]}):", found[1][:3600].rstrip()]
    else:
        out = ["INPUT (no abstract found; first page shown instead — "
               "read on with `show --pages 1-2` if the abstract is not here):", ("⟨p.1⟩\n" + pages[0])[:2800].rstrip()]
    if s.get("orientation"):
        a = s["orientation"]["primary_aim"]
        out.append(f"Primary aim recorded in step 1 (p.{a['page']}): {a['text']}")
    out.append("READ (run these before you answer):")
    out += read_suggestions(run, ["introduction", "conclusion", "discussion"],
                            [] if any("conclu" in h["title"].lower() or "discuss" in h["title"].lower()
                                      for h in main_headings(s)) else [f"show --pages {last_text_pages(run)}"])
    return out


def _data_input(run) -> list:
    deps = ["headline_claims"] + (["loi_promises"] if run.state.get("loi_promises") else [])
    out = ["CONTEXT:"] + context_lines(run, deps)
    out += ["EVIDENCE (where design words occur):"] + evidence(run, refs.row("A2")["search_hints"][1:2], 6)
    out += ["READ (run these before you answer):"]
    out += read_suggestions(run, ["data", "sample", "method", "measure", "material"])
    return out


def _figures_input(run) -> list:
    items = (run.state.get("metrics") or {}).get("items", [])
    out = ["INPUT (figures and tables found by the script; ★ = main text, must be listed):"]
    out += [f"  {'★' if x['main'] else ' '} {x['label']} p.{x['page']}: {clip(x['caption'], 170)}" for x in items] \
        or ["  none found"]
    return out + ["CONTEXT:"] + context_lines(run, ["headline_claims"])


def _step_head(run, step, task=None) -> list:
    last = st.get_plan(run.state)[-1]["no"]
    sec = refs.step(step["kind"])
    return [f"STEP {step['no']} of {last} · {step['title']}", "TASK: " + (task or sec["Task"])]


def _scale() -> list:
    return ["SCALE:", refs.scale()["short"]]


def block(run, step) -> str:
    kind, s = step["kind"], run.state
    sec = refs.step(kind) if kind in refs.STEP_FILES else {}
    out = _step_head(run, step)
    if kind == "orientation":
        out += ["RULES:", sec["Rules"]] + _layouts() + _orientation_input(run)
        out += answer_format(run, step, sec["Fields"], refs.example("orientation"))
    elif kind == "loi":
        out += ["RULES:", sec["Rules"]] + _loi_input(run)
        out += answer_format(run, step, sec["Fields"], refs.example("loi"))
    elif kind == "claims":
        out += ["RULES:", sec["Rules"]] + _claims_input(run)
        out += answer_format(run, step, sec["Fields"], refs.example("claims"))
    elif kind == "data":
        out += ["RULES:", sec["Rules"]] + _data_input(run)
        out += answer_format(run, step, sec["Fields"], refs.example("data"))
    elif kind == "figures":
        out += ["RULES:", sec["Rules"]] + _figures_input(run)
        out += answer_format(run, step, sec["Fields"], refs.example("figures"))
    elif kind == "inventory":
        out += ["RULES:", sec["Rules"]]
        has_loi = s["meta"]["inputs"].get("loi")
        example = {}
        for sub, key in (("orientation", "orientation"), ("loi", "loi"), ("claims", "claims"),
                         ("data", "data"), ("figures", "figures")):
            if sub == "loi" and not has_loi:
                continue
            part = refs.step(sub)
            out += [f"--- Part \"{key}\": {part['Task']}", part["Rules"], "Fields:", part["Fields"]]
            example[key] = refs.example(sub)
        out += _layouts() + _orientation_input(run)
        if has_loi:
            out += _loi_input(run)
        out += ["READ (run these before you answer):"]
        out += read_suggestions(run, ["introduction", "data", "method", "measure", "conclusion", "discussion"])
        out += answer_format(run, step, "As described in the parts above.", example)
    elif kind == "row":
        code = step["rows"][0]
        row = refs.row(code)
        out = _step_head(run, step, f"Assess criterion {code} \"{row['title']}\". Answer the check questions in order, "
                                    "then set the score with the score decision.")
        out += ["CONTEXT:"] + context_lines(run, row["depends_on"])
        out += row_parts(run, code)
        out += _scale()
        out += ["READ (optional; read only what the check questions need):"] + _row_read(run, code)
        out += answer_format(run, step, sec["Fields"], row_example(code))
    elif kind == "group":
        codes = [c for c in step["rows"] if not (c == "L1" and not s["meta"]["inputs"].get("loi"))]
        deps = []
        for c in codes:
            deps += [d for d in refs.row(c)["depends_on"] if d not in deps]
        out += ["RULES:", sec["Rules"], "CONTEXT:"] + context_lines(run, deps)
        for c in codes:
            out += ["", f"=== CRITERION {c} ==="] + row_parts(run, c)
        out += [""] + _scale()
        out += ["READ:"] + read_suggestions(run, ["introduction", "data", "method", "results", "discussion", "limitation"])
        out += answer_format(run, step, refs.step("row")["Fields"],
                             {"rows": {c: row_example(c) for c in codes[:2]}},
                             note=f"Criteria required in this answer: {', '.join(codes)}.")
    elif kind == "consistency":
        out += ["RULES:", sec["Rules"]] + consistency_input(run)
        out += answer_format(run, step, sec["Fields"], refs.example("consistency"))
    elif kind == "synthesis":
        out += ["RULES:", sec["Rules"]] + synthesis_input(run)
        out += answer_format(run, step, sec["Fields"], refs.example("synthesis"))
    elif kind == "sentence":
        out += ["RULES:", sec["Rules"], "INPUT:"]
        out += context_lines(run, ["orientation", "data_sources", "headline_claims"])
        out += answer_format(run, step, sec["Fields"], refs.example("sentence"))
    elif kind == "readback":
        out += ["RULES:", sec["Rules"], "CALIBRATION RULES:", refs.scale()["calibration"]]
        steps = {x["rows"][0]: x["no"] for x in st.get_plan(s) if x["kind"] == "row"}
        out.append("To add or remove an entry, redo the criterion step instead: "
                   + ", ".join(f"{c}=step {n}" for c, n in steps.items())
                   + ". Command: " + run.cmd("redo <step>"))
        out += ["PREVIEW (IDs in square brackets are the targets for changes):",
                render.render_text(render.build_view(s))]
        out += answer_format(run, step, sec["Fields"], refs.example("readback"))
    else:  # script steps
        out += ["This step is done by the script.",
                "NEXT COMMAND: " + run.cmd("finish" if kind == "finish" else "next")]
    return "\n".join(out)


def consistency_input(run) -> list:
    rows = run.state["rows"]
    issues = ops.consistency_issues(rows)
    out = ["CASES:"]
    for i in issues:
        if i["type"] == "route":
            _, gap = ops.find_gap(rows, i["gap"])
            out.append(f"  {i['id']} ROUTE · gap {i['gap']} in criterion {i['row']} (p.{gap['page']}): \"{gap['text']}\" · "
                       f"topic \"{i['topic']}\" belongs to criterion {i['target']} "
                       f"\"{refs.row(i['target'])['title']}\"")
        else:
            a, b = (ops.find_gap(rows, g)[1] for g in i["gaps"])
            out.append(f"  {i['id']} DUPLICATE · p.{i['page']} · {a['id']}: \"{a['text']}\" · {b['id']}: \"{b['text']}\"")
    if not issues:
        out.append("  none. Answer with \"decisions\": [].")
    out.append("SCORES NOW: " + " ".join(f"{c}={rows[c]['score']}" for c in ROW_ORDER if c in rows))
    if ops.needs_calibration(rows):
        low, n = ops.low_share(rows)
        out += [f"CALIBRATION: {low} of {n} scored criteria are 1 or 0. Rules:", refs.scale()["calibration"],
                "Low criteria and their gaps:"]
        for c in ROW_ORDER:
            r = rows.get(c) or {}
            if r.get("score") in (0, 1):
                gaps = "; ".join(f"{g['id']} [{g['fix']['size']}] {clip(g['text'], 90)}" for g in r["gaps"])
                out.append(f"  {c}={r['score']}: {gaps}")
    return out


def synthesis_input(run) -> list:
    s = run.state
    rows = s["rows"]
    big, small = [], []
    for code, g in ops.all_gaps(rows):
        bears = f" · bears on {', '.join(g['affects'])}" if g.get("affects") else ""
        line = f"  {g['id']} [criterion score {rows[code]['score']} · {g['fix']['kind']} · {g['fix']['size']}{bears}] {g['text']}"
        on_claim = any(a.startswith("H") for a in g.get("affects") or [])
        (small if g["fix"]["size"] == "small" and not on_claim else big).append(line)
    out = ["INPUT:", "Headline claims:"] + claims_lines(s)
    out += ["Gaps that can be critical issues (moderate or substantial fix, or any fix that bears on a headline claim):"] \
        + (big or ["  none → \"critical\": []"])
    out += ["Gaps with a small fix that bear on no headline claim (only for \"other_changes\"):"] + (small or ["  none"])
    out += ["Strengths:"] + [f"  {p['id']} [criterion score {rows[code]['score']}] {p['text']}"
                             for code, p in ops.all_plus(rows)]
    return out
