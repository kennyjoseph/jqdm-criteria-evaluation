"""Anonymity: find identifying strings on the title page and check output text for them."""
from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
INST_RE = re.compile(
    r"\b(?:Universit[yäé]\w*|Universi[dt]a[dt]\w*|Institut[eo]?|College|School of|Department of|"
    r"Hochschule|Cent(?:er|re) for|Laborator(?:y|ies)|Faculty of|Fakultät|Lehrstuhl|Académie|Academy)\b")
GENERIC_STEMS = {"manuscript", "paper", "draft", "submission", "article", "main", "loi",
                 "appendix", "supplement", "letter", "final", "revision", "document"}


def detect_candidates(pages):
    """Email addresses and institution lines on the title page (before the abstract)."""
    head = "\n".join(pages[:1])
    cut = re.search(r"(?mi)^\s*(?:#+\s*)?(abstract|introduction|zusammenfassung)\b", head)
    if cut:
        head = head[:cut.start()]
    head = "\n".join(head.split("\n")[:40])
    emails = sorted(set(EMAIL_RE.findall("\n".join(pages[:2]))))
    inst = []
    for line in head.split("\n"):
        s = " ".join(line.strip(" *#,;").split())
        if s and INST_RE.search(s) and len(s) <= 120 and s not in inst:
            inst.append(s)
    return {"emails": emails, "institutions": inst[:8]}


def file_tokens(names):
    """Strings derived from input file names that must not appear in the output."""
    out = []
    for name in names:
        if not name:
            continue
        out.append(name)
        stem = name.rsplit(".", 1)[0]
        if (len(stem) >= 6 and stem.lower() not in GENERIC_STEMS
                and re.search(r"[_\-\d ]", stem)):
            out.append(stem)
    return out


NAME_TOKEN = re.compile(r"^[A-ZÀ-Þ][\w'’\-]*\.?$")
PARTICLES = {"van", "von", "de", "der", "den", "da", "di", "du", "del", "la", "le", "al", "el", "bin", "ten", "ter"}


def surname(entry: str):
    """The surname of a person's name in `redact` ("Jennifer Golbeck" → "Golbeck"), or None for
    institutions and single words. Footnote digits are dropped ("GOLBECK1"); all-caps is title-cased."""
    if "," in entry.rstrip(", "):   # "Hertie School, Berlin, Germany" is an affiliation, not a person
        return None
    words = [re.sub(r"\d+$", "", w).strip(",*") for w in entry.split()]
    words = [w for w in words if w]
    if not 2 <= len(words) <= 5 or INST_RE.search(entry) or EMAIL_RE.search(entry):
        return None
    if not all(NAME_TOKEN.match(w if not w.isupper() else w.title()) or w.lower() in PARTICLES for w in words):
        return None
    last = words[-1]
    last = "-".join(p.capitalize() for p in last.split("-")) if last.isupper() else last
    return last if len(last) >= 3 and not last.endswith(".") else None


def find_identifiers(text: str, redact=(), file_names=()):
    """Return the identifying strings that occur in `text`: each redact entry (any case), and the
    surname of each person in it (exact case, so "Long" does not match "long")."""
    hits = []
    for name in redact:
        name = name.strip()
        if len(name) >= 2 and re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", text, re.I):
            hits.append(name)
            continue
        last = surname(name)
        if last and re.search(r"(?<!\w)(?:" + re.escape(last) + "|" + re.escape(last.upper()) + r")(?!\w)", text):
            hits.append(last)
    hits += sorted(set(EMAIL_RE.findall(text)))
    low = text.lower()
    hits += [t for t in file_tokens(file_names) if t.lower() in low]
    return hits
