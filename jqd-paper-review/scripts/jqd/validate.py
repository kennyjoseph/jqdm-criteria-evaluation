"""All validation rules V01–V24. 'S' rules run when a step is submitted, 'E' rules at the end."""
from __future__ import annotations

import re

from . import anon, metrics, ops, quotes, refs, schemas
from .common import Problem, ROW_ORDER, count_words, dehyphenate, errors_of

NON_TEXT_KEYS = {"id", "kind", "type", "status", "topic", "layout", "billing", "category", "op",
                 "target", "figure", "model", "redact", "action", "issue", "keep_gap", "gap", "doc",
                 "paper_type", "size", "row"}
DECISION_PATTERNS = [
    # Statistical and technical uses ("rejects the null", "false rejection rate", "rejection sampling") are fine.
    (r"(?<!false )(?<!false-)\breject(?:s|ed|ion)?\b(?! (?:the |a )?(?:null|hypothes|rates?\b|sampling|region))", "reject"),
    (r"\b(?:minor|major) revisions?\b", "minor/major revision"),
    (r"\brevise[- ]and[- ]resubmit\b|\bR&R\b", "revise and resubmit"),
    (r"\b(?:should|would|will|could|recommend\w*|suggest\w*)(?: \w+){0,2} accept(?:ed|ance)?\b", "accept"),
    (r"\baccept(?:ance of)? (?:the|this) (?:paper|manuscript|submission)\b|\bacceptance\b", "accept"),
    (r"\b(?:overall|total|aggregate|summary) (?:score|rating|grade|verdict|assessment)\b", "overall score"),
    (r"\b(?:un)?publishable\b|\bready for publication\b", "publication verdict"),
]
ID_IN_TEXT = re.compile(r"(?<!Table )(?<!Tables )(?<!Fig\. )(?<!Figs\. )(?<!Figure )(?<!Figures )"
                        r"(?<!Section )(?<!Appendix )(?<!Note )(?<!Eq\. )(?<!SI )(?<![-–])\b[SM]\d{1,2}\b(?![-–]\d)")


class Ctx:
    """Texts available for page and quote checks: {'manuscript': [pages], 'loi': …, 'appendix': …}."""

    def __init__(self, docs=None):
        self.docs = {k: v for k, v in (docs or {}).items() if v}

    def pages(self, doc="manuscript"):
        return self.docs.get(doc)


# ---------------------------------------------------------------- helpers

