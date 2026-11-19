# Manual mode (no code execution)

Use this file only if `review.py --version` cannot be run, or if you were given
`manual-mode-single-file.md`. Follow only this file.
In manual mode no script counts, checks or formats anything. You write the criteria evaluation
yourself, as Markdown, in the format given below under "Evaluation template". The author reads it
directly, so it must be complete and readable on its own.

If you were given `manual-mode-single-file.md` instead of the skill folder: every file this text
refers to (`references/...`) is included in that document as a section headed `FILE: <path>`.
Read that section wherever this text says to read a file.

## Before you start: check that you can see the whole manuscript

Some chat applications pass a long attachment to the model in fragments. Before anything else,
write down for yourself the number of pages, the first sentence of the abstract and the last
sentence before the references.
- If you cannot, or the text you see has gaps, stop. Tell the user: "I can see only parts of the
  manuscript. Please paste the full text into the chat, or attach it in a way that passes the whole
  document, and ask again." Do not evaluate a manuscript you have seen only in part.
- Page numbers: use the page numbers printed in the manuscript. If none are printed, count the
  first page as page 1.

## What you deliver

1. **The criteria evaluation, as Markdown** (see "Evaluation template"). This is the main output.
   If you can create files, write it to `jqd-criteria-evaluation.md` and tell the user the path.
   Otherwise put it in the chat as your final message.
2. **The registry, as JSON**, if you can create files or have room left (see "Registry format").
   Write it to `jqd-review-state.json`, or put it in one code block after the evaluation. Anyone with
   Python can then check it and get the HTML version:
   `python <skill-folder>/scripts/review.py render --from jqd-review-state.json --manuscript <file>`.
   Skip it if you are short of space; the evaluation comes first.

Tell the user once: "Created in manual mode: quotes, page numbers, counts and anonymity were not
checked by the script." Do not give a decision, a recommendation or an overall score.

## Stance

- The question and the data are accepted (the paper follows an accepted Letter of Inquiry). Assess
  how well the manuscript carries out the project. Read `references/journal.md` once.
- Describe what the paper does and does not do. Write "the manuscript", never author names.
- Credit what is there first. Read the sections "Scale (short version)", "Fix tags" and
  "Calibration rules" in `references/scale.md` once.

## Workflow

Work in this order. Finish each step before you start the next. For each step, read its
instruction file in `references/steps/` (sections "Rules" and "Fields"). Keep short working notes;
if you cannot keep them private, put them in the chat under the heading "Working notes", before
the evaluation. Where a step file mentions the script, an INPUT block, READ commands or
submitting, read the manuscript directly instead; nothing is submitted in manual mode.

The evidence table in step 6 is not optional, and it must be written out in the chat, not kept
in your head. In testing, evaluations written without it read the manuscript too quickly: they
credited the abstract with findings it did not state and an answer to a research question that
appeared only in the Discussion.

1. **Orientation** (`01-orientation.md`): title, layout, paper type, primary aim, secondary aims.
2. **LOI promises** (`02-loi-promises.md`): only if an LOI was provided.
3. **Headline claims** (`03-headline-claims.md`): 3–5 claims H1 … with page, quote and status.
4. **Data and measures** (`04-data-and-measures.md`): sources S1 …, measures M1 …, design.
5. **Figure mapping** (`05-figure-mapping.md`): note which figures support each claim.
6. **Evidence table.** Write it in the chat under the heading "Working notes: evidence", before
   you score anything. Copy every quote character for character, and give single pages, not
   ranges.
   - **Abstract:** copy each sentence of the abstract that states a finding (a result, usually with
     a number). If none does, write "The abstract states no finding."
   - **Questions:** for each research question or stated aim, give the page, the name of the
     section the quote comes from, and a quote that answers it, plus the data and method behind
     the answer. If that section is the Discussion, the introduction or the conclusion rather than
     the Results, write "not answered in the Results": that is a gap under C1.
   - **Headline claims:** for each of H1 … H5, the page and a quote where the body supports it.
   Use the table while scoring. Two criteria depend on it directly: P3 (findings first) and C1
   (delivers on the question).
7. **Criteria**, one at a time, in this order: L1, A1, A2, D1, D2, D3, P1, P2, P3, P4, P5, C1, C2,
   C3, C4, C5. For each criterion read `references/criteria/<code>.md` (L1, A1, …).
   Answer the check questions, then set the score with the score decision. Read the field notes
   in `references/steps/06-21-criterion-assessment.md` once.
   If no LOI was provided, L1 is "N/A" with the reason "No Letter of Inquiry provided."
   **A score of 3 needs evidence:** for each criterion you score 3, write in your working notes
   one quote from the manuscript, with its page, that shows the criterion is met. If you cannot
   find one, the score is not 3.
