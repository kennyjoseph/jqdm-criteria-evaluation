"""Answer-file schemas as plain Python data, plus a small validator. No external library."""
from __future__ import annotations

import copy
import re

from .common import Problem, ROW_ORDER, count_words

LAYOUTS = ["standard", "results_first", "question_led", "research_note", "short_report", "inventory"]
SOURCE_KINDS = ["probability_survey", "platform_census", "vendor_collection", "convenience_sample",
                "keyword_collection", "tracking_panel", "other"]
MEASURE_KINDS = ["classifier", "llm_coding", "sentiment", "topic_model", "embedding", "lexicon",
                 "pretrained_tool", "manual_coding", "survey_item", "constructed_index",
                 "count_metric", "other"]
DESIGN_KINDS = ["descriptive", "event_study", "interrupted_time_series", "diff_in_diff",
                "discontinuity", "matched_control", "synthetic_control", "placebo_test",
                "shock_comparison", "causal_question", "matched_comparison", "other"]
# matched_comparison: units matched only to hold a variable fixed in a descriptive comparison.
CAUSAL_DESIGNS = set(DESIGN_KINDS) - {"descriptive", "matched_comparison", "other"}
FEATURE_STATUS = ["present", "partial", "absent", "not_applicable"]
MINOR_CATEGORIES = ["figures", "cross_references", "numbers", "citations", "wording", "other"]
SCORES = [0, 1, 2, 3, "NA"]


def S(max_len, min_len=3, **kw):
    return dict(t="str", max=max_len, min=min_len, **kw)


def E(values, **kw):
    return dict(t="enum", values=list(values), **kw)


def L(items, lo=0, hi=None, **kw):
    return dict(t="list", items=items, lo=lo, hi=hi, **kw)


def O(**fields):
    return dict(t="obj", fields=fields)


def ID(pattern, **kw):
    return dict(t="str", max=12, min=2, pattern=pattern, **kw)


def opt(schema):
    s = dict(schema)
    s["opt"] = True
    return s


PAGE = dict(t="int", lo=1)
QUOTE = dict(t="str", max=200, min=3, max_words=15)
DOC = opt(E(["manuscript", "appendix", "loi"]))
H_REF = ID(r"^H[1-5]$")

ORIENTATION = O(
    model=S(80, 2), title=S(300, 3), redact=L(S(120, 2), 0, 40), layout=E(LAYOUTS),
    paper_type=E(["full", "short"]),
    primary_aim=O(text=S(220, 10), page=PAGE, quote=opt(QUOTE)),
    secondary_aims=L(O(text=S(220, 10), page=PAGE, billing=E(["subordinate", "equal"])), 0, 5),
)
LOI = O(promises=L(O(id=ID(r"^P\d{1,2}$"), type=E(["question", "data", "analysis", "output"]),
                     text=S(220, 10), loi_page=PAGE), 1, 12))
CLAIMS = O(claims=L(O(id=H_REF, short=S(60, 5), text=S(220, 10), page=PAGE, quote=QUOTE,
                      status=E(["firm", "tentative"])), 2, 5))