def iter_texts(obj, path=""):
    """Yield (path, key, string) for every free-text string in an answer.
    Strings inside lists (ID lists, check answers, redact names) are not free text."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            sub = f"{path}.{k}" if path else k
            if isinstance(v, str):
                if k not in NON_TEXT_KEYS:
                    yield sub, k, v
            else:
                yield from iter_texts(v, sub)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                yield from iter_texts(v, f"{path}[{i}]")


def decision_words(text: str):
    return [label for pat, label in DECISION_PATTERNS if re.search(pat, text, re.I)]


def loaded_words(text: str):
    low = text.lower()
    return [w for w in refs.scale()["loaded_words"]
            if re.search(r"(?<!\w)" + re.escape(w.lower()) + r"(?!\w)", low)]


def check_texts(state, answer, prefix="", redact=None):
    """V19 and V20 on the free-text fields of one answer; plain IDs in text."""
    out = []
    meta = state.get("meta", {})
    redact = meta.get("redact", []) if redact is None else redact
    private = meta.get("private", {})
    for path, key, text in iter_texts(answer, prefix):
        hits = anon.find_identifiers(text, redact, private.get("input_names", []))
        if hits:
            out.append(Problem("V19", path, f"The text contains identifying information: \"{hits[0]}\".",
                               "Remove it. Write \"the authors\" or \"the manuscript\" instead of names, "
                               "and shorten or drop a quote that contains a name. Author surnames are matched on "
                               "their own, so drop citations of the authors' own work (\"prior work\" instead)."))
        if key == "quote":
            continue
        for label in decision_words(text):
            out.append(Problem("V20", path, f"The text contains decision language ({label}).",
                               "Describe what the paper does and what would strengthen it. "
                               "Write one score per criterion instead of a verdict."))
        if key != "title" and ID_IN_TEXT.search(text):
            out.append(Problem("V01", path, f"The text contains an inventory ID (\"{ID_IN_TEXT.search(text).group(0)}\").",
                               "Write the name of the data source or measure instead of its ID."))
    return out


def _check_page(ctx, doc, page, path, out, strict=True):
    pages = ctx.pages(doc)
    if pages is None:
        if strict and ctx.pages("manuscript") is not None and doc != "manuscript":
            out.append(Problem("V01", path, f"No {doc} file was provided, so it cannot be cited.",
                               "Delete the \"doc\" field and give a manuscript page."))
        return None
    if page > len(pages):
        out.append(Problem("V01", path, f"Page {page} does not exist; the {doc} has {len(pages)} pages.",
                           f"Use a page marker from 1 to {len(pages)} as shown by `review.py show`."))
        return None
    return pages


def check_quote(ctx, item, path, out, doc=None, page_key="page"):
    """V09. Corrects item[page_key] in place when the quote is on another page."""
    doc = doc or item.get("doc") or "manuscript"
    pages = _check_page(ctx, doc, item[page_key], f"{path}.{page_key}", out)
    quote = item.get("quote")
    if pages is None or not quote:
        return None
    if dehyphenate(quote) != quote:
        item["quote"] = quote = dehyphenate(quote)  # "suffi- ciently" copied across a line break
    status, found = quotes.find_quote(quote, pages, item[page_key])
    if status == "missing":
        p = item[page_key]
        out.append(Problem("V09", f"{path}.quote",
                           f"The quote \"{quote}\" was not found on page {p} or anywhere in the {doc}.",
                           f"Copy the quote verbatim from `review.py show --pages {max(1, p - 1)}-{p + 1}`"
                           + (", or delete the quote field." if path.find("claims") < 0 else ".")))
    elif status == "moved":
        out.append(Problem("V09", f"{path}.{page_key}",
                           f"The quote is on page {found}, not page {item[page_key]}; the page was corrected.",
                           level="warning"))
        item[page_key] = found
    return status


def _unique_ids(items, path, out, expect=None):
    seen = set()
    for i, it in enumerate(items):
        if it["id"] in seen:
            out.append(Problem("V02", f"{path}[{i}].id", f"The ID \"{it['id']}\" is used twice.",
                               "Give every entry its own ID, numbered 1, 2, 3 …"))
        seen.add(it["id"])
        if expect and it["id"] != expect(i):
            out.append(Problem("V02", f"{path}[{i}].id",
                               f"The ID \"{it['id']}\" is out of sequence; expected \"{expect(i)}\".",
                               "Number the entries consecutively in list order."))


def _refs_exist(ids, known, path, out, what):
    for i, ref in enumerate(ids or []):
        if ref not in known:
            out.append(Problem("V02", f"{path}[{i}]", f"\"{ref}\" does not refer to an existing {what}.",
                               "Use one of: " + (", ".join(sorted(known)) or "(none exist; leave the list empty)") + "."))


def claim_ids(state):
    return {c["id"] for c in state.get("headline_claims", [])}


# ---------------------------------------------------------------- inventory steps (S)

def check_orientation(state, ans, ctx, prefix=""):
    out = schemas.check(ans, schemas.ORIENTATION, prefix)
    if errors_of(out):
        return out
    p = f"{prefix}." if prefix else ""
    check_quote(ctx, ans["primary_aim"], f"{p}primary_aim", out)
    for i, aim in enumerate(ans["secondary_aims"]):
        _check_page(ctx, "manuscript", aim["page"], f"{p}secondary_aims[{i}].page", out)
    out += check_texts(state, ans, prefix, redact=ans["redact"])
    return out


def check_loi(state, ans, ctx, prefix=""):
    out = schemas.check(ans, schemas.LOI, prefix)
    if errors_of(out):
        return out
    p = f"{prefix}." if prefix else ""
    _unique_ids(ans["promises"], f"{p}promises", out, lambda i: f"P{i + 1}")
    for i, pr in enumerate(ans["promises"]):
        _check_page(ctx, "loi", pr["loi_page"], f"{p}promises[{i}].loi_page", out, strict=False)
    return out + check_texts(state, ans, prefix)


def check_claims(state, ans, ctx, prefix=""):
    out = schemas.check(ans, schemas.CLAIMS, prefix)
    if errors_of(out):
        return out
    p = f"{prefix}." if prefix else ""
    _unique_ids(ans["claims"], f"{p}claims", out, lambda i: f"H{i + 1}")
    for i, c in enumerate(ans["claims"]):
        check_quote(ctx, c, f"{p}claims[{i}]", out)
    if len(ans["claims"]) == 2:
        out.append(Problem("V01", f"{p}claims", "Only 2 headline claims were recorded; 3–5 are usual.",
                           level="warning"))
    if not any(c["status"] == "firm" for c in ans["claims"]):
        out.append(Problem("V22", f"{p}claims", "No headline claim has the status \"firm\".",
                           level="warning"))
    return out + check_texts(state, ans, prefix)


def check_data(state, ans, ctx, prefix=""):
    out = schemas.check(ans, schemas.DATA, prefix)
    if errors_of(out):
        return out
    p = f"{prefix}." if prefix else ""
    _unique_ids(ans["data_sources"], f"{p}data_sources", out, lambda i: f"S{i + 1}")
    _unique_ids(ans["measures"], f"{p}measures", out, lambda i: f"M{i + 1}")
    known = claim_ids(state)
    for i, m in enumerate(ans["measures"]):
        _refs_exist(m["supports"], known, f"{p}measures[{i}].supports", out, "headline claim")
    for key in ("data_sources", "measures", "subsets"):
        for i, it in enumerate(ans.get(key) or []):
            _check_page(ctx, "manuscript", it["page"], f"{p}{key}[{i}].page", out)
    _check_page(ctx, "manuscript", ans["design"]["page"], f"{p}design.page", out)
    if ans["design"].get("loi_promise"):
        _refs_exist([ans["design"]["loi_promise"]], {x["id"] for x in state.get("loi_promises", [])},
                    f"{p}design.loi_promise", out, "LOI promise")
    return out + check_texts(state, ans, prefix)


def norm_label(label: str) -> str:
    m = re.match(r"\s*(fig|tab)\w*\.?\s*([A-Za-z]{0,2}\.?\d+)\s*(\(appendix\))?", label, re.I)
    if not m:
        return label.strip()
    return f"{m.group(1).title()} {m.group(2).replace('.', '').upper()}" + (" (appendix)" if m.group(3) else "")


def check_figures(state, ans, ctx, prefix=""):
    out = schemas.check(ans, schemas.FIGURES, prefix)
    if errors_of(out):
        return out
    p = f"{prefix}." if prefix else ""
    items = (state.get("metrics") or {}).get("items")
    known_claims, seen = claim_ids(state), set()
    labels = {x["label"] for x in items} if items is not None else None
    for i, m in enumerate(ans["map"]):
        label = norm_label(m["figure"])
        if labels is not None and label not in labels:
            out.append(Problem("V02", f"{p}map[{i}].figure", f"\"{m['figure']}\" is not in the list of figures and tables.",
                               "Use the labels exactly as listed in the task block, e.g. \"Fig 2\" or \"Tab 1\"."))
        if label in seen:
            out.append(Problem("V02", f"{p}map[{i}].figure", f"\"{label}\" is listed twice.",
                               "List every figure and table once."))
        seen.add(label)
        _refs_exist(m["supports"], known_claims, f"{p}map[{i}].supports", out, "headline claim")
    if items is not None:
        missing = [x["label"] for x in items if x["main"] and x["label"] not in seen]
        if missing:
            out.append(Problem("V01", f"{p}map", "Main-text figures or tables are missing from the map: "
                               + ", ".join(missing) + ".",
                               "Add one entry for each of them. Use \"supports\": [] if it supports no headline claim."))
    return out


# ---------------------------------------------------------------- row steps (S)

def _ref_keys(text):
    """{("table"|"figure"|"section", number)} for every reference written in a text."""
    keys = {(metrics._kind(m.group(1)), m.group(2).replace(".", "").upper()) for m in metrics.MENTION_RE.finditer(text)}
    keys |= {("section", m.group(1)) for m in metrics.SECTION_REF_RE.finditer(text)}
    return keys


def check_crossref_minor(ctx, minor, path, out):
    """V24. A cross-reference reported as broken must actually occur in the manuscript."""
    pages = ctx.pages("manuscript")
    if not pages:
        return
    present = _ref_keys("\n".join(pages))
    for i, m in enumerate(minor):
        if m.get("category") != "cross_references":
            continue
        missing = sorted(f"{k.capitalize()} {n}" for k, n in _ref_keys(m["text"]) - present)
        if missing:
            out.append(Problem("V24", f"{path}[{i}].text",
                               f"The manuscript never refers to {', '.join(missing)}, so it cannot be a broken cross-reference.",
                               "Write each reference exactly as the paper does (e.g. \"Table 7\"), after confirming it with "
                               "`review.py find`, or delete the item."))


def check_row(state, code, ans, ctx, prefix="", with_schema=True, with_quotes=True):
    """Rules V01–V11 for one row answer. `ans` may be modified (page correction)."""
    out = schemas.check(ans, schemas.ROW, prefix) if with_schema else []
    if errors_of(out):
        return out
    p = f"{prefix}." if prefix else ""
    row = refs.row(code)
    score, plus, gaps = ans["score"], ans["plus"], ans["gaps"]
    has_loi = bool(state.get("meta", {}).get("inputs", {}).get("loi", False))

    for kind, items, sign in (("plus", plus, "+"), ("gaps", gaps, "-")):
        _unique_ids(items, f"{p}{kind}", out)
        for i, it in enumerate(items):
            if not it["id"].startswith(f"{code}{sign}"):
                out.append(Problem("V02", f"{p}{kind}[{i}].id", f"The ID \"{it['id']}\" does not belong to criterion {code}.",
                                   f"Use \"{code}{sign}{i + 1}\"."))
    known = claim_ids(state) | {x["id"] for x in state.get("loi_promises", [])}
    topics = refs.routing()
    for i, g in enumerate(gaps):
        _refs_exist(g.get("affects"), known, f"{p}gaps[{i}].affects", out, "headline claim or LOI promise")
        t = g.get("topic")
        if t and t not in topics:
            mine = ", ".join(refs.topics_for(code)) or "(none for this criterion)"
            out.append(Problem("V01", f"{p}gaps[{i}].topic", f"\"{t}\" is not a topic in the routing table.",
                               f"Delete the topic field, or use one of the topics of criterion {code}: {mine}."))
        elif t and topics[t]["row"] != code:
            out.append(Problem("V12", f"{p}gaps[{i}].topic",
                               f"The topic \"{t}\" belongs to criterion {topics[t]['row']}, not {code}. "
                               "The consistency step will ask whether to move this gap.", level="warning"))
        if with_quotes:
            check_quote(ctx, g, f"{p}gaps[{i}]", out)
    if with_quotes:
        for i, it in enumerate(plus):
            _check_page(ctx, it.get("doc") or "manuscript", it["page"], f"{p}plus[{i}].page", out)

    if with_quotes:
        check_crossref_minor(ctx, ans.get("minor") or [], f"{p}minor", out)

    feats = ans["features"]
    for name in row["features"]:
        if name not in feats:
            out.append(Problem("V01", f"{p}features.{name}", f"The feature \"{name}\" has no status.",
                               f"Add \"{name}\" with one of: {', '.join(schemas.FEATURE_STATUS)}."))
    for name in feats:
        if name not in row["features"]:
            out.append(Problem("V01", f"{p}features.{name}", f"\"{name}\" is not a feature of criterion {code}.",
                               "Delete it. Use exactly the feature names listed in the task block."))

    if score == "NA":
        if not ans.get("na_reason"):
            out.append(Problem("V04", f"{p}na_reason", "The score is \"NA\" but no reason is given.",
                               "Add \"na_reason\": one sentence (≤ 200 characters) on why the criterion cannot apply."))
        if gaps:
            out.append(Problem("V04", f"{p}gaps", "A criterion scored \"NA\" cannot list gaps.",
                               "Delete the gaps, or give the criterion a score from 0 to 3."))
    else:
        if len(ans["checks"]) != len(row["questions"]):
            out.append(Problem("V01", f"{p}checks", f"Criterion {code} has {len(row['questions'])} check questions, "
                               f"but \"checks\" has {len(ans['checks'])} answers.",
                               "Write one short answer per check question, in order."))
    if code == "L1":
        if not has_loi and score != "NA":
            out.append(Problem("V10", f"{p}score", "No Letter of Inquiry was provided, so L1 must be \"NA\".",
                               "Set \"score\": \"NA\" and \"na_reason\": \"No Letter of Inquiry provided.\""))
        if has_loi and score == "NA":
            out.append(Problem("V10", f"{p}score", "A Letter of Inquiry was provided, so L1 cannot be \"NA\".",
                               "Score L1 from 0 to 3 against the LOI promises listed in the task block."))
    if score in (0, 1, 2) and not gaps:
        out.append(Problem("V03", f"{p}gaps", f"The score is {score} but no gap is listed.",
                           "Add at least one gap with page and fix (kind, size, text), or set the score to 3."))
    if score == 3:
        big = [g["id"] for g in gaps if g["fix"]["size"] != "small"]
        if big:
            out.append(Problem("V06", f"{p}score", f"The score is 3, but gap {big[0]} needs a "
                               "moderate or substantial fix.",
                               "Lower the score to 2 or less, or change the fix size to \"small\" if that is accurate."))
    behind_claim = [g for g in gaps if any(a.startswith("H") for a in g.get("affects") or [])]
    not_small = [g for g in gaps if g["fix"]["size"] != "small"]
    if score == 1 and code == "P4":
        # Length problems rarely attach to one headline claim; the P4 rubric allows a 1 for a
        # substantial share of off-aim material, which is at least a moderate cut.
        if not not_small:
            out.append(Problem("V23", f"{p}score", "The score is 1, but every gap has a small fix.",
                               "Raise the score to 2, or set the fix size to \"moderate\" if the cut is that large."))
    elif score == 1:
        if not behind_claim and len(not_small) < 2:
            out.append(Problem("V23", f"{p}score", "The score is 1, but no gap bears on a headline claim and fewer "
                               "than two gaps need more than a small fix.",
                               "Raise the score to 2, or list the headline claim (H…) the gap changes under "
                               "\"affects\" if that is accurate."))
    if score == 0 and code == "P1" and not behind_claim:
        out.append(Problem("V25", f"{p}score", "P1 is 0, but no gap names a headline claim that depends on an "
                           "unchecked choice.",
                           "Score 0 only when a headline number depends on a consequential choice and nothing is "
                           "checked. Otherwise raise the score to 2, or list that claim (H…) under \"affects\"."))
    present = [k for k, v in feats.items() if v == "present"]
    if present and not plus and score != "NA":
        out.append(Problem("V05", f"{p}plus", f"The feature \"{present[0]}\" is marked present, but no strength is listed.",
                           "Add one strength (\"plus\") that says where the paper does this, with the page."))
    if score == 0 and present:
        out.append(Problem("V07", f"{p}score", f"The score is 0 although the feature \"{present[0]}\" is marked present.",
                           level="warning"))
    total = len(plus) + len(gaps)
    if score != "NA":
        if total == 0:
            out.append(Problem("V08", f"{p}plus", "The criterion has no strengths and no gaps.",
                               "Add at least one strength or gap with a page."))
        elif total > 3:
            out.append(Problem("V08", f"{p}gaps", f"The criterion has {total} strengths and gaps; the limit is 3.",
                               "Keep the 2 or 3 most important points, usually one strength and one or two gaps. "
                               "Move small items to \"minor\"."))
    design = state.get("design") or {}
    if code == "A2" and design.get("kind") in schemas.CAUSAL_DESIGNS and not design.get("loi_promise") and score != 0:
        kind = state["design"]["kind"]
        if not ans.get("design_justification"):
            out.append(Problem("V11", f"{p}score", f"The data step recorded a causal design ({kind}); "
                               "the rule for A2 is then score 0.",
                               "Set the score to 0, or add \"design_justification\": one sentence on why "
                               "the design is not used to support a causal claim."))
        else:
            out.append(Problem("V11", f"{p}score", f"A2 is scored {score} although a causal design ({kind}) "
                               "was recorded; a justification was given.", level="warning"))
    body = {"plus": plus, "gaps": gaps, "minor": ans.get("minor") or [], "na_reason": ans.get("na_reason") or ""}
    return out + check_texts(state, body, prefix)


def check_group(state, ans, ctx, codes):
    out = schemas.check(ans, schemas.GROUP)
    if errors_of(out):
        return out
    for code in codes:
        if code not in ans["rows"]:
            out.append(Problem("V01", f"rows.{code}", f"The answer for criterion {code} is missing.",
                               f"Add \"{code}\": {{ … }} inside \"rows\"."))
        else:
            out += check_row(state, code, ans["rows"][code], ctx, f"rows.{code}", with_schema=False)
    for code in ans["rows"]:
        if code not in codes:
            out.append(Problem("V01", f"rows.{code}", f"Criterion {code} is not part of this step.",
                               f"Delete it. This step covers: {', '.join(codes)}."))
    return out


# ---------------------------------------------------------------- consistency, synthesis, read-back (S)

def _recheck_rows(state, rows, codes, label):
    out = []
    trial = dict(state, rows=rows)
    for code in sorted(codes, key=ROW_ORDER.index):
        for pr in check_row(trial, code, rows[code], Ctx(), f"criterion {code} {label}",
                            with_schema=False, with_quotes=False):
            if pr.level == "error":
                out.append(pr)
    return out


def check_consistency(state, ans):
    out = schemas.check(ans, schemas.CONSISTENCY)
    if errors_of(out):
        return out, None
    rows = state["rows"]
    issues = ops.consistency_issues(rows)
    by_id = {i["id"]: i for i in issues}
    decided = set()
    for n, d in enumerate(ans["decisions"]):
        issue = by_id.get(d["issue"])
        path = f"decisions[{n}]"
        if not issue:
            out.append(Problem("V02", f"{path}.issue", f"\"{d['issue']}\" is not in the list of cases.",
                               "Use the case IDs from the task block: " + (", ".join(by_id) or "(no cases)") + "."))
            continue
        if d["issue"] in decided:
            out.append(Problem("V02", f"{path}.issue", f"Case {d['issue']} is decided twice.", "Keep one decision per case."))
        decided.add(d["issue"])
        allowed = ("move", "keep") if issue["type"] == "route" else ("merge", "keep")
        if d["action"] not in allowed:
            out.append(Problem("V01", f"{path}.action", f"\"{d['action']}\" is not possible for case {d['issue']}.",
                               f"Use \"{allowed[0]}\" or \"keep\"."))
        elif d["action"] == "merge" and d.get("keep_gap") not in issue["gaps"]:
            out.append(Problem("V01", f"{path}.keep_gap", "A merge needs the gap that stays.",
                               f"Add \"keep_gap\": \"{issue['gaps'][0]}\" or \"{issue['gaps'][1]}\"."))
        elif d["action"] == "move" and rows[issue["target"]]["score"] == "NA":
            out.append(Problem("V12", f"{path}.action", f"Criterion {issue['target']} is scored NA and cannot take a gap.",
                               "Use \"keep\" with a reason."))
    for iid in by_id:
        if iid not in decided:
            out.append(Problem("V01", "decisions", f"Case {iid} has no decision.",
                               f"Add {{\"issue\": \"{iid}\", \"action\": …, \"reason\": …}}."))
    if errors_of(out):
        return out, None
    new_rows, kept, touched = ops.apply_consistency(rows, issues, ans)
    for pr in _recheck_rows(state, new_rows, touched, "after the decisions"):
        pr.fix = (pr.fix + " " if pr.fix else "") + \
            "Adjust the criterion with \"score_changes\", or decide \"keep\" for the case that changed this criterion."
        out.append(pr)
    if ops.needs_calibration(new_rows) and not ans.get("calibration_justification"):
        low, n = ops.low_share(new_rows)
        out.append(Problem("V14", "calibration_justification",
                           f"{low} of {n} criteria are scored 1 or 0, but no calibration justification is given.",
                           "Re-read the calibration rules in the task block. Raise criteria with \"score_changes\" "
                           "where they were scored against perfection, or add \"calibration_justification\" "
                           "(one or two sentences on why the paper falls short this broadly)."))
    return out, (new_rows, kept)


def check_synthesis(state, syn, prefix=""):
    """V15–V17 on the synthesis part (critical, strengths, other_changes)."""
    out = []
    rows = state.get("rows", {})
    crit = syn.get("critical", [])
    if len(crit) > 3:
        out.append(Problem("V15", "critical", f"{len(crit)} critical issues are listed; the limit is 3.",
                           "Keep the 3 that most affect trust in the headline findings."))
    seen = set()
    for i, c in enumerate(crit):
        _, gap = ops.find_gap(rows, c["gap"])
        if gap is None:
            out.append(Problem("V15", f"critical[{i}].gap", f"\"{c['gap']}\" is not an existing gap.",
                               "Use a gap ID from the list of candidates in the task block."))
        elif gap["fix"]["size"] == "small" and not any(a.startswith("H") for a in gap.get("affects") or []):
            out.append(Problem("V15", f"critical[{i}].gap", f"Gap {c['gap']} has a small fix and bears on no headline "
                               "claim, so it cannot be a critical issue.",
                               "Remove it from \"critical\" and put it in \"other_changes\", or, if it changes how a "
                               "headline claim should be read, redo its criterion step and list that claim under \"affects\"."))
        if c["gap"] in seen:
            out.append(Problem("V15", f"critical[{i}].gap", f"Gap {c['gap']} is listed twice.", "List each gap once."))
        seen.add(c["gap"])
    if sorted(c["rank"] for c in crit) != list(range(1, len(crit) + 1)):
        out.append(Problem("V15", "critical", "The ranks must be 1, 2, 3 without gaps or repeats.",
                           f"Number the {len(crit)} critical issues from 1 to {len(crit)}."))
    strengths = syn.get("strengths", [])
    if not 2 <= len(strengths) <= 4:
        out.append(Problem("V16", "strengths", f"{len(strengths)} strengths are listed; 2–4 are required.",
                           "Choose 2–4 strength IDs from the task block."))
    if len(set(strengths)) != len(strengths):
        out.append(Problem("V16", "strengths", "A strength is listed twice.", "List each strength ID once."))
    for i, sid in enumerate(strengths):
        if ops.find_plus(rows, sid)[1] is None:
            out.append(Problem("V16", f"strengths[{i}]", f"\"{sid}\" is not an existing strength entry.",
                               "Use an ID such as A1+1 from the list of strengths in the task block."))
    other = syn.get("other_changes", [])
    if len(other) > 4:
        out.append(Problem("V17", "other_changes", f"{len(other)} other changes are listed; the limit is 4.",
                           "Keep the 4 most useful ones."))
    used = set()
    for i, ch in enumerate(other):
        for j, gid in enumerate(ch["gaps"]):
            if ops.find_gap(rows, gid)[1] is None:
                out.append(Problem("V17", f"other_changes[{i}].gaps[{j}]", f"\"{gid}\" is not an existing gap.",
                                   "Use gap IDs from the task block."))
            elif gid in seen:
                out.append(Problem("V17", f"other_changes[{i}].gaps[{j}]", f"Gap {gid} is already a critical issue.",
                                   "Remove it here; other changes go beyond the critical issues."))
            elif gid in used:
                out.append(Problem("V17", f"other_changes[{i}].gaps[{j}]", f"Gap {gid} is used in two changes.",
                                   "Use each gap in one change only."))
            used.add(gid)
    return out


def check_synthesis_answer(state, ans):
    out = schemas.check(ans, schemas.SYNTHESIS)
    if errors_of(out):
        return out
    return out + check_synthesis(state, ans) + check_texts(state, ans)


def check_sentence(state, ans):
    out = schemas.check(ans, schemas.SENTENCE)
    if errors_of(out):
        return out
    if ans.get("cannot_be_stated"):
        if not ans.get("reason"):
            out.append(Problem("V18", "reason", "\"cannot_be_stated\" is true but no reason is given.",
                               "Add \"reason\": one sentence on what prevents stating the paper in one sentence."))
    elif not ans.get("one_sentence"):
        out.append(Problem("V18", "one_sentence", "The sentence is missing.",
                           "Add \"one_sentence\" (≤ 45 words), or set \"cannot_be_stated\": true with a \"reason\"."))
    return out + check_texts(state, ans)


_READBACK_VALUE = {
    "edit_text": schemas.S(180, 10), "edit_fix_text": schemas.S(200, 10), "edit_why": schemas.S(220, 10),
    "set_score": schemas.E([0, 1, 2, 3]), "set_fix_size": schemas.E(["small", "moderate", "substantial"]),
    "edit_sentence": dict(schemas.S(400, 10), max_words=45),
}


def check_readback(state, ans):
    out = schemas.check(ans, schemas.READBACK)
    if errors_of(out):
        return out, None
    for i, ch in enumerate(ans["changes"]):
        out += schemas.check(ch.get("value"), _READBACK_VALUE[ch["op"]], f"changes[{i}].value")
        if ch["op"] != "edit_sentence" and not ch.get("target"):
            out.append(Problem("V01", f"changes[{i}].target", "This change needs a target.",
                               "Add \"target\": a criterion code (set_score) or an entry ID such as D3-1."))
        if isinstance(ch.get("value"), str):
            out += check_texts(state, {"text": ch["value"]}, f"changes[{i}]")
    if errors_of(out):
        return out, None
    rows, syn, touched, bad = ops.apply_readback(state["rows"], state["synthesis"], ans)
    for i, msg, fix in bad:
        out.append(Problem("V02", f"changes[{i}].target", msg, fix))
    out += _recheck_rows(state, rows, touched, "after the changes")
    trial = dict(state, rows=rows)
    out += check_synthesis(trial, syn)
    if ops.needs_calibration(rows) and not (state.get("consistency") or {}).get("calibration_justification"):
        out.append(Problem("V14", "changes", "After these changes more than a third of the criteria are scored 1 or 0.",
                           "Remove the set_score change that lowers a criterion."))
    return out, (rows, syn)


# ---------------------------------------------------------------- end rules (E)

def end_problems(state, view=None, rendered_text=None):
    """Rules checked at `finish` and `render --from`. Returns a list of Problem."""
    out = []
    rows = state.get("rows", {})
    for code in ROW_ORDER:
        if code not in rows:
            out.append(Problem("V01", f"rows.{code}", f"Criterion {code} has not been assessed.",
                               "Complete all criterion steps before finishing."))
    if errors_of(out):
        return out
    for code in ROW_ORDER:
        out += [p for p in check_row(state, code, rows[code], Ctx(), f"rows.{code}", with_quotes=False)
                if p.level == "error"]
    syn = state.get("synthesis") or {}
    out += check_synthesis(state, syn)
    sentence = syn.get("one_sentence")
    if not sentence:
        out.append(Problem("V18", "synthesis.one_sentence", "\"The paper in one sentence\" is missing.",
                           "Write the sentence (≤ 45 words) or state explicitly that it cannot be stated."))
    elif syn.get("one_sentence_stated", True) and count_words(sentence) > 45:
        out.append(Problem("V18", "synthesis.one_sentence", f"The sentence has {count_words(sentence)} words; the limit is 45.",
                           "Shorten it to at most 45 words."))
    cons = state.get("consistency") or {}
    kept = set(cons.get("kept", []))
    for issue in ops.consistency_issues(rows):
        if issue["key"] in kept:
            continue
        if issue["type"] == "route":
            out.append(Problem("V12", issue["gap"], f"Gap {issue['gap']} is in criterion {issue['row']}; the routing "
                               f"table assigns \"{issue['topic']}\" to criterion {issue['target']}.", level="warning"))
        else:
            a, b = issue["gaps"]
            out.append(Problem("V13", a, f"Gaps {a} and {b} are on the same page and say similar things.",
                               level="warning"))
    if ops.needs_calibration(rows) and not cons.get("calibration_justification"):
        low, n = ops.low_share(rows)
        out.append(Problem("V14", "consistency.calibration_justification",
                           f"{low} of {n} criteria are scored 1 or 0 and no calibration justification is recorded.",
                           "Redo the consistency step and either raise criteria or add the justification."))
    if view is not None and len(view["minor"]) > 8:
        out.append(Problem("V17", "minor", "More than 8 groups of smaller fixes.", "Reduce the minor items."))
    if rendered_text is not None:
        meta = state.get("meta", {})
        private = meta.get("private", {})
        ids = anon.find_identifiers(rendered_text, meta.get("redact", []), private.get("input_names", []))
        for hit in ids:
            out.append(Problem("V19", "scorecard", f"The criteria evaluation text contains identifying information: \"{hit}\".",
                               "Find the entry with `review.py preview`, then redo that step without the name."))
        for label in decision_words(rendered_text):
            out.append(Problem("V20", "scorecard", f"The criteria evaluation text contains decision language ({label}).",
                               "Find the entry with `review.py preview`, then redo that step and describe instead of judging."))
        for word in loaded_words(rendered_text):
            out.append(Problem("V21", "scorecard", f"The criteria evaluation uses the loaded word \"{word}\".", level="warning"))
    return out
