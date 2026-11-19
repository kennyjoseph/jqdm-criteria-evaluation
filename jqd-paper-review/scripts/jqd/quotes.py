"""Quote and page check. Tolerates line-break hyphenation, ligatures, typographic quotes and dashes."""
from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

_TRANS = {ord(c): '"' for c in "“”„‟«»″"}
_TRANS.update({ord(c): "'" for c in "‘’‚‛′`´"})
_TRANS.update({ord(c): "-" for c in "‐‑‒–—−"})
_TRANS[0x00AD] = None


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_TRANS)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    return " ".join(text.lower().split())


def squeeze(text: str) -> str:
    return "".join(c for c in norm(text) if c.isalnum())


def _contains(hay_norm: str, hay_sq: str, part: str) -> bool:
    n = norm(part)
    if not n:
        return True
    if n in hay_norm:
        return True
    s = squeeze(part)
    if not s:
        return True
    if s in hay_sq:
        return True
    if len(s) < 20:
        return False
    # fuzzy: align on 8-character anchors, accept windows with ≥ 90 % similarity.
    # Numbers are never fuzzy: every digit run of the quote must be in the window, in order.
    L, digits = len(s), re.findall(r"\d+", s)
    for off in range(0, L - 8, max(4, L // 6)):
        anchor, start = s[off:off + 8], 0
        while True:
            pos = hay_sq.find(anchor, start)
            if pos < 0:
                break
            lo = max(0, pos - off)
            window = hay_sq[lo:lo + L + 2]
            if (SequenceMatcher(None, s, window[:L], autojunk=False).ratio() >= 0.9
                    and re.findall(r"\d+", window)[:len(digits)] == digits):
                return True
            start = pos + 1
    return False


def _parts(quote: str):
    return [p for p in re.split(r"\s*(?:\.\.\.|…|\[\.\.\.\]|\[…\])\s*", quote.strip().strip('"“”')) if p.strip()]


def _in_block(block: str, quote: str) -> bool:
    hn, hs = norm(block), squeeze(block)
    return all(_contains(hn, hs, p) for p in _parts(quote))


def find_quote(quote: str, pages, page: int):
    """Search `quote` on `page` ±1, then everywhere.
    Returns ('ok', page), ('moved', actual_page) or ('missing', None)."""
    n = len(pages)

    def text(i):
        return pages[i - 1] if 1 <= i <= n else ""

    for cand in (page, page - 1, page + 1):
        if 1 <= cand <= n and _in_block(text(cand), quote):
            return "ok", page
    if 1 <= page <= n and (_in_block(text(page - 1) + "\n" + text(page), quote)
                           or _in_block(text(page) + "\n" + text(page + 1), quote)):
        return "ok", page
    for i in range(1, n + 1):
        if _in_block(text(i), quote):
            return "moved", i
    for i in range(1, n):
        if _in_block(text(i) + "\n" + text(i + 1), quote):
            return "moved", i
    return "missing", None