8. **Consistency** (`22-consistency.md`): look for the same gap in two criteria and for gaps in the
   wrong criterion (the "not_here" lists of the criterion files tell you). Move or delete them.
9. **Synthesis** (`23-synthesis.md`), **one sentence** (`24-one-sentence.md`).
10. **Read-back** (`25-read-back.md`): read your results once as the author would. Correct them.
11. Run the self-check below. Then write the evaluation (and the JSON, if you deliver it).

## Self-check before you deliver

The script normally enforces these rules. In manual mode you check them yourself.
- Every criterion with a score below 3 has at least one gap with a page and a fix (kind, size, text).
- Every criterion scored "N/A" has a reason. L1 is "N/A" if and only if no LOI was provided.
- Every criterion with a feature marked "present" has at least one strength.
- No criterion scored 3 has a gap with a moderate or substantial fix.
- Each criterion has at most 3 strengths and gaps in total; 2 are usual.
- A criterion scored 1 (other than P4) has a gap that bears on a headline claim, or at least two gaps
  whose fix is not small.
- A2 is 0 when the design is causal, unless you can say why not.
- P1 is 0 only when a headline number depends on a consequential choice and nothing is checked; a gap must name that claim.
- P4 is 1 only with a gap whose fix is moderate or larger.
- 0–3 critical issues. Each is a gap whose fix is not small, or a small-fix gap that bears on a
  headline claim.
- 2–4 strengths in the "Strengths" section, each one of the strengths recorded under a criterion.
- At most 4 other changes. At most 3 smaller fixes per criterion.
- The one-sentence summary has at most 45 words.
- **Quotes:** at most 15 words, copied character for character from the manuscript. If you are not
  sure a quote is exact, leave it out; a gap without a quote is fine. Never reconstruct a quote
  from memory.
- **Evidence:** the evidence table is written out, and every score of 3 has a quote in your notes.
- **Pages:** each page number is a single page where the point can be checked, not a range. If you are unsure, check
  again or leave the gap out.
- **Anonymity:** no author name, affiliation, email address or file name anywhere. Author
  surnames count on their own, so write "prior work" instead of citing the authors' own papers.
- No decision words (accept, reject, minor or major revision) and no overall score.
- Lengths: strength and gap text at most 180 characters, fix text at most 200.
- If more than a third of the criteria are scored 1 or 0, re-check them against the calibration
  rules, or give one or two sentences of justification in your working notes.

## Evaluation template

Write the evaluation exactly in this structure, in this order. Text in angle brackets is yours;
everything else is fixed wording. Criterion titles and groups are in the frontmatter of each
criterion file (`title`, `group`). Score labels: 3 Fully, 2 Mostly, 1 Partly, 0 Not met, N/A.

