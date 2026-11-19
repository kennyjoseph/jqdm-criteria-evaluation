"""Counts and mechanical checks: words, figures, tables, citations, cross-references, size line."""
from __future__ import annotations

import re

from . import refs
from .common import clip, count_words, fold
from .extract import zone_texts, line_zone_fn, find_abstract

CAP_RE = re.compile(
    r"^\s*(?:[#>*_]+\s*)?(Figure|Fig\.?|Abbildung|Abb\.?|Table|Tab\.?|Tabelle)\s+"
    r"([A-Z]{0,2}\.?\d{1,3})[a-z]?(?:\*\*|__)?\s*(?P<sep>[.:|—–-])?\s*(?P<rest>.*)$", re.I)
VERB_RE = re.compile(
    r"^(shows?|displays?|presents?|plots?|reports?|illustrates?|depicts?|compares?|summari[sz]es?|"
    r"gives?|provides?|lists?|contains?|is|are|was|were|and|or|also|further|zeigt|stellt|enthält)\b", re.I)
MENTION_RE = re.compile(
    r"\b(Figures?|Figs?\.?|Abbildung(?:en)?|Abb\.|Tables?|Tabellen?|Tab\.)\s+([A-Z]{0,2}\.?\d{1,3})[a-z]?\b")
# Words that put a figure or table outside the manuscript ("Supplementary Table 6", "Online Figure 2").
OUTSIDE_RE = re.compile(r"(?:supplementary|supplemental|online|appendix|\bSI|\bS\.?)\s*$", re.I)
# LaTeX's marker for an unresolved reference. Reported directly: it is almost never a false positive.
QQ_RE = re.compile(r"\b(Figures?|Figs?\.|Tables?|Sections?|Appendi(?:x|ces)|Equations?|Eqs?\.)\s*\?\?")
SECTION_REF_RE = re.compile(r"\b(?:Sections?|Abschnitt|Kapitel)\s+(\d{1,2}(?:\.\d{1,2})*)")
YEAR = r"(?:19|20)\d{2}[a-z]?"
NAME = r"[A-ZÀ-Þ][\w'’\-]+"
NARRATIVE_RE = re.compile(
    rf"({NAME})(?:\s+(?:et al\.?|(?:and|&|und)\s+{NAME}))?(?:['’]s)?,?\s*\(({YEAR})")
PAREN_RE = re.compile(rf"\(([^()]*?{YEAR}[^()]*)\)")
STOP = {fold(w) for w in """January February March April May June July August September October
November December Jan Feb Mar Apr Jun Jul Aug Sep Sept Oct Nov Dec Figure Fig Table Tab Section
Appendix Wave Study Model Panel Chapter Version Spring Summer Fall Autumn Winter In Since Until From
Between During After Before Through Census Survey See Cf Eg Ie As On At By For Of The And Or Q1 Q2 Q3
Q4 Data Dataset Sample Year Period Abbildung Tabelle Siehe Vgl Januar Februar März Juni Juli Oktober
Dezember Election Elections Release Update Supplement Note Source Sources""".split()}
# Only appendix-like material counts; a data or code repository (Dataverse, GitHub, OSF) is not an appendix.
APPX_HINT = re.compile(r"appendi(?:x|ces)|supplement(?:ary|al)? (?:material|information|file|table|figure|section)s?|"
                       r"\bSI\b|online material|\bAnhang\b", re.I)


def _kind(word: str) -> str:
    return "table" if word.lower().startswith("tab") else "figure"


def _label(kind: str, num: str) -> str:
    return ("Tab " if kind == "table" else "Fig ") + num.replace(".", "").upper()


def _continues_sentence(prev: str, line: str) -> bool:
    """A wrapped body sentence ("… is shown in" / "Figure 7. A 12-week …") rather than a caption: the line
    before is a long body line, ends mid-sentence, and is indented like this one."""
    p = prev.rstrip()
    if len(p.strip()) < 50 or not re.search(r"[a-z,;]$", p):
        return False
    indent = lambda x: len(x) - len(x.lstrip())
    return abs(indent(prev) - indent(line)) <= 8


