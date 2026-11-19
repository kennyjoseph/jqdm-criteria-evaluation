"""state.json → scorecard. Deterministic: the same registry gives a byte-identical file."""
from __future__ import annotations

import html
import re

from . import metrics as metrics_mod
from . import ops, refs
from .common import ASSET_DIR, GROUPS, ROW_ORDER, SCORE_LABEL, SIZE_RANK, read_text

NOTE = ("Input on how effectively this manuscript carries out its accepted Letter of Inquiry, compared "
        "with what JQD:DM values and what its published papers tend to have. It is not a review decision "
        "and does not suggest one. Scores show how fully the paper currently meets each value, not how "
        "much work a fix would take; the tags on each point give the size of the fix. Each \"one potential "
        "fix\" is a suggestion: you need not apply it, and any change or explanation that addresses the point "
        "is fine. Scores of 2 are "
        "common in published JQD:DM papers. When you submit, address each item under \"Response required at "
        "submission\" or explain in your cover letter, by its label, why you left it unchanged. Everything "
        "else is optional. The reviewers and the handling editor read this evaluation and your responses.")
MINOR_LABELS = [("figures", "Figures and captions"), ("cross_references", "Cross-references"),
                ("numbers", "Numbers"), ("citations", "Citations"),
                ("wording", "Wording"), ("other", "Other")]
RECOMPUTED_AT_END = {"V12", "V13", "V21"}


# ---------------------------------------------------------------- view

def requires_response(gap: dict, score) -> bool:
    """Whether a gap in a criterion scored 0 or 1 needs a response at submission.

    Score 0 (the paper does not attempt the criterion): every gap. Score 1: gaps that bear on a
    headline claim or need more than a small fix; the others stay in the evaluation as optional.
    Critical gaps are always required and are handled by the caller.
    """
    if score == 0:
        return True
    return (any(str(a).startswith("H") for a in gap.get("affects") or [])
            or gap["fix"]["size"] != "small")


def _page(state, item):
    doc = item.get("doc") or "manuscript"
    page = item.get("page")
    if page is None:
        return ""
    if doc == "manuscript":
        offset = state.get("meta", {}).get("page_offset")
        return f"p. {page + offset}" if isinstance(offset, int) and page + offset >= 1 else f"p. {page}"
    return f"{'LOI' if doc == 'loi' else 'appendix'} p. {page}"


def _resolver(state):
    shorts = {c["id"]: c.get("short") or c["text"] for c in state.get("headline_claims", [])}

    def resolve(text):
        def one(m):
            hid = m.group(1)
            if hid not in shorts:
                return m.group(0)
            return f"the claim “{shorts[hid]}”{m.group(2) or ''}"
        # "H2" → "the claim “…”", without doubling a preceding "the claim"; capitalized at sentence start.
        text = re.sub(r"(?i)\b(?:the\s+)?(?:headline\s+)?claims?\s+(?=H[1-5]\b)", "", text.strip())
        text = re.sub(r"\b(H[1-5])\b(['’]s)?", one, text)
        return re.sub(r"(^|[.!?]\s+)the claim", lambda m: m.group(1) + "The claim", text)
    return resolve, shorts


def _tag(fix):
    return f"{fix['kind']} · {fix['size']}"


def _features(state):
    """Up to five 'absent' strong-paper features: rows whose gaps bear on headline claims first,
    then lower scores first, then row order; at most two per row."""
    rows = state.get("rows", {})
    ranked = []
    for idx, code in enumerate(ROW_ORDER):
        row = rows.get(code) or {}
        absent = [k for k in refs.row(code)["features"] if row.get("features", {}).get(k) == "absent"]
        if not absent or row.get("score") == "NA":
            continue
        bears = any(g.get("affects") for g in row.get("gaps", []))
        ranked.append((0 if bears else 1, row.get("score", 3), idx, code, absent[:2]))
    ranked.sort()
    out = []
    for round_ in (0, 1):
        for _, _, _, code, absent in ranked:
            if round_ < len(absent) and len(out) < 5:
                meta = refs.row(code)
                out.append({"text": meta["features"][absent[round_]], "loc": f"{code} · {meta['title']}"})
    return out


LIT_NOTE = ("Works named here were suggested from memory by a language model. They may not exist or may be "
            "less closely related than they seem; check them before citing.")


def _examples(items, n=3):
    shown = "; ".join(items[:n])
    return shown + (f"; and {len(items) - n} more" if len(items) > n else "")