```markdown
# JQD:DM criteria evaluation

**<title of the manuscript>** · <date, YYYY-MM-DD>

> Created in manual mode: quotes, page numbers, counts and anonymity were not checked by the script.

Input on how effectively this manuscript carries out its accepted Letter of Inquiry, compared with what JQD:DM values and what its published papers tend to have. It is not a review decision and does not suggest one. Scores show how fully the paper currently meets each value, not how much work a fix would take; the tags on each point give the size of the fix. Each "one potential fix" is a suggestion: you need not apply it, and any change or explanation that addresses the point is fine. Scores of 2 are common in published JQD:DM papers. When you submit, address each item under "Response required at submission" or explain in your cover letter, by its label, why you left it unchanged. Everything else is optional. The reviewers and the handling editor read this evaluation and your responses.

<Only if no LOI was provided:> No Letter of Inquiry was provided; the accepted question was inferred from the manuscript.

## The paper in one sentence

<one sentence, at most 45 words>

## Strengths

- <strength text> (<criterion code> · p. <page>)
<2–4 items>

## Response required at submission

Address each item, or explain in your cover letter, by its label, why you left it unchanged. The fixes suggested in this evaluation are one way to address a point, not the expected one; any change that resolves it, or a reasoned explanation, is a full response. The reviewers and the handling editor read your responses.

**<code> <criterion title>:** Scored <score> of 3 (<label>). The score rests on the points below; respond to each by its label.
- **<gap id>** <gap text> (p. <page>) <only for a critical issue:> *Why it matters:* <why>

<Repeat for every criterion scored 0 or 1. For a criterion scored 0, list all its gaps. For a
criterion scored 1, list only the gaps that bear on a headline claim, need more than a small fix,
or are critical issues. If that leaves out some of its gaps, replace the second sentence with:
"Respond to the points below by their labels; smaller points under this criterion are optional."
Then, for each critical issue in a criterion scored 2 or 3:>

**<code> <criterion title>:** Scored <score> of 3 (<label>). This point bears on a headline claim; respond by its label.
- **<gap id>** <gap text> (p. <page>) *Why it matters:* <why>

<If nothing qualifies, write: Nothing requires a response.>

## Size

About <your estimate, rounded to 100> words main text · <n> figures · <n> tables · <appendix present / no appendix> (counted by hand; approximate)

<One sentence: within, above or below the typical range for full papers (about 6,000–14,000 words) or short reports (about 2,500–4,000 words). These ranges are context, not rules.>

## Scores by criterion

| Code | Criterion | Score |
|---|---|---|
| L1 | Delivers what the LOI promised | <score> <label> |
<one row per criterion, all 16, in the order L1, A1, A2, D1, D2, D3, P1, P2, P3, P4, P5, C1, C2, C3, C4, C5>

### <group name, e.g. Aim and framing>

**<code> <criterion title>: <score> (<label>)**
- + <strength text> (p. <page>)
- − **<gap id>** <gap text> (p. <page>)
  From the paper: "<quote, if any>"
  One potential fix: <fix text> *(<writing or analysis> · <small, moderate or substantial>)*

<For an N/A criterion write its reason instead of strengths and gaps. Repeat for every criterion,
grouped under the group headings in the order: Letter of Inquiry, Aim and framing, Data,
Presentation and analysis, Contribution and claims.>

## What JQD:DM papers tend to have that this one may not

- <description of a feature you marked "absent", copied from the criterion file's frontmatter> (<code> · <criterion title>)
<Up to five. Take them first from criteria whose gaps bear on headline claims, then from the
lowest-scored criteria; at most two per criterion. If none: No strong-paper feature was marked as absent.>

## Other changes that would strengthen the paper

- <text> *(<writing or analysis> · <largest fix size among its gaps>; would raise <codes>)*
<At most four. If none: None beyond the points listed under each criterion.>

## Smaller fixes

- <Figures and captions / Cross-references / Numbers / Citations / Wording / Other>: <text> (p. <page>)
<If none: None recorded.>

---

Manual mode · jqd-paper-review 2026.11.17 · model: <your model name> · <date>
```

## Registry format

Deliver this only as described under "What you deliver". It holds the same content as the
evaluation in a form the script can check.

```json
{
  "schema_version": "2.0",
  "meta": {"run_id": "6 random hex characters", "mode": "manual", "model": "your model name",
           "created": "YYYY-MM-DD", "inputs": {"manuscript": true, "loi": true, "appendix": false},
           "redact": []},
  "orientation": {"title": "…", "layout": "standard", "paper_type": "full",
                  "primary_aim": {"text": "…", "page": 2},
                  "secondary_aims": [{"text": "…", "page": 3, "billing": "subordinate"}]},
  "loi_promises": [{"id": "P1", "type": "analysis", "text": "…", "loi_page": 1}],
  "headline_claims": [{"id": "H1", "short": "…", "text": "…", "page": 1, "quote": "…",
                       "status": "firm", "figures": ["Fig 2"]}],
  "data_sources": [{"id": "S1", "kind": "platform_census", "text": "…", "page": 5, "n": "1.2M posts"}],
  "measures": [{"id": "M1", "kind": "llm_coding", "text": "…", "page": 6, "supports": ["H1"]}],
  "design": {"kind": "descriptive", "text": "…", "page": 5},
  "rows": {
    "D3": {"checks": ["one answer per check question"], "score": 2, "na_reason": null,
           "plus": [{"id": "D3+1", "text": "…", "page": 6}],
           "gaps": [{"id": "D3-1", "text": "…", "page": 7, "quote": "…", "affects": ["H1"],
                     "fix": {"kind": "analysis", "size": "moderate", "text": "…"}}],
           "features": {"validated_on_own_data": "present", "error_rates_in_main_text": "absent"},
           "minor": [{"category": "figures", "text": "…", "page": 9}]}
  },
  "consistency": {"calibration_justification": null},
  "synthesis": {"one_sentence": "…",
                "critical": [{"gap": "D3-1", "rank": 1, "why": "…"}],
                "strengths": ["A1+1", "D2+2"],
                "other_changes": [{"gaps": ["P5-1", "P5-2"], "text": "…", "raises": ["P5"]}]}
}
```

Notes on the format:
- `rows` needs all 16 criteria. `features` needs every feature key from the frontmatter of the criterion file.
- An "N/A" criterion has `"score": "NA"`, a `na_reason`, all features "not_applicable", and empty `checks`, `plus` and `gaps`.
- Enumerated values (layouts, kinds, statuses) are listed in the step files. Use them exactly.
- Minor categories: figures, cross_references, numbers, citations, wording, other.
- Leave out `metrics`; the render command counts words, figures and tables itself when it gets
  the manuscript file.
