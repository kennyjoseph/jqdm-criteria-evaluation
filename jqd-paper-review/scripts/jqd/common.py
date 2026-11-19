"""Shared constants and small helpers."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

SKILL_VERSION = "2026.11.17"  # date of the last change to criteria, anchors or rules
SCHEMA_VERSION = "2.0"

SKILL_DIR = Path(__file__).resolve().parent.parent.parent
REF_DIR = SKILL_DIR / "references"
ASSET_DIR = SKILL_DIR / "assets"

ROW_ORDER = ["L1", "A1", "A2", "D1", "D2", "D3", "P1", "P2", "P3", "P4", "P5",
             "C1", "C2", "C3", "C4", "C5"]
GROUPS = [
    ("L", "Letter of Inquiry", ["L1"]),
    ("A", "Aim and framing", ["A1", "A2"]),
    ("D", "Data", ["D1", "D2", "D3"]),
    ("P", "Presentation and analysis", ["P1", "P2", "P3", "P4", "P5"]),
    ("C", "Contribution and claims", ["C1", "C2", "C3", "C4", "C5"]),
]
SCORE_LABEL = {3: "Fully", 2: "Mostly", 1: "Partly", 0: "Not met", "NA": "N/A"}
SIZE_RANK = {"small": 0, "moderate": 1, "substantial": 2}
DOCS = ("manuscript", "loi", "appendix")
MARKER_RE = re.compile(r"^⟨p\.(\d+)⟩\s*$", re.M)


class Problem:
    """One validation finding. level is 'error' or 'warning'."""

    def __init__(self, rule, path, msg, fix="", level="error"):
        self.rule, self.path, self.msg, self.fix, self.level = rule, path, msg, fix, level

    def short(self):
        where = f" · {self.path}" if self.path else ""
        return f"{self.rule}{where}: {self.msg}"

    def __repr__(self):
        return f"<{self.level} {self.short()}>"


def errors_of(problems):
    return [p for p in problems if p.level == "error"]


def warnings_of(problems):
    return [p for p in problems if p.level == "warning"]


def read_text(path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def write_text(path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read_json(path):
    return json.loads(read_text(path))


def dump_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


WORD_RE = re.compile(r"\d+(?:[.,]\d+)*%?|[^\W_]+(?:[-'’][^\W_]+)*")   # "9.2" and "122,079" are one word


def count_words(text: str) -> int:
    return len(WORD_RE.findall(text))


def fold(text: str) -> str:
    """Lower-case, strip diacritics. For tolerant name comparison."""
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower()


def clip(text: str, n: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


SENT_RE = re.compile(r"(?<=[.!?])[\"”’)\]]?\s+(?=[A-ZÄÖÜ\"“(\[0-9])")


ABBREV_RE = re.compile(r"(?:\bet al|\be\.g|\bi\.e|\bcf|\bvs|\bFig|\bTab|\bNo|\bca|\bapprox|\bz\.B|\bvgl|\bAbb)\.$", re.I)


def split_sentences(text: str):
    parts = [s.strip() for s in SENT_RE.split(" ".join(text.split())) if s.strip()]
    out = []
    for part in parts:
        if out and ABBREV_RE.search(out[-1]):
            out[-1] += " " + part
        else:
            out.append(part)
    return out


LIGATURES = {ord(k): v for k, v in {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}.items()}
_HYPHEN_BREAK = re.compile(r"([^\W\d_]{2})-\s+(?!(?:and|or|to|und|oder|bis)\b)([^\W\d_A-ZÀ-Þ])")


def dehyphenate(text: str) -> str:
    """Join words split at a line break ("suffi- ciently" → "sufficiently"). Keeps "pre- and post-"."""
    return _HYPHEN_BREAK.sub(r"\1\2", text.translate(LIGATURES))


def page_sentences(page: str):
    """Sentences of a page as (first line number of the paragraph, sentence).
    Paragraphs are split at blank lines first, so headings stay separate."""
    out, buf, start = [], [], 0
    lines = page.split("\n")
    for i, line in enumerate(lines + [""]):
        if line.strip():
            if not buf:
                start = i
            buf.append(line.strip())
        elif buf:
            out += [(start, s) for s in split_sentences(dehyphenate(" ".join(buf)))]
            buf = []
    return out


def group_of(row: str):
    for key, title, rows in GROUPS:
        if row in rows:
            return key, title
    raise KeyError(row)
