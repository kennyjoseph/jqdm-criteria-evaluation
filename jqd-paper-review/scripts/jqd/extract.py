"""PDF / DOCX / Markdown / text → page texts with markers ⟨p.N⟩, headings and zones."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from .common import LIGATURES, MARKER_RE, read_text

SYNTHETIC_PAGE_CHARS = 3000


class ExtractError(Exception):
    def __init__(self, msg, fix):
        super().__init__(msg)
        self.msg, self.fix = msg, fix


# ---------------------------------------------------------------- readers

def _pdf_pdftotext(path: Path):
    exe = shutil.which("pdftotext")
    if not exe or os.environ.get("JQD_NO_PDFTOTEXT"):
        return None
    try:
        res = subprocess.run([exe, "-layout", "-enc", "UTF-8", str(path), "-"],
                             capture_output=True, timeout=180)
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    pages = res.stdout.decode("utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


def _pdf_pypdf(path: Path):
    vendor = str(Path(__file__).resolve().parent / "vendor")
    if vendor not in sys.path:
        sys.path.insert(0, vendor)
    try:
        from pypdf import PdfReader  # type: ignore
        reader = PdfReader(str(path))
        return [(page.extract_text() or "") for page in reader.pages]
    except Exception as exc:  # pypdf raises many types; all mean "unreadable"
        raise ExtractError(f"The PDF could not be read ({type(exc).__name__}).",
                           "Provide an unencrypted PDF, a DOCX or a text version.")


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _docx(path: Path):
    try:
        with zipfile.ZipFile(path) as zf:
            root = ET.fromstring(zf.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ET.ParseError):
        raise ExtractError("The DOCX file could not be opened.",
                           "Save the document again as .docx or export it as PDF.")
    pages, cur = [], []

    def para_text(p):
        out, breaks = [], 0
        for el in p.iter():
            if el.tag == W + "t":
                out.append(el.text or "")
            elif el.tag == W + "tab":
                out.append(" ")
            elif el.tag == W + "br":
                if el.get(W + "type") == "page":
                    breaks += 1
                else:
                    out.append(" ")
            elif el.tag == W + "lastRenderedPageBreak":
                breaks += 1
        return "".join(out).strip(), breaks

    def heading_level(p):
        style = p.find(f"{W}pPr/{W}pStyle")
        if style is not None:
            m = re.match(r"(?:heading|berschrift|überschrift)\s*(\d)", style.get(W + "val", ""), re.I)
            if m:
                return int(m.group(1))
            if style.get(W + "val", "").lower() == "title":
                return 1
        return 0

    body = root.find(W + "body")
    for el in (body if body is not None else []):
        if el.tag == W + "p":
            text, breaks = para_text(el)
            if breaks and cur:
                pages.append("\n".join(cur))
                cur = []
            if text:
                lvl = heading_level(el)
                cur.append(("#" * lvl + " " if lvl else "") + text)
                cur.append("")
        elif el.tag == W + "tbl":
            for tr in el.iter(W + "tr"):
                cells = []
                for tc in tr.findall(W + "tc"):
                    cells.append(" ".join(para_text(p)[0] for p in tc.iter(W + "p")).strip())
                cur.append(" | ".join(cells))
            cur.append("")
    if cur:
        pages.append("\n".join(cur))
    return pages


def _paginate(text: str):
    """Split text without page breaks into pseudo-pages at paragraph boundaries."""
    pages, cur, size = [], [], 0
    for para in re.split(r"\n\s*\n", text):
        if size + len(para) > SYNTHETIC_PAGE_CHARS and cur:
            pages.append("\n\n".join(cur))
            cur, size = [], 0
        cur.append(para)
        size += len(para)
    if cur:
        pages.append("\n\n".join(cur))
    return pages


# ---------------------------------------------------------------- cleaning

NUM_LINE = re.compile(r"^\s*(?:[-–—]\s*)?(?:page\s+|seite\s+)?(\d{1,4})(?:\s*(?:/|of|von)\s*\d+)?(?:\s*[-–—])?\s*$", re.I)


def _edge_indices(lines, k=2):
    idx = [i for i, l in enumerate(lines) if l.strip()]
    return idx[:k], idx[-k:]


def _clean(pages):
    """Remove running headers/footers and page-number lines. Return (pages, page_offset)."""
    split = [p.replace("\r\n", "\n").replace("\r", "\n").split("\n") for p in pages]
    n = len(split)
    offsets, norm_count = [], Counter()
    for lines in split:
        top, bottom = _edge_indices(lines)
        for i in set(top + bottom):
            norm_count[re.sub(r"\d+", "#", lines[i].strip())] += 1
    running = {s for s, c in norm_count.items()
               if n >= 4 and c >= max(3, n // 2) and len(s) < 100 and s != "#"}
    cleaned = []
    for pno, lines in enumerate(split, 1):
        top, bottom = _edge_indices(lines)
        drop = set()
        for i in set(top + bottom):
            s = lines[i].strip()
            m = NUM_LINE.match(s)
            if m and n >= 3:
                offsets.append(int(m.group(1)) - pno)
                drop.add(i)
            elif re.sub(r"\d+", "#", s) in running:
                drop.add(i)
                nums = re.findall(r"(?<![\d.])\d{1,4}(?![\d.])", s)
                if len(nums) == 1:
                    offsets.append(int(nums[0]) - pno)
        out = []
        for i, l in enumerate(lines):
            if i in drop:
                continue
            l = re.sub(r"(?<=\S) {3,}", "  ", l.rstrip().replace("\u00ad", "").translate(LIGATURES))
            out.append(l)
        indent = min((len(l) - len(l.lstrip()) for l in out if l.strip()), default=0)
        text = "\n".join(l[indent:] if l.strip() else "" for l in out)
        cleaned.append(re.sub(r"\n{3,}", "\n\n", text).strip("\n"))
    page_offset = None
    if offsets:
        value, count = Counter(offsets).most_common(1)[0]
        if count >= max(3, int(0.6 * n)):
            page_offset = value
    return cleaned, page_offset


# ---------------------------------------------------------------- public

def extract_file(path) -> dict:
    """Read one input file. Returns {'pages', 'synthetic', 'page_offset', 'tool', 'warnings'}."""
    path = Path(path)
    if not path.is_file():
        raise ExtractError(f"Input file not found: {path.name}", "Check the path and run init again.")
    ext = path.suffix.lower()
    synthetic, tool = False, ext.lstrip(".")
    if ext == ".pdf":
        pages = _pdf_pdftotext(path)
        tool = "pdftotext"
        if not pages or not any(p.strip() for p in pages):
            pages, tool = _pdf_pypdf(path), "pypdf"
    elif ext == ".docx":
        pages = _docx(path)
        if len(pages) <= 1:
            pages, synthetic = _paginate("\n".join(pages)), True
    elif ext in (".md", ".markdown", ".txt", ".text", ".tex", ""):
        text = read_text(path)
        if "\f" in text:
            pages = text.split("\f")
        else:
            pages, synthetic = _paginate(text), True
    else:
        raise ExtractError(f"File type '{ext}' is not supported.",
                           "Provide the document as PDF, DOCX, Markdown or plain text.")
    empty = [i for i, p in enumerate(pages, 1) if len(re.sub(r"\s", "", p)) < 40]
    if not pages or len(empty) > len(pages) / 2:
        raise ExtractError(
            f"{len(empty)} of {len(pages)} pages contain no text (scanned or image-only document).",
            "Please provide a text version or an OCR'd PDF.")
    pages, offset = _clean(pages)
    warnings = []
    if empty:
        warnings.append("Pages without text (scanned or figure-only): " + ", ".join(map(str, empty)))
    if synthetic:
        warnings.append("The input has no page breaks; page numbers are positions in the extracted text.")
    return {"pages": pages, "synthetic": synthetic, "page_offset": None if synthetic else offset,
            "tool": tool, "warnings": warnings}


def to_marked(pages) -> str:
    return "".join(f"⟨p.{i}⟩\n{p}\n" for i, p in enumerate(pages, 1))


def load_marked(path):
    """Read a marked text file back into a list of page texts. Missing file → None."""
    path = Path(path)
    if not path.is_file():
        return None
    parts = MARKER_RE.split(read_text(path))
    return [parts[i].strip("\n") for i in range(2, len(parts), 2)]


# ---------------------------------------------------------------- headings and zones

KNOWN = (r"abstract|summary|introduction|background|related work|literature review|prior work|"
         r"data|methods?|data (?:and|&) methods?|materials (?:and|&) methods|methodology|"
         r"measures|measurement|analysis|results?|findings|discussion|limitations|"
         r"conclusions?|discussion (?:and|&) conclusions?|concluding remarks|"
         r"acknowledge?ments?|funding|data (?:and code )?availability(?: statement)?|"
         r"keywords|ethics(?: statement)?|competing interests|"
         r"zusammenfassung|einleitung|hintergrund|daten|methoden?|ergebnisse|diskussion|fazit|danksagung")
REFS = r"references|bibliography|works cited|literature cited|reference list|literatur|literaturverzeichnis"
APPX = r"appendix|appendices|supplement|supplementary|online appendix|supporting information|anhang"
NUM = r"(?:\d{1,2}(?:\.\d{1,2}){0,3}\.?\s+)?"
RE_MD = re.compile(r"^(#{1,4})\s+(.+?)\s*#*$")
RE_REFS = re.compile(rf"^{NUM}(?:{REFS})\s*:?$", re.I)
RE_APPX = re.compile(rf"^{NUM}(?:{APPX})\b.{{0,70}}$", re.I)
RE_KNOWN = re.compile(rf"^{NUM}(?:{KNOWN})\s*[:.]?$", re.I)
RE_NUMBERED = re.compile(r"^(\d{1,2}(?:\.\d{1,2}){0,3})\.?\s+([A-ZÄÖÜ][^\t]{1,80})$")
RE_CAPTION_START = re.compile(r"^(?:figure|fig\.?|table|tab\.?|abbildung|abb\.?|tabelle)\s+[A-Z]?\d", re.I)


def detect_sections(pages):
    """Find headings. Returns list of {title, level, page, line, zone, weak}."""
    found, zone = [], "main"
    for pno, page in enumerate(pages, 1):
        lines = page.split("\n")
        for i, raw in enumerate(lines):
            s = raw.strip()
            if not s or len(s) > 90:
                continue
            level, title, weak = 0, s, False
            m = RE_MD.match(s)
            if m:
                level, title = len(m.group(1)), m.group(2).strip()
            if RE_CAPTION_START.match(title):
                continue
            is_refs, is_appx = bool(RE_REFS.match(title)), bool(RE_APPX.match(title))
            if is_appx and not level and (title[-1:] in ".,;" or len(title.split()) > 9):
                is_appx = False
            if not level:
                if is_refs or is_appx or RE_KNOWN.match(title):
                    level = 1
                else:
                    m = RE_NUMBERED.match(s)
                    if (m and s[-1] not in ".,;:" and len(s.split()) <= 12
                            and "  " not in s and sum(c.isdigit() for c in m.group(2)) <= 4):
                        level = m.group(1).count(".") + 1
                    else:
                        before = i == 0 or not lines[i - 1].strip()
                        after = i == len(lines) - 1 or not lines[i + 1].strip()
                        words = s.split()
                        alpha = sum(c.isalpha() or c.isspace() for c in s) / len(s)
                        if (before and after and 2 <= len(words) <= 12 and 4 <= len(s) <= 70
                                and s[0].isupper() and s[-1] not in ".,;:)" and alpha >= 0.85
                                and not re.search(r"https?:|www\.|@", s)
                                and not (pno == 1 and s.isupper())
                                and "  " not in s and "," not in s and ": " not in s):
                            level, weak = 2, True
            if not level:
                continue
            if is_refs:
                zone = "references"
            elif is_appx and (pno > 1 or i > 5):
                zone = "appendix"
            found.append({"title": title, "level": level, "page": pno, "line": i,
                          "zone": zone, "weak": weak})
    return found


def zone_texts(pages, sections):
    """Return {'main': str, 'references': str, 'appendix': str} using strong headings."""
    changes = []
    zone = "main"
    for s in sections:
        if s["zone"] != zone and not s["weak"]:
            zone = s["zone"]
            changes.append((s["page"], s["line"], zone))
    out = {"main": [], "references": [], "appendix": []}
    zone, k = "main", 0
    for pno, page in enumerate(pages, 1):
        for i, line in enumerate(page.split("\n")):
            while k < len(changes) and (pno, i) >= changes[k][:2]:
                zone = changes[k][2]
                k += 1
            out[zone].append(line)
        for z in out:
            out[z].append("")
    return {z: "\n".join(v) for z, v in out.items()}


def line_zone_fn(sections):
    """Return f(page, line) → zone."""
    changes, zone = [], "main"
    for s in sections:
        if s["zone"] != zone and not s["weak"]:
            zone = s["zone"]
            changes.append((s["page"], s["line"], zone))

    def f(page, line):
        z = "main"
        for p, l, zz in changes:
            if (page, line) >= (p, l):
                z = zz
        return z
    return f


KEYWORDS_RE = re.compile(r"^\s*(?:\*\*)?(?:keywords?|key ?words|index terms|schlagw[oö]rter)\b", re.I)
ABSTRACT_LABEL_RE = re.compile(r"^\s*(?:#+\s*)?(?:\*\*)?(?:abstract|summary|zusammenfassung)(?:\*\*)?\s*[:.—–-]?\s*", re.I)


BOILERPLATE_RE = re.compile(r"copyright|©|licen[cs]ed under|creative commons|date submitted|received:|accepted:|"
                            r"\S+@\S+\.\w|journal of quantitative description|journalqd|available at:|https?://|"
                            r"doi\.org|10\.\d{4,}/", re.I)


def _prose_block(block):
    lines = [l.strip() for l in block if l.strip()]
    words = sum(len(l.split()) for l in lines)
    return words >= 15 and sum(len(l) for l in lines) / len(lines) >= 45


def find_abstract(pages, sections):
    """The abstract as (first page, text without heading or keywords), or None.
    Tries, in order: an "Abstract" heading; an inline "Abstract:" label; the prose block(s)
    right above a "Keywords" line on the first three pages (the JQD:DM layout has no heading)."""
    span = section_span(pages, [s for s in sections if not s["weak"]], "abstract")
    if span and span[0].lower().strip("# ").startswith(("abstract", "summary", "zusammenfassung")):
        body = re.sub(r"⟨p\.\d+⟩\n?", "", span[2]).split("\n", 1)[-1]
        body = re.split(r"\n\s*(?:\*\*)?(?:keywords?|key ?words|schlagw[oö]rter)\b", body, flags=re.I)[0].strip()
        if len(body.split()) >= 20:
            return span[1], body
    lines = []  # (page, line) over the first three pages
    for pno, page in enumerate(pages[:3], 1):
        lines += [(pno, l) for l in page.split("\n")]
    for i, (pno, l) in enumerate(lines):
        m = ABSTRACT_LABEL_RE.match(l)
        if m and (l[m.end():].strip() or i + 1 < len(lines)) and len(l) < 200 and (
                l[:m.end()].strip().rstrip(":.—–-").strip("*# ").lower() in ("abstract", "summary", "zusammenfassung")):
            body = [l[m.end():]]
            for _, nxt in lines[i + 1:]:
                if KEYWORDS_RE.match(nxt) or (not nxt.strip() and len(" ".join(body).split()) >= 40):
                    break
                body.append(nxt)
            text = "\n".join(body).strip()
            if len(text.split()) >= 20:
                return pno, text
    k = next((i for i, (_, l) in enumerate(lines) if KEYWORDS_RE.match(l)), None)
    if k is None:
        return None
    blocks, cur = [], []
    for pno, l in reversed(lines[:k]):
        if BOILERPLATE_RE.search(l):
            continue  # footer or title-page notes, possibly between two parts of the abstract
        if l.strip():
            cur.append((pno, l))
        elif cur:
            blocks.append(list(reversed(cur)))
            cur = []
    if cur:
        blocks.append(list(reversed(cur)))
    taken = []
    for b in blocks:
        if _prose_block([l for _, l in b]) and sum(len(l.split()) for blk in taken for _, l in blk) < 400:
            taken.insert(0, b)
        elif taken:
            break
    if not taken:
        return None
    return taken[0][0][0], "\n\n".join("\n".join(l.strip() for _, l in b) for b in taken)


def section_span(pages, sections, name):
    """Text of the first section whose title contains `name` (case-insensitive).
    Returns (title, first_page, text) or None."""
    strong = [s for s in sections if not s["weak"]] or sections
    name_l = name.lower().strip()
    pick = next((s for s in strong if s["title"].lower().strip(" :.#0123456789") == name_l), None) \
        or next((s for s in strong if name_l in s["title"].lower()), None) \
        or next((s for s in sections if name_l in s["title"].lower()), None)
    if not pick:
        return None
    pool = strong if not pick["weak"] else sections
    end = next((s for s in pool if (s["page"], s["line"]) > (pick["page"], pick["line"])
                and s["level"] <= pick["level"]), None)
    out = []
    for pno in range(pick["page"], (end["page"] if end else len(pages)) + 1):
        lines = pages[pno - 1].split("\n")
        lo = pick["line"] if pno == pick["page"] else 0
        hi = end["line"] if end and pno == end["page"] else len(lines)
        out.append(f"⟨p.{pno}⟩\n" + "\n".join(lines[lo:hi]))
    return pick["title"], pick["page"], "\n".join(out)
