"""Load reference files: row files, anchors, scale, journal profile, routing, step instructions."""
from __future__ import annotations

import json
import re
from functools import lru_cache

from .common import REF_DIR, ASSET_DIR, read_text, read_json


def _scalar(raw: str):
    raw = raw.strip()
    if raw == "":
        return ""
    try:
        return json.loads(raw)
    except ValueError:
        if raw.startswith("[") and raw.endswith("]"):
            return [x.strip().strip('"') for x in raw[1:-1].split(",") if x.strip()]
        return raw


def _strip_comment(line: str) -> str:
    """Remove a trailing '# comment' that is outside double quotes."""
    out, quoted, prev = [], False, ""
    for ch in line:
        if ch == '"' and prev != "\\":
            quoted = not quoted
        if ch == "#" and not quoted and (not out or out[-1] in " \t"):
            break
        out.append(ch)
        prev = ch
    return "".join(out).rstrip()


def parse_frontmatter(text: str):
    """Tiny frontmatter reader. Supports 'key: value', inline lists '[a, b]',
    and one level of indented '- item' lists or 'subkey: value' maps.
    Quoted strings follow JSON rules. Returns (dict, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end < 0:
        return {}, text
    head, body = text[3:end], text[end + 4:].lstrip("\n")
    data, key = {}, None
    for raw in head.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indented = line[0] in " \t"
        s = line.strip()
        if not indented:
            k, _, v = s.partition(":")
            key = k.strip()
            data[key] = _scalar(v) if v.strip() else None
        elif key is not None:
            if s.startswith("- "):
                if not isinstance(data[key], list):
                    data[key] = []
                data[key].append(_scalar(s[2:]))
            else:
                if not isinstance(data[key], dict):
                    data[key] = {}
                k, _, v = s.partition(":")
                data[key][k.strip()] = _scalar(v)
    for k, v in data.items():
        if v is None:
            data[k] = []
    return data, body


def sections(body: str):
    """Split a Markdown body by '## ' headings → {heading: text}."""
    out, name, buf = {}, None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if name is not None:
                out[name] = "\n".join(buf).strip()
            name, buf = line[3:].strip(), []
        elif name is not None:
            buf.append(line)
    if name is not None:
        out[name] = "\n".join(buf).strip()
    return out


@lru_cache(maxsize=None)
def row(code: str) -> dict:
    meta, body = parse_frontmatter(read_text(REF_DIR / "criteria" / f"{code}.md"))
    secs = sections(body)
    questions = re.findall(r"^\d+\.\s+(.*)$", secs.get("Check questions", ""), re.M)
    feats = meta.get("features") or {}
    return {
        "row": code, "title": meta["title"], "group": meta["group"],
        "depends_on": list(meta.get("depends_on") or []),
        "search_hints": list(meta.get("search_hints") or []),
        "features": dict(feats), "not_here": list(meta.get("not_here") or []),
        "body": body.strip(), "questions": questions,
    }


@lru_cache(maxsize=None)
def anchors(code: str, include_drafts: bool = False) -> str:
    """Calibration anchors of a row. Anchors are used only once the editors have agreed them
    (frontmatter `status: agreed`); drafts are returned only on request."""
    path = REF_DIR / "calibration" / f"{code}.md"
    if not path.is_file():
        return ""
    meta, body = parse_frontmatter(read_text(path))
    if meta.get("status") != "agreed" and not include_drafts:
        return ""
    return body.strip()


@lru_cache(maxsize=None)
def scale() -> dict:
    meta, body = parse_frontmatter(read_text(REF_DIR / "scale.md"))
    secs = sections(body)
    return {"loaded_words": list(meta.get("loaded_words") or []),
            "short": secs["Scale (short version)"],
            "calibration": secs["Calibration rules"],
            "sections": secs}


@lru_cache(maxsize=None)
def journal() -> dict:
    meta, body = parse_frontmatter(read_text(REF_DIR / "journal.md"))
    return {"layouts": dict(meta["layouts"]), "norms": dict(meta["norms"]),
            "sections": sections(body)}


@lru_cache(maxsize=None)
def routing() -> dict:
    return read_json(REF_DIR / "routing.json")["topics"]


def topics_for(row_code: str):
    return [t for t, d in routing().items() if d["row"] == row_code]


STEP_FILES = {
    "init": "00-setup.md", "orientation": "01-orientation.md", "loi": "02-loi-promises.md",
    "claims": "03-headline-claims.md", "data": "04-data-and-measures.md",
    "figures": "05-figure-mapping.md", "row": "06-21-criterion-assessment.md",
    "consistency": "22-consistency.md", "synthesis": "23-synthesis.md",
    "sentence": "24-one-sentence.md", "readback": "25-read-back.md", "finish": "26-finish.md",
    "inventory": "compact-inventory.md", "group": "compact-group.md",
}


@lru_cache(maxsize=None)
def step(kind: str) -> dict:
    """Instruction file of a step kind → {'Task': ..., 'Rules': ..., 'Fields': ...}."""
    _, body = parse_frontmatter(read_text(REF_DIR / "steps" / STEP_FILES[kind]))
    return sections(body)


@lru_cache(maxsize=None)
def example(kind: str):
    name = {"row": "criterion"}.get(kind, kind)
    return read_json(ASSET_DIR / "examples" / f"{name}.json")
