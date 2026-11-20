# jqd-paper-review

The criteria evaluation of the *Journal of Quantitative Description: Digital Media* (JQD:DM). You run it with an AI coding agent on your full manuscript before you submit. It scores the manuscript 0–3 on 16 criteria, with page references, and lists the points you must respond to at submission. It never recommends acceptance or rejection.

- **Authors:** read "For authors" below.
- **Agents:** start with `SKILL.md`.
- **Maintainers:** see "Install", "Layout" and "Notes for maintainers".

## For authors

### What you need

- An AI agent that can run commands on your computer and read skills, for example Claude Code. The agent runs the skill; the skill is a folder of instructions and Python scripts. Tested so far with Claude Code and Claude Opus 5.5 (see "Open items").
- Python 3.10 or newer. Nothing else needs installing.
- Your manuscript as a PDF with selectable text (not a scan), DOCX or plain text. Please also include your accepted Letter of Inquiry (LOI) and a separate appendix if it exists.

### Running it

1. Put this folder where your agent finds skills (see "Install"). For Claude Code: `~/.claude/skills/jqd-paper-review/`.
2. Open the agent in a folder that holds your files and ask, for example: *"Run the jqd-paper-review skill on manuscript.pdf, with my LOI loi.pdf."*
3. The agent works through 26 short steps. A run takes about 5 minutes and uses roughly 200,000 model tokens.
4. The result is an HTML file: `jqd-review-<id>/out/criteria-evaluation-<id>.html`. Open it in a browser.

The skill runs on your computer and does not use the web. Your manuscript text is sent to the model your agent uses, under that provider's terms, as with any other use of the agent.

### Reading the evaluation

- **Strengths** come first.
- **Response required at submission** lists what you must answer: every gap in a criterion scored 0 or 1, and up to three other gaps that bear on a headline claim. Each gap has a label, such as "D2-1".
- **Scores by criterion** gives each criterion's score with its strengths and gaps. Each gap shows the page, a quote from the paper where useful, and *one potential fix*.
- A score of 2 ("Mostly") is common in published JQD:DM papers. A score says how fully a value is met now, not how much work a fix takes; the tag on each fix (for example "writing · small") gives the effort.

### What to submit

- Submit the HTML file with your manuscript.
- For every item under "Response required at submission", either change the manuscript or explain in a letter submitted alongside your paper, by the item's label, why you left it unchanged. The suggested fix is one way to address a point, not the expected one; any change that resolves it, or a reasoned explanation, is a full response.
- Everything else in the evaluation is optional.
- The reviewers and the handling editor read the evaluation and your responses.

The evaluation is produced by a language model and can be wrong. If a point misreads your paper, say so in your response.

## How it works

A Python script splits the work into short steps: extract the text, read the LOI, list the headline claims, assess one criterion at a time, check consistency, and render. Each step gives the model a task block with the criterion's questions, examples and the relevant passages from the manuscript. Each answer is checked against fixed rules (scores, quotes, page references, anonymity, length) before the next step starts. Every quote must occur in the manuscript.

**Calibration.** Each criterion has three or four example cases with a score and a one-sentence justification. They are paraphrased and anonymized from ten published JQD:DM papers the editors picked as good examples, plus a few invented cases for low scores, which published papers rarely show. The editors agreed them on 2026-11-16.

## Install

The folder follows the open Agent Skills format and needs Python ≥ 3.10. Nothing is installed at runtime; `pypdf` is included under `scripts/jqd/vendor/`.

- **Claude Code:** `~/.claude/skills/jqd-paper-review/`, or `.claude/skills/jqd-paper-review/` in a project.
- **Codex, OpenCode:** `~/.agents/skills/jqd-paper-review/`, or `.agents/skills/jqd-paper-review/` in a project.
- **claude.ai:** upload the folder as a skill. Without code execution the skill falls back to `references/manual-mode.md`: the model writes the evaluation as Markdown, and quotes, page references and anonymity are not checked. For chat tools that cannot take a folder, use `manual-mode-single-file.md` from the package instead.
- **Agents without skill support:** `AGENTS.md` holds a three-line pointer.

Check the installation with `python scripts/review.py --version` and `python -m unittest discover -s tests`. The version is the date of the last change to criteria, examples or rules.

## Layout

```text
SKILL.md, AGENTS.md
scripts/review.py              single entry point (init, next, show, find, submit, status, redo, preview, finish, render)
scripts/jqd/                   extract, metrics, state, schemas, validate, quotes, anon, render
                               + tasks (task blocks), ops (consistency and read-back changes), refs (loaders), common
references/steps/              one instruction file per step
references/criteria/           one file per criterion L1 … C5
references/calibration/        example cases per criterion
references/journal.md, scale.md, routing.json, manual-mode.md
assets/template.html, assets/examples/
tests/
```


## Open items

1. **Platforms.** Tested on macOS with Python 3.10, 3.11, 3.12 and 3.14, Claude Code and Claude Opus 5.5. Linux, Windows, Codex CLI, OpenCode and other models are untested.
2. **Stability.** On seven published papers run twice each, 102 of 112 criterion scores matched exactly and none differed by more than one point.
3. **Length.** An evaluation is about 2,500–3,500 words.