def find_captions(pages, sections):
    """Figures and tables by caption pattern. One entry per label, first caption wins."""
    zone_of = line_zone_fn(sections)
    items, seen = [], set()
    for pno, page in enumerate(pages, 1):
        lines = page.split("\n")
        for i, line in enumerate(lines):
            m = CAP_RE.match(line)
            if not m:
                continue
            rest = m.group("rest").strip()
            if not m.group("sep") and (not rest or not rest[0].isupper() or VERB_RE.match(rest)):
                continue
            if m.group("sep") and VERB_RE.match(rest) and not rest[:1].isupper():
                continue
            if i and _continues_sentence(lines[i - 1], line):
                continue
            kind, zone = _kind(m.group(1)), zone_of(pno, i)
            label = _label(kind, m.group(2))
            num_plain = m.group(2).isdigit()
            key = (label, zone if num_plain else "x")
            if key in seen:
                continue
            seen.add(key)
            cap = [rest]
            for nxt in lines[i + 1:i + 6]:
                if not nxt.strip():
                    break
                cap.append(nxt.strip())
            in_main = zone == "main" and num_plain
            if not in_main and num_plain and any(x["label"] == label for x in items):
                label += " (appendix)"
            items.append({"label": label, "kind": kind, "page": pno, "main": in_main,
                          "caption": clip(" ".join(cap), 300)})
    return items


def _crossrefs(pages, sections, items, has_appendix_text):
    zone_of = line_zone_fn(sections)
    labels = {x["label"].replace(" (appendix)", "") for x in items}
    numbered = {m.group(1).rstrip(".") for s in sections
                for m in [re.match(r"^(\d{1,2}(?:\.\d{1,2})*)\.?\s", s["title"])] if m}
    broken, seen = [], set()
    for pno, page in enumerate(pages, 1):
        for i, line in enumerate(page.split("\n")):
            if zone_of(pno, i) == "references":
                continue
            for m in MENTION_RE.finditer(line):
                if OUTSIDE_RE.search(line[:m.start()]):
                    continue
                num = m.group(2).replace(".", "").upper()
                label = _label(_kind(m.group(1)), num)
                if label in labels or label in seen:
                    continue
                if not num.isdigit() and not has_appendix_text:
                    continue  # appendix item, appendix not available: cannot check
                seen.add(label)
                word = "Table" if label.startswith("Tab") else "Figure"
                broken.append({"ref": f"{word} {num}", "page": pno})
            if len(numbered) >= 3:
                for m in SECTION_REF_RE.finditer(line):
                    num = m.group(1)
                    if num not in numbered and ("S" + num) not in seen:
                        seen.add("S" + num)
                        broken.append({"ref": f"Section {num}", "page": pno})
    return broken


def _unresolved_markers(pages, sections):
    """"Figure ??", "Section ??" and the like: references LaTeX could not resolve."""
    zone_of = line_zone_fn(sections)
    found = []
    for pno, page in enumerate(pages, 1):
        for i, line in enumerate(page.split("\n")):
            if zone_of(pno, i) == "references":
                continue
            found += [f"{m.group(1)} ?? (p. {pno})" for m in QQ_RE.finditer(line)]
    return found


def _ref_entries(ref_text: str):
    entries, cur, prev_blank = [], "", True
    for line in ref_text.split("\n"):
        s = line.strip()
        if not s:
            prev_blank = True
            continue
        s = re.sub(r"^(?:[-*•]\s+|\[\d+\]\s*|\d+\.\s+)", "", s)
        starts = re.match(rf"^{NAME}[,\s]", s) or re.match(r"^(?:van|von|de|di|del|der)\s", s, re.I)
        if cur and starts and (prev_blank or re.search(YEAR, cur)):
            entries.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
        prev_blank = False
    if cur:
        entries.append(cur)
    out = []
    for e in entries:
        y = re.search(YEAR, e)
        n = re.search(NAME, e)
        if y and n:
            out.append({"surname": n.group(0).strip(",."), "year": y.group(0), "head": fold(e[:160]),
                        "years": set(re.findall(YEAR, e))})
    return out


def _citations(text: str):
    cites = set()
    for m in NARRATIVE_RE.finditer(text):
        if fold(m.group(1)) not in STOP:
            cites.add((m.group(1), m.group(2)))
    for m in PAREN_RE.finditer(text):
        for part in m.group(1).split(";"):
            years = re.findall(YEAR, part)
            names = [n for n in re.findall(NAME, part) if fold(n) not in STOP and len(n) > 1]
            if years and names and re.search(rf"{NAME}[^;]*?{YEAR}", part):
                for y in years:
                    cites.add((names[0].rstrip("'’s") if names[0].endswith(("'s", "’s")) else names[0], y))
    return sorted(cites)


# Switched off 2026-11-16: the matcher produced many false positives on published papers (et al./&
# forms, line-break hyphens, hashtags, wrong years), and its output leaked author surnames into the
# criteria evaluation. Keep the code for a later, more reliable version.
CITATION_CHECK = False


