# JQD:DM criteria evaluation

Version 2026.11.17. This is the version we plan to use.

Authors would run this tool with an AI agent on their full manuscript before submission. It scores the paper 0–3 on the journal's 16 criteria and lists the points the authors must respond to. Authors submit the evaluation with the paper, and the reviewers and the handling editor read it with the authors' responses.

## What's in this repository

| | For | What it is |
|---|---|---|
| `for-authors.md` | authors | Draft text for the submission instructions on the journal site |
| `jqd-paper-review/` | authors, agents | The tool itself, the folder authors would download. Its `README.md` explains installing and running it. |
| `manual-mode-single-file.md` | authors | Fallback for authors whose AI tool cannot run code: one file to give a chat tool with the manuscript. Unchecked, so weaker than the full tool. |

The editors' internal notes (how the journal would use the tool, test results, open decisions, the change log) and the example evaluations are not in this public repository. Editors have them in the zipped package.

## Quickest way in

To try it on a manuscript, follow "For authors" in `jqd-paper-review/README.md`.