def _minor(state, resolve):
    buckets = {k: [] for k, _ in MINOR_LABELS}
    for code in ROW_ORDER:
        for m in (state.get("rows", {}).get(code) or {}).get("minor") or []:
            loc = _page(state, m)
            item = resolve(m["text"]).rstrip(".") + (f" ({loc})" if loc else "")
            # The same slip noted under two criteria is printed once.
            if not any(ops._sim(item, x) >= 0.8 for x in buckets[m["category"]]):
                buckets[m["category"]].append(item)
    mt = state.get("metrics") or {}
    if mt.get("unresolved_markers"):
        buckets["cross_references"].append(
            "unresolved references shown as \"??\" (automated check): " + _examples(mt["unresolved_markers"]))
    return [{"label": label, "text": _examples(buckets[key]) + "."}
            for key, label in MINOR_LABELS if buckets[key]]


def build_view(state: dict) -> dict:
    """Everything the scorecard shows, as plain data. Used by HTML and plain-text output."""
    meta, rows = state.get("meta", {}), state.get("rows", {})
    syn, orient = state.get("synthesis") or {}, state.get("orientation") or {}
    resolve, shorts = _resolver(state)
    has_loi = bool(meta.get("inputs", {}).get("loi"))

    critical = []
    for c in sorted(syn.get("critical", []), key=lambda c: c["rank"]):
        code, gap = ops.find_gap(rows, c["gap"])
        if gap is None:
            continue
        critical.append({"id": gap["id"], "text": resolve(gap["text"]), "why": resolve(c["why"]),
                         "fix": resolve(gap["fix"]["text"]), "tag": _tag(gap["fix"]),
                         "loc": f"{gap['id']} · {_page(state, gap)}",
                         "bears_on": [shorts[a] for a in gap.get("affects") or [] if a in shorts]})
    strengths = []
    for sid in syn.get("strengths", []):
        code, p = ops.find_plus(rows, sid)
        if p is not None:
            strengths.append({"id": sid, "text": resolve(p["text"]), "loc": f"{code} · {_page(state, p)}"})

    groups = []
    for key, title, codes in GROUPS:
        g = {"title": title, "rows": []}
        for code in codes:
            r = rows.get(code)
            if r is None:
                continue
            score = r["score"]
            gaps = [{"id": x["id"], "text": resolve(x["text"]), "quote": x.get("quote") or "",
                     "fix": resolve(x["fix"]["text"]), "tag": _tag(x["fix"]), "loc": _page(state, x)}
                    for x in r.get("gaps", [])]
            all_small = (score == 1 and gaps
                         and all(x["fix"]["size"] == "small" for x in r["gaps"]))
            notes = ["Every gap in this criterion has a small fix: the score shows how fully the value is "
                     "met now, and a few sentences or numbers would raise it."] if all_small else []
            if code == "C2" and gaps:
                notes.append(LIT_NOTE)
            g["rows"].append({
                "code": code, "title": refs.row(code)["title"], "score": score,
                "label": SCORE_LABEL[score], "cls": "sna" if score == "NA" else f"s{score}",
                "na_reason": resolve(r.get("na_reason") or "") if score == "NA" else "",
                "plus": [{"id": x["id"], "text": resolve(x["text"]), "loc": _page(state, x)}
                         for x in r.get("plus", [])],
                "gaps": gaps,
                "note": " ".join(notes),
            })
        groups.append(g)

    why = {c["id"]: c["why"] for c in critical}
    raw = {x["id"]: x for r in rows.values() for x in r.get("gaps", [])}
    responses = []
    for g in groups:
        for r in g["rows"]:
            low = r["score"] in (0, 1)
            gaps = [x for x in r["gaps"]
                    if x["id"] in why or (low and requires_response(raw[x["id"]], r["score"]))]
            if not gaps:
                continue
            if low:
                rest = len(gaps) < len(r["gaps"])
                text = (f"Scored {r['score']} of 3 ({r['label']}). " + (
                    "The score rests on the points below; respond to each by its label." if not rest else
                    "Respond to the points below by their labels; smaller points under this criterion are optional."))
            else:
                text = (f"Scored {r['score']} of 3 ({r['label']}). "
                        + ("This point bears" if len(gaps) == 1 else "These points bear")
                        + " on a headline claim; respond by its label.")
            responses.append({"label": f"{r['code']} {r['title']}", "text": text, "items": [
                {"label": x["id"], "text": x["text"], "loc": x["loc"], "why": why.get(x["id"], "")}
                for x in gaps]})

    other = []
    for ch in syn.get("other_changes", []):
        fixes = [ops.find_gap(rows, gid)[1] for gid in ch["gaps"]]
        fixes = [f["fix"] for f in fixes if f]
        if not fixes:
            continue
        kind = "analysis" if any(f["kind"] == "analysis" for f in fixes) else "writing"
        size = max((f["size"] for f in fixes), key=SIZE_RANK.get)
        other.append({"text": resolve(ch["text"]), "tag": f"{kind} · {size}",
                      "raises": ", ".join(ch.get("raises") or [])})

    size_line, norms_line = metrics_mod.size_summary(state.get("metrics") or {},
                                                     orient.get("paper_type", "full"))
    warnings = [f"{w['rule']} (step {w['step']}): {w['text']}" for w in state.get("warnings", [])
                if w["rule"] not in RECOMPUTED_AT_END]
    warnings += [f"{w['rule']}: {w['text']}" for w in state.get("end_warnings", [])]
    manual = meta.get("mode") == "manual"
    one = syn.get("one_sentence") or ""
    if one and not syn.get("one_sentence_stated", True):
        one = "This sentence cannot be stated for this manuscript: " + one
    return {
        "title": orient.get("title", "(title not recorded)"),
        "date": meta.get("created", ""),
        "note": NOTE,
        "loi_line": ("Read alongside the accepted Letter of Inquiry." if has_loi else
                     "No Letter of Inquiry was provided; the accepted question was inferred from the manuscript."),
        "mode_note": ("Created without validation of quotes and page references (manual mode, "
                      "no manuscript text available to the scripts)." if manual and not meta.get("quotes_checked")
                      else ""),
        "one_sentence": resolve(one),
        "critical": critical, "responses": responses, "strengths": strengths,
        "size_line": size_line, "norms_line": norms_line,
        "groups": groups, "features": _features(state), "other": other,
        "minor": _minor(state, resolve),
        "footer": {"run_id": meta.get("run_id", ""), "skill_version": meta.get("skill_version", ""),
                   "model": meta.get("model") or "not reported", "date": meta.get("created", ""),
                   "warnings": warnings},
    }