def check_citations(body_text: str, ref_text: str):
    """Return (citations_missing_in_refs, refs_never_cited, references_found)."""
    entries = _ref_entries(ref_text)
    if not entries:
        return [], [], False
    missing = []
    for name, year in _citations(body_text):
        f = fold(name)
        if not any(f in e["head"] and year in e["years"] for e in entries):
            missing.append(f"{name} {year}")
    body_f, never = fold(body_text), []
    for e in entries:
        pat = re.escape(fold(e["surname"])) + r"[^.;]{0,90}?" + re.escape(e["year"][:4])
        if not re.search(pat, body_f):
            never.append(f"{e['surname']} {e['year']}")
    return missing, sorted(set(never)), True


def _abstract_words(pages, sections):
    found = find_abstract(pages, sections)
    return count_words(found[1]) if found else None


def compute(pages, sections, appendix_pages=None) -> dict:
    """All metrics for metrics.json. `items` (figures and tables with captions) is included."""
    zones = zone_texts(pages, sections)
    items = find_captions(pages, sections)
    if appendix_pages:
        for it in find_captions(appendix_pages, []):
            if not any(x["label"] == it["label"] for x in items):
                it.update(main=False, doc="appendix")
                items.append(it)
    body = zones["main"] + "\n" + zones["appendix"]
    missing, never, refs_found = check_citations(body, zones["references"])
    if not CITATION_CHECK:
        missing, never = [], []
    has_appx_text = bool(appendix_pages) or count_words(zones["appendix"]) > 100
    if has_appx_text:
        appendix = "present"
    elif APPX_HINT.search(zones["main"]):
        appendix = "referenced_elsewhere"
    else:
        appendix = "none"
    return {
        "words_main": count_words(re.sub(r"(?m)^#+\s*", "", zones["main"])),
        "figures": sum(1 for x in items if x["kind"] == "figure" and x["main"]),
        "tables": sum(1 for x in items if x["kind"] == "table" and x["main"]),
        "abstract_words": _abstract_words(pages, sections),
        "appendix": appendix,
        "pages": len(pages),
        "references_found": refs_found,
        "citations_missing_in_refs": missing,
        "refs_never_cited": never,
        # Candidates only: shown to the model at P5, which reports the real ones as minor items.
        "broken_crossrefs": [f"{b['ref']} (p. {b['page']})" for b in
                             _crossrefs(pages, sections, items, has_appx_text)],
        # Unambiguous: rendered directly under "Smaller fixes".
        "unresolved_markers": _unresolved_markers(pages, sections),
        "items": items,
    }


def _fmt(n: int) -> str:
    return f"{n:,}"


def size_summary(metrics: dict, paper_type: str):
    """Return (size line, comparison with the length norms). Entirely rule-based."""
    if not metrics or metrics.get("words_main") is None:
        return "Not counted (no manuscript text was available to the scripts).", ""
    norms = refs.journal()["norms"]
    words = int(round(metrics["words_main"] / 100.0)) * 100
    f, t = metrics["figures"], metrics["tables"]
    appx = {"present": "appendix present", "referenced_elsewhere": "appendix referenced elsewhere",
            "none": "no appendix"}[metrics.get("appendix", "none")]
    line = (f"~{_fmt(words)} words main text · {f} figure{'s' if f != 1 else ''} · "
            f"{t} table{'s' if t != 1 else ''} · {appx}")
    kind = "short reports and research notes" if paper_type == "short" else "full papers"
    lo, hi = norms["short_words" if paper_type == "short" else "full_words"]
    w = metrics["words_main"]
    pos = "within" if lo <= w <= hi else ("above" if w > hi else "below")
    parts = [f"Main-text length is {pos} the typical range for {kind} (about {_fmt(lo)}–{_fmt(hi)} words)"]
    for name, n, (lo2, hi2) in (("figures", f, norms["figures"]), ("tables", t, norms["tables"])):
        if not lo2 <= n <= hi2:
            parts.append(f"the number of {name} is {'above' if n > hi2 else 'below'} the typical {lo2}–{hi2}")
    aw = metrics.get("abstract_words")
    if aw is not None and not norms["abstract_words"][0] <= aw <= norms["abstract_words"][1]:
        lo3, hi3 = norms["abstract_words"]
        parts.append(f"the abstract ({aw} words) is {'above' if aw > hi3 else 'below'} the typical {lo3}–{hi3} words")
    return line, "; ".join(parts) + ". These ranges are context, not rules."