DATA = O(
    data_sources=L(O(id=ID(r"^S\d{1,2}$"), kind=E(SOURCE_KINDS), text=S(220, 10), page=PAGE,
                     n=opt(S(60, 1))), 1, 8),
    subsets=opt(L(O(text=S(220, 10), page=PAGE, n=opt(S(60, 1))), 0, 8)),
    measures=L(O(id=ID(r"^M\d{1,2}$"), kind=E(MEASURE_KINDS), text=S(220, 10), page=PAGE,
                 supports=L(H_REF, 0, 5)), 0, 12),
    design=O(kind=E(DESIGN_KINDS), text=S(220, 10), page=PAGE,
             loi_promise=opt(dict(ID(r"^P\d{1,2}$"), nullable=True))),
)
FIGURES = O(map=L(O(figure=S(30, 3), supports=L(H_REF, 0, 5)), 0, 60))
FIX = O(kind=E(["writing", "analysis"]), size=E(["small", "moderate", "substantial"]), text=S(200, 10))
ROW = O(
    checks=L(S(200, 1), 0, 8),
    score=E(SCORES),
    na_reason=opt(dict(S(200, 5), nullable=True)),
    design_justification=opt(dict(S(200, 10), nullable=True)),
    plus=L(O(id=ID(r"^[LADPC]\d\+\d$"), text=S(180, 10), page=PAGE, doc=DOC), 0, 3),
    gaps=L(O(id=ID(r"^[LADPC]\d-\d$"), text=S(180, 10), page=PAGE, doc=DOC, quote=opt(QUOTE),
             affects=opt(L(ID(r"^(H[1-5]|P\d{1,2})$"), 0, 6)), topic=opt(dict(S(40, 3), nullable=True)),
             fix=FIX), 0, 3),
    features=dict(t="map", values=FEATURE_STATUS),
    minor=opt(L(O(category=E(MINOR_CATEGORIES), text=S(160, 5), page=opt(PAGE)), 0, 3)),
)
CONSISTENCY = O(
    decisions=L(O(issue=ID(r"^K\d{1,2}$"), action=E(["move", "merge", "keep"]),
                  reason=S(200, 10), keep_gap=opt(S(8, 4))), 0, 40),
    score_changes=opt(L(O(row=E(ROW_ORDER), score=E([0, 1, 2, 3]), reason=S(200, 10)), 0, 16)),
    calibration_justification=opt(dict(S(300, 20), nullable=True)),
)
SYNTHESIS = O(
    critical=L(O(gap=S(8, 4), rank=dict(t="int", lo=1, hi=3), why=S(220, 10)), 0, 3),
    strengths=L(S(8, 4), 2, 4),
    other_changes=L(O(gaps=L(S(8, 4), 1, 4), text=S(200, 10), raises=opt(L(E(ROW_ORDER), 0, 6))), 0, 4),
)
SENTENCE = O(one_sentence=opt(dict(S(400, 10), max_words=45)), cannot_be_stated=opt(dict(t="bool")),
             reason=opt(S(200, 10)))
READBACK = O(changes=L(O(
    op=E(["edit_text", "edit_fix_text", "edit_why", "set_score", "set_fix_size", "edit_sentence"]),
    target=opt(S(8, 2)), value=dict(t="any"), reason=S(200, 5)), 0, 5))
INVENTORY = O(orientation=ORIENTATION, loi=opt(LOI), claims=CLAIMS, data=DATA, figures=FIGURES)
GROUP = O(rows=dict(t="rowmap"))

BY_KIND = {"orientation": ORIENTATION, "loi": LOI, "claims": CLAIMS, "data": DATA,
           "figures": FIGURES, "row": ROW, "consistency": CONSISTENCY, "synthesis": SYNTHESIS,
           "sentence": SENTENCE, "readback": READBACK, "inventory": INVENTORY, "group": GROUP}

_TYPE_NAMES = {"str": "a text string", "int": "a whole number", "list": "a list [ … ]",
               "obj": "an object { … }", "bool": "true or false", "map": "an object { … }",
               "rowmap": "an object { … }"}


def limits(schema, path="") -> list:
    """Human-readable length and count limits of a schema, e.g. "gaps[].text: at most 180 characters"."""
    out, t = [], schema["t"]
    if t == "obj":
        for k, sub in schema["fields"].items():
            out += limits(sub, f"{path}.{k}" if path else k)
    elif t == "list":
        lo, hi = schema.get("lo", 0), schema.get("hi")
        if hi is not None and path != "checks":  # the number of checks is set by the check questions
            out.append(f"{path}: {lo}–{hi} entries")
        out += limits(schema["items"], f"{path}[]")
    elif t == "rowmap":
        out += limits(ROW, f"{path}.<code>" if path else "<code>")
    if schema is ROW:
        out.append("plus and gaps together: at most 3 (V08)")
    elif t == "str" and schema["max"] > 60 and not schema.get("pattern"):
        words = f", {schema['max_words']} words" if schema.get("max_words") else ""
        out.append(f"{path}: at most {schema['max']} characters{words}")
    return out