# ---------------------------------------------------------------- HTML

def esc(text) -> str:
    return html.escape(str(text), quote=True)


def _li(cls, sign, body):
    return f'<li class="{cls}"><span class="sign">{sign}</span> {body}</li>'


def _loc(loc):
    return f' <span class="loc">({esc(loc)})</span>' if loc else ""


def _tag_html(tag):
    return f' <span class="tag">{esc(tag)}</span>'


def render_html(view: dict) -> str:
    v = view
    strengths = "\n".join(_li("plus", "+", esc(s["text"]) + _loc(s["loc"])) for s in v["strengths"])
    def _resp(x):
        sub = "".join(f'<li><strong>{esc(i["label"])}</strong> {esc(i["text"])}{_loc(i["loc"])}'
                      + (f'<span class="why"><span class="fixlabel">Why it matters:</span> {esc(i["why"])}</span>'
                         if i["why"] else "")
                      + "</li>" for i in x["items"])
        return (f'<li><strong>{esc(x["label"])}:</strong> {esc(x["text"])}'
                f'<ul class="points">{sub}</ul></li>')
    responses = ("<ul class=\"crits\">\n" + "\n".join(_resp(x) for x in v["responses"]) + "\n</ul>"
                 if v["responses"] else
                 "<p>Nothing requires a response. All changes in this criteria evaluation are optional.</p>")
    table = []
    for g in v["groups"]:
        table.append(f'<tr class="group"><th colspan="4" scope="colgroup">{esc(g["title"])}</th></tr>')
        for r in g["rows"]:
            bullets = [_li("plus", "+", esc(p["text"]) + _loc(p["loc"])) for p in r["plus"]]
            for x in r["gaps"]:
                quote = (f'<span class="quote">From the paper: <q>{esc(x["quote"])}</q></span>'
                         if x["quote"] else "")
                bullets.append(_li("gap", "−", f'<strong class="gid">{esc(x["id"])}</strong> {esc(x["text"])}'
                                   f'{_loc(x["loc"])}{quote}<span class="fix"><span class="fixlabel">One potential '
                                   f'fix:</span> {esc(x["fix"])}{_tag_html(x["tag"])}</span>'))
            body = f'<ul class="marks">{"".join(bullets)}</ul>' if bullets else ""
            if r["na_reason"]:
                body = f'<p>{esc(r["na_reason"])}</p>' + body
            if r["note"]:
                body += f'<p class="rownote">{esc(r["note"])}</p>'
            table.append(
                f'<tr><td class="code">{esc(r["code"])}</td><td class="value">{esc(r["title"])}</td>'
                f'<td class="score"><span class="badge {r["cls"]}">{esc(r["score"] if r["score"] != "NA" else "N/A")}'
                f'</span>{"" if r["score"] == "NA" else " " + esc(r["label"])}</td>'
                f'<td class="expl">{body}</td></tr>')
    features = ("\n".join(f'<li>{esc(f["text"])}{_loc(f["loc"])}</li>' for f in v["features"])
                or "<li>No strong-paper feature was marked as absent.</li>")
    other = ("\n".join(f'<li>{esc(o["text"])}{_tag_html(o["tag"])}'
                       + (f' <span class="loc">(would raise {esc(o["raises"])})</span>' if o["raises"] else "")
                       + "</li>" for o in v["other"]) or "<li>None beyond the points listed under each criterion.</li>")
    minor = ("\n".join(f'<li><strong>{esc(m["label"])}:</strong> {esc(m["text"])}</li>' for m in v["minor"])
             or "<li>None recorded.</li>")
    f = v["footer"]
    warn = ("<p>Validator warnings:</p><ul>" + "".join(f"<li>{esc(w)}</li>" for w in f["warnings"]) + "</ul>"
            if f["warnings"] else "<p>Validator warnings: none.</p>")
    footer = (f'<p>Run {esc(f["run_id"])} · jqd-paper-review {esc(f["skill_version"])} · model: '
              f'{esc(f["model"])} · {esc(f["date"])}</p>{warn}')
    fills = {
        "title": esc(v["title"]), "date": esc(v["date"]), "note": esc(v["note"]),
        "loi_line": esc(v["loi_line"]),
        "mode_note": f'<p class="modenote">{esc(v["mode_note"])}</p>' if v["mode_note"] else "",
        "one_sentence": esc(v["one_sentence"]), "responses": responses, "strengths": strengths,
        "size_line": esc(v["size_line"]), "norms_line": esc(v["norms_line"]),
        "table_rows": "\n".join(table), "features": features, "other_changes": other,
        "minor": minor, "footer": footer,
    }
    template = read_text(ASSET_DIR / "template.html")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: fills[m.group(1)], template)


