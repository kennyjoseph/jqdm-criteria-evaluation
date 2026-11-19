"""Build manual-mode-single-file.md: everything manual mode needs, in one file.

For users whose AI tool cannot run code (chat apps, institutional portals, local chat apps).
They upload this one file with the manuscript instead of the skill folder.

Usage, from the skill folder:  python tests/tools/build_manual_bundle.py [--check]
Writes ../manual-mode-single-file.md (next to README.md). With --check, exits 1 if that file is
missing or out of date instead of writing it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2]
OUT = SKILL.parent / "manual-mode-single-file.md"
ROWS = ["L1", "A1", "A2", "D1", "D2", "D3", "P1", "P2", "P3", "P4", "P5", "C1", "C2", "C3", "C4", "C5"]
STEPS = ["01-orientation", "02-loi-promises", "03-headline-claims", "04-data-and-measures",
         "05-figure-mapping", "06-21-criterion-assessment", "22-consistency", "23-synthesis",
         "24-one-sentence", "25-read-back"]

HEADER = """# JQD:DM criteria evaluation: single-file version for tools that cannot run code

Use this file if your AI tool can only chat (for example a chat window with code execution off, a
university chat portal, or a local model in LM Studio or Ollama). Give the AI this file and the full
text of your manuscript (and your accepted Letter of Inquiry, if you have it), and write:

> Follow the instructions in the section "FILE: references/manual-mode.md" to produce the JQD:DM
> criteria evaluation of the attached manuscript.

If your tool can run code (Claude Code, Codex CLI, OpenCode, or a chat app with code execution
turned on), use the `jqd-paper-review` folder instead: it checks quotes, pages and anonymity.

Generated from the skill folder by `tests/tools/build_manual_bundle.py`. Do not edit by hand.
"""


def _strip_search_hints(text: str) -> str:
    """Drop the `search_hints:` block from a criterion file's frontmatter (used only by the script)."""
    return re.sub(r"(?m)^search_hints:\n(?:[ \t]+-.*\n)+", "", text)


def build() -> str:
    parts = [HEADER]
    files = (["references/manual-mode.md", "references/journal.md", "references/scale.md"]
             + [f"references/steps/{s}.md" for s in STEPS]
             + [f"references/criteria/{r}.md" for r in ROWS])
    for rel in files:
        text = (SKILL / rel).read_text(encoding="utf-8")
        if "/criteria/" in rel:
            text = _strip_search_hints(text)
        parts.append(f"\n\n---\n\n## FILE: {rel}\n\n{text.strip()}\n")
    return "".join(parts).rstrip() + "\n"


def main(argv):
    text = build()
    if "--check" in argv:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("up to date" if ok else f"out of date: run python tests/tools/build_manual_bundle.py")
        return 0 if ok else 1
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT} ({len(text.split())} words)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