def check(value, schema, path=""):
    """Validate `value` against `schema`. Returns a list of Problem (rule V01)."""
    out = []

    def err(msg, fix):
        out.append(Problem("V01", path or "(top level)", msg, fix))

    t = schema["t"]
    if value is None and schema.get("nullable"):
        return out
    if t == "any":
        return out
    if t == "str":
        if not isinstance(value, str):
            err(f"Expected a text string, found {_show(value)}.", "Write the value in double quotes.")
            return out
        v = value.strip()
        if len(v) < schema.get("min", 0):
            err(f"The text is too short ({len(v)} characters, minimum {schema['min']}).",
                "Write a specific statement, or remove the entry.")
        if len(v) > schema["max"]:
            err(f"The text has {len(v)} characters; the limit is {schema['max']}.",
                f"Shorten it to one precise sentence of at most {schema['max']} characters.")
        if schema.get("max_words") and count_words(v) > schema["max_words"]:
            err(f"The text has {count_words(v)} words; the limit is {schema['max_words']}.",
                f"Cut it to at most {schema['max_words']} words.")
        if schema.get("pattern") and not re.match(schema["pattern"], v):
            err(f"\"{v}\" does not follow the ID pattern {schema['pattern']}.",
                "Use the ID pattern shown in the example of the task block.")
    elif t == "int":
        if isinstance(value, bool) or not isinstance(value, int):
            err(f"Expected a whole number, found {_show(value)}.", "Write a number without quotes, e.g. 7.")
        elif value < schema.get("lo", value) or (schema.get("hi") is not None and value > schema["hi"]):
            hi = schema.get("hi")
            err(f"{value} is outside the allowed range.",
                f"Use a number from {schema.get('lo')} to {hi}." if hi else f"Use a number ≥ {schema.get('lo')}.")
    elif t == "bool":
        if not isinstance(value, bool):
            err(f"Expected true or false, found {_show(value)}.", "Write true or false without quotes.")
    elif t == "enum":
        if value not in schema["values"] or isinstance(value, bool):
            allowed = ", ".join(_show(v) for v in schema["values"])
            err(f"{_show(value)} is not an allowed value.", f"Use exactly one of: {allowed}.")
    elif t == "list":
        if not isinstance(value, list):
            err(f"Expected a list, found {_show(value)}.", "Write a list in square brackets [ … ].")
            return out
        if len(value) < schema.get("lo", 0):
            err(f"The list has {len(value)} entries; at least {schema['lo']} are required.",
                f"Add entries until there are at least {schema['lo']}.")
        if schema.get("hi") is not None and len(value) > schema["hi"]:
            err(f"The list has {len(value)} entries; at most {schema['hi']} are allowed.",
                f"Keep the {schema['hi']} most important entries and delete the rest.")
        for i, item in enumerate(value):
            out += check(item, schema["items"], f"{path}[{i}]")
    elif t == "obj":
        if not isinstance(value, dict):
            err(f"Expected an object, found {_show(value)}.", "Write an object in curly braces { … }.")
            return out
        for name, sub in schema["fields"].items():
            sub_path = f"{path}.{name}" if path else name
            if name not in value:
                if not sub.get("opt"):
                    out.append(Problem("V01", sub_path, f"The required field \"{name}\" is missing.",
                                       f"Add \"{name}\" ({_TYPE_NAMES.get(sub['t'], 'a value')}) "
                                       "as shown in the example of the task block."))
                continue
            if value[name] is None and sub.get("opt"):
                continue
            out += check(value[name], sub, sub_path)
        for name in value:
            if name not in schema["fields"]:
                out.append(Problem("V01", f"{path}.{name}" if path else name,
                                   f"The field \"{name}\" is not part of this answer format.",
                                   f"Delete \"{name}\". Allowed fields: {', '.join(schema['fields'])}."))
    elif t == "map":
        if not isinstance(value, dict):
            err(f"Expected an object, found {_show(value)}.", "Write an object in curly braces { … }.")
            return out
        for k, v in value.items():
            if v not in schema["values"]:
                out.append(Problem("V01", f"{path}.{k}", f"{_show(v)} is not an allowed status.",
                                   "Use exactly one of: " + ", ".join(schema["values"]) + "."))
    elif t == "rowmap":
        if not isinstance(value, dict):
            err(f"Expected an object, found {_show(value)}.", "Write an object with one entry per criterion code.")
            return out
        for k, v in value.items():
            if k in ROW_ORDER:
                out += check(v, ROW, f"{path}.{k}")
    return out


def _show(v):
    if isinstance(v, str):
        return f"\"{v[:40]}\""
    if v is None:
        return "null"
    if isinstance(v, (dict, list)):
        return "an object" if isinstance(v, dict) else "a list"
    return str(v).lower() if isinstance(v, bool) else str(v)


def minimal(value, schema):
    """Copy of an example answer with every optional field removed and lists cut to their minimum."""
    t = schema["t"]
    if t == "obj" and isinstance(value, dict):
        return {k: minimal(value[k], sub) for k, sub in schema["fields"].items()
                if k in value and not sub.get("opt")}
    if t == "list" and isinstance(value, list):
        keep = max(1, schema.get("lo", 0))
        return [minimal(v, schema["items"]) for v in value[:keep]]
    if t == "rowmap" and isinstance(value, dict):
        return {k: minimal(v, ROW) for k, v in value.items()}
    return copy.deepcopy(value)