def html_to_text(page: str) -> str:
    """Visible text of the rendered page (for the anonymity and wording checks)."""
    page = re.sub(r"(?s)<style.*?</style>|<head.*?</head>", " ", page)
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page)))


# ---------------------------------------------------------------- plain text

def render_text(view: dict, with_ids=True) -> str:
    v, out = view, []

    def ident(x):
        return f"[{x['id']}] " if with_ids and x.get("id") else ""

    out += ["JQD:DM criteria evaluation", v["title"], v["date"], "", v["loi_line"]]
    if v["mode_note"]:
        out.append(v["mode_note"])
    out += ["", "THE PAPER IN ONE SENTENCE", v["one_sentence"], ""]
    out += ["STRENGTHS"] + [f"+ {ident(s)}{s['text']} ({s['loc']})" for s in v["strengths"]]
    out += ["", "RESPONSE REQUIRED AT SUBMISSION"]
    for x in v["responses"]:
        out.append(f"{x['label']}: {x['text']}")
        out += [f"   {p['label']} {p['text']}" + (f" ({p['loc']})" if p["loc"] else "")
                + (f"\n      Why it matters: {p['why']}" if p["why"] else "") for p in x["items"]]
    if not v["responses"]:
        out.append("Nothing requires a response.")
    out += ["", "SIZE", v["size_line"], v["norms_line"], "", "SCORES BY CRITERION"]
    for g in v["groups"]:
        out.append(f"-- {g['title']} --")
        for r in g["rows"]:
            score = "N/A" if r["score"] == "NA" else f"{r['score']} {r['label']}"
            out.append(f"{r['code']} {r['title']}: {score}")
            if r["na_reason"]:
                out.append(f"    {r['na_reason']}")
            out += [f"    + {ident(p)}{p['text']} ({p['loc']})" for p in r["plus"]]
            for x in r["gaps"]:
                out.append(f"    − {ident(x)}{x['text']} ({x['loc']})")
                if x["quote"]:
                    out.append(f"      From the paper: “{x['quote']}”")
                out.append(f"      One potential fix: {x['fix']} [{x['tag']}]")
            if r["note"]:
                out.append(f"    Note: {r['note']}")
    out += ["", "WHAT JQD:DM PAPERS TEND TO HAVE THAT THIS ONE MAY NOT"]
    out += [f"- {f['text']} ({f['loc']})" for f in v["features"]] or ["- No strong-paper feature was marked as absent."]
    out += ["", "OTHER CHANGES THAT WOULD STRENGTHEN THE PAPER"]
    out += [f"- {o['text']} [{o['tag']}]" + (f" (would raise {o['raises']})" if o["raises"] else "")
            for o in v["other"]] or ["- None beyond the points listed under each criterion."]
    out += ["", "SMALLER FIXES"]
    out += [f"- {m['label']}: {m['text']}" for m in v["minor"]] or ["- None recorded."]
    return "\n".join(out) + "\n"
