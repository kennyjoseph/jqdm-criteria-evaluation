# Tests

Run from the skill folder: `python -m unittest discover -s tests`. Standard library only.

| File | Covers |
| --- | --- |
| `test_extract.py` | Page markers; main text, references, appendix; PDF via `pdftotext` and vendored `pypdf`; DOCX; scanned PDF |
| `test_metrics.py` | Word count (±3 %), figures and tables (exact), citations, cross-references, size line |
| `test_quotes.py` | Hyphenation, ligatures, typographic marks, moved pages, invented quotes |
| `test_validate.py` | Every rule V01–V22 with a passing and a failing case |
| `test_render.py` | Byte-identical output, no external resources, escaping, sections, anonymity |
| `test_pipeline.py` | Complete runs (full, compact, without LOI), resume, redo, error messages, manual mode |
| `test_refs.py` | Criterion files, anchors, routing table, step files, `SKILL.md`, standard-library-only imports |

## Fixtures

`fixtures/manuscript.txt` and `manuscript.pdf` are a synthetic five-page manuscript with known properties: three figures, two tables, one citation missing from the reference list, one uncited reference, two broken cross-references, one causal phrase, one overreaching sentence. `loi.txt` is its Letter of Inquiry. `scanned.pdf` has no text. The PDF has a running header and printed page numbers starting at 11.

## Not included: the acceptance test set

The specification asks for at least six real manuscripts with reference criteria evaluations from the editors, and for model runs on Claude Code, Codex CLI and OpenCode. These are not part of this folder. To evaluate model runs:

1. Run the skill five times per manuscript with the same model, each in its own working directory.
2. Run `python tests/tools/compare_runs.py RUN1 RUN2 RUN3 RUN4 RUN5 [--reference ref.json]`.
3. The tool prints score stability, exact agreement, overlap of critical issues, evidence fidelity and the steps with the most submit errors. A reference file has the form `{"rows": {"D3": [1, 2], …}}`.

After every change to a criterion file or an anchor, repeat this on at least two manuscripts. Justify shifts of a criterion median by more than one level.
