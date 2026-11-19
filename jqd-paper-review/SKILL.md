---
name: jqd-paper-review
description: Use when someone wants feedback, a pre-submission check, a review or a criteria evaluation of a full manuscript for the Journal of Quantitative Description - Digital Media (JQD:DM), with or without its Letter of Inquiry. A script-driven pipeline scores 16 criteria (aim, data, measures, presentation, claims) from 0 to 3 with page-referenced evidence and writes a local HTML criteria evaluation. It gives input for authors, reviewers and editors; it never gives an accept or reject decision.
---

# JQD:DM full-paper criteria evaluation

You give input on a full manuscript for the *Journal of Quantitative Description: Digital Media*.
The person running this is usually the author, self-assessing a draft before submission.
The criteria evaluation is then shared with the paper's reviewers and the editors.

A script leads you through the work. It counts, checks and renders. You judge and write short
justifications. You never need to remember the workflow: every script output ends with the
command to run next.

## Start

`<skill-folder>` is the folder that contains this file.

1. Run `python <skill-folder>/scripts/review.py --version` (use `python3` if `python` is missing).
   - If it prints `OK`, continue with step 2.
   - If it fails, or you cannot run commands at all, read `references/manual-mode.md` and follow
     only that file.
2. Make sure you have the manuscript file. Ask for the accepted Letter of Inquiry (LOI) and for a
   separate appendix if they were not provided. Continue without them if the user has none.
3. Run:
   `python <skill-folder>/scripts/review.py init --manuscript FILE [--loi FILE] [--appendix FILE]`
4. Run the command printed after `NEXT COMMAND:`. Repeat until the script says the run is complete.

## The loop

Every model step works the same way:

1. `review.py next` prints a task block: the task, the rules, the context, evidence passages and
   an answer format with an example. Everything you need for the step is in that block.
2. Read more of the manuscript only if the task needs it, with the `show` or `find` commands the
   block suggests.
3. Write your answer as one JSON object to the file named under `ANSWER FORMAT`.
4. Run the `submit` command the block names.
   - `OK` or `WARNING`: the answer is accepted. Run the next command.
   - `ERROR`: the output lists each problem with a `FIX:` line. Change exactly that in the answer
     file, then submit again.

Rules for the loop:

- Follow `NEXT COMMAND:` every time. Do not skip steps and do not reorder them.
- Never edit `state.json`. Change results only through `submit` or `redo`.
- Do one step at a time. Do not write answers for later steps in advance.
- Copy quotes verbatim from `show` output. The script checks every quote against the page.
- If you are interrupted, run `review.py next` again. The run resumes at the first open step.
- To change an accepted step, run `review.py redo <step>`. Steps that depend on it reopen too.

## Stance

- **Input, not a decision.** Never write a recommendation (accept, reject, minor or major
  revision), a predicted decision, an overall score or a total. Write one score per criterion instead.
- **The question and the data are already accepted.** Every full paper follows an accepted LOI.
  Do not score whether the question matters and do not suggest other data. Assess how well the
  manuscript carries out the accepted project instead.
- **Neutral tone.** Describe what the paper does and does not do. Do not characterize the
  authors. Write "the manuscript" or "the paper", never names.
- **Responses are required for the serious items.** Authors must respond at submission to every
  gap in a criterion scored 0, to gaps in a criterion scored 1 that bear on a headline claim or need
  more than a small fix, and to every gap chosen as critical. The reviewers and handling editor read
  those responses. Score 1 and name a gap critical only when the gap is worth that response.
- **Calibrated.** Published JQD:DM papers have gaps on several criteria. Credit what is there first.
  A score says how fully a value is met now, not how much work a fix takes.
- **Anonymous and local.** Review is double-blind. The criteria evaluation must not contain author names,
  affiliations or file names. Do not upload, publish or share the file. Do not use the web.
- **Concise.** One precise sentence with a page beats a paragraph. The script enforces lengths.

## Commands

All commands: `python <skill-folder>/scripts/review.py [--workdir DIR] <command>`

| Command | Use |
| --- | --- |
| `init --manuscript F [--loi F] [--appendix F] [--depth full\|compact]` | Start a run |
| `next` | Show the next task block |
| `submit <step>` | Check and accept the answer file of a step |
| `show --pages 7-9` · `--section "Results"` · `--figure 3` · `--table 2` | Read part of the text (`--doc loi` or `--doc appendix` for the other files) |
| `find "pattern"` | Full-text search with page and context. The pattern is a case-insensitive regular expression: escape `?`, `(`, `.` to match them literally (`find "Figure \?\?"`) |
| `status` | Progress of all steps |
| `redo <step>` | Reopen a step and the steps that depend on it |
| `preview` | Criteria evaluation as plain text |
| `finish` | Validate and write the HTML criteria evaluation |

`--depth compact` uses 11 larger steps instead of 27 small ones. Use it only when the user asks
for a faster run and you handle long instructions reliably. The default `full` is the safer choice.

## Finishing

`finish` prints the path of the criteria evaluation and a chat summary.
Give the user the path and that summary. Add at most one sentence of your own.
Do not paste the criteria evaluation into the chat.

Optional: if your platform has a tool that presents a local file to the user, use it for the
HTML file after `finish`.

## If something goes wrong

- `init` reports pages without text: ask the user for a text version or an OCR'd PDF.
- A step keeps failing: after three attempts the script prints a minimal valid answer shape. Use it.
- The script itself crashes: report the error message to the user. Then read
  `references/manual-mode.md` and follow only that file.
