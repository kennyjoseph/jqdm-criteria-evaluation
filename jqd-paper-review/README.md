# jqd-paper-review

The criteria evaluation of the *Journal of Quantitative Description: Digital Media* (JQD:DM). You run it with an AI coding agent on your full manuscript before you submit. It scores the manuscript 0–3 on the journal's 16 criteria, with page references, and lists the points you must respond to at submission. It never recommends acceptance or rejection.

- **Authors:** read "For authors" below.
- **Agents:** start with `SKILL.md`.
- **Maintainers:** see "Install", "Layout" and "Notes for maintainers".

## For authors

### What you need

- An AI agent that can run commands on your computer and read skills, for example Claude Code. The agent runs the skill; the skill is a folder of instructions and Python scripts. Tested so far with Claude Code and Claude Opus 5.5 (see "Open items").
- Python 3.10 or newer. Nothing else needs installing.
- Your manuscript as a PDF with selectable text (not a scan), DOCX or plain text. If you have them, your accepted Letter of Inquiry (LOI) and a separate appendix.

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
- For every item under "Response required at submission", either change the manuscript or explain in your cover letter, by the item's label, why you left it unchanged. The suggested fix is one way to address a point, not the expected one; any change that resolves it, or a reasoned explanation, is a full response.
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

1. **Platforms.** Tested on macOS with Python 3.12, Claude Code and Claude Opus 5.5. Linux, Windows, Codex CLI, OpenCode and other models are untested.
2. **Stability.** On seven published papers run twice each, 102 of 112 criterion scores matched exactly and none differed by more than one point.
3. **Length.** An evaluation is about 2,500–3,500 words.
4. **Citation check.** A check of in-text citations against the reference list is switched off for now. It had too many false positives.

## Notes for maintainers

The design document is `../docs/specification.md`. Where the skill goes beyond it or departs from it:

- Criterion answers have a field `checks`: one short answer per check question. It makes the guided decision visible and is stored in the registry.
- Headline claims have a field `short` (≤ 60 characters). The criteria evaluation prints it in place of `H1 …`.
- Two headline claims are accepted with a warning (short notes may have only two); the specification says 3–5.
- Step 22 is completed by the script when it finds no duplicate, no misplaced gap and no calibration warning.
- V19 and V20 also run at `submit`, so that a name or a decision word is caught where it is written. V12 and V13 are shown at `submit` and resolved in step 22. V21 runs at the end only.
- Fuzzy quote matching never applies to numbers: every digit of a quote must match.
- "Raw lists of items in tables" belongs to P4 only.
- Institutions on the title page are shown to the model in step 1 as candidates for `redact`; only email addresses are added automatically. Automatic blocking on institution names would also block legitimate mentions of data providers.
- Criteria scored 1 whose gaps all have small fixes get an automatic note ("a score is not an effort estimate").
- `render --from state.json` checks quotes only when `--manuscript FILE` is given. Without it the evaluation carries the note "Created without validation of quotes and page references".
- Figures are assessed from captions and text only. Criterion P5 says so; the scripts do not read images.
- **Small fixes can be critical** when the gap bears on a headline claim (`affects` lists an H ID; V15, step 23). Effect on headline claims decides criticality, not fix size.
- **Tighter 1s (V23).** A criterion scored 1 needs a gap behind a headline claim, or at least two gaps that each need more than a small fix.
- **Cross-references: the script proposes, the model decides.** Regex candidates go to the model at P5, which checks each with `find` and reports real ones as a P5 minor item. V24 rejects a reported reference the manuscript never makes. Mentions after "Supplementary", "Online", "Appendix" or "SI" are not candidates. LaTeX "Figure ??" markers are printed directly (`unresolved_markers`).
- **A2.** Design kind `matched_comparison` (matching to hold a variable fixed in a descriptive comparison) does not force A2 to 0; `matched_control` means matching used to estimate an effect. A design linked to an LOI promise (`design.loi_promise`) was accepted by the editors, so V11 does not apply and A2 judges the language only.
- **C3.** A single wording-level abstract overclaim is a 2. Several overclaims, or one that reverses or misstates a finding, are a 1.
- **C2.** The model names suggested works; the evaluation adds a fixed note that they were suggested from memory and should be checked.
- **Length.** At most 3 strengths and 3 gaps per criterion (V08; 2 is the norm), each at most 180 characters. Each task block lists the schema's limits ("LIMITS").
- **Extraction.** Abstracts without a heading (the JQD:DM layout: an unlabelled block above "Keywords") are found, also across a page break (`extract.find_abstract`). Papers with few numbered headings use layout-detected headings. Ligatures and line-break hyphens are normalized in extraction, `find`, EVIDENCE and submitted quotes. Redaction also matches each author's surname on its own, case-sensitive.
- **The general rule for a 1 wins** over a criterion's own score decision; each task block says so. The score-1 lines of A1, A2, C2, C4, D3, P2 and P3 were aligned with it after test runs showed them pushing small-fix gaps to 1.
- **One problem, one criterion.** A problem that fits several criteria is recorded once (coverage → D2, measurement → D3, robustness → P1, intervals → P2, abstract overclaim → C3). Step 22 also flags gaps in different criteria that share a quote or a headline claim and read alike. Its calibration check now starts when more than a third of criteria are 1 or 0, since each needs an author response.
- **Layout.** There is no separate "Critical issues" section: the gaps step 23 marks critical are listed under "Response required" with their criterion and a "Why it matters" line. That list holds every gap of a criterion scored 0 or 1 plus the critical gaps of other criteria, by label (e.g. "D2-1"; the same label stands before each gap in the scores table). Strengths come first. Fixes are labelled "One potential fix"; the note and the response box say that authors need not apply the suggested fix.
- **Claim IDs in prose** are rendered as "the claim “…”"; models are told to name claims in words.
- **Robustness for agents:** printed commands and paths are absolute, `show` parts are at most 8,000 characters, numbers like "9.2" count as one word, technical uses of "rejection" do not trip V20, duplicate smaller fixes are printed once, and an affiliation with a place ("Hertie School, Berlin, Germany") no longer makes the country a redaction term.
- **Calibration examples** are shown when a file in `references/calibration/` has `status: agreed`. The map from example to source paper is kept outside this folder. After a change to a criterion file or an example, run the skill twice on at least two manuscripts and compare with `tests/tools/compare_runs.py` (see `tests/README.md`).
