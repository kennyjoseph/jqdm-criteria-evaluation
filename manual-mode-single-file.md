# JQD:DM criteria evaluation: single-file version for tools that cannot run code

Use this file if your AI tool can only chat (for example a chat window with code execution off, a
university chat portal, or a local model in LM Studio or Ollama). Give the AI this file and the full
text of your manuscript (and your accepted Letter of Inquiry, if you have it), and write:

> Follow the instructions in the section "FILE: references/manual-mode.md" to produce the JQD:DM
> criteria evaluation of the attached manuscript.

If your tool can run code (Claude Code, Codex CLI, OpenCode, or a chat app with code execution
turned on), use the `jqd-paper-review` folder instead: it checks quotes, pages and anonymity.

Generated from the skill folder by `tests/tools/build_manual_bundle.py`. Do not edit by hand.


---

## FILE: references/manual-mode.md

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


---

## FILE: references/journal.md

---
layouts:
  standard: "Introduction → Background / Related Work → Data & Methods → Results → Discussion (the most common shape)"
  results_first: "Introduction → Results → Discussion → Methods at the end (short reports, dataset or resource papers)"
  question_led: "Results sections titled with the research questions or plain-language questions; methods introduced where used"
  research_note: "Short research note: brief unheaded introduction ending in a list of aims, then results and discussion; robustness in supplementary files"
  short_report: "Short descriptive report: Introduction → Methods → Results → Conclusion, no literature section"
  inventory: "A method section followed by many short results sections, one per quantity or unit of analysis, each opening with its finding"
norms:
  full_words: [6000, 14000]
  short_words: [2500, 4000]
  abstract_words: [100, 275]
  figures: [2, 25]
  tables: [0, 11]
---

# JQD:DM: what the journal publishes, layouts, length norms

The scripts read the frontmatter (layout list, length norms) and show excerpts of the sections below.

## What the journal publishes
JQD:DM publishes quantitative descriptive research in which digital media is the substantive object of study. A strong paper tells readers something they did not know, and should care about, about what is happening in digital media. It uses data whose relationship to a population is clear. It makes no causal claims.

## Starting point
Every full paper follows an accepted Letter of Inquiry (LOI). The editors have already judged that the question is worth answering, that it is about digital media, and that the dataset is a reasonable way to answer it.
- Do not score whether the question matters. Score how clearly the paper answers it instead.
- Do not suggest a different question or different data. Suggest how to characterize the accepted data instead.
- Limits of the data are in scope as things to characterize and to reflect in the claims.
- If no LOI is provided, infer the accepted question and data from the manuscript's own stated aims and data section.

## Layouts
There is no required structure. Do not mark a paper down for its layout. Ask whether the layout lets a reader find what is described, from what data, and what was found. Six shapes are common: see the layout list in the frontmatter. Background ranges from prior work woven into the introduction to a full literature review ending in research questions; what matters is that its length and depth match the questions asked. A short explainer of how a platform works helps when readers need it to interpret the measures.

## Length norms
Context, not rules. Judge length against what the paper delivers.
- Main text (excluding references and appendix, captions included): full papers about 6,000–14,000 words, median about 7,000–9,000. Short reports and research notes about 2,500–4,000.
- Abstract: one paragraph, about 100–275 words.
- Main-text figures: about 2–25, typically 5–13. Multi-panel figures are common.
- Main-text tables: 0–11. Many strong papers have none.
- Appendix or supplement: none to very long. Many papers use an external supplement or repository.

## Appendices
The appendix is where detail belongs: codebooks, full LLM prompts, keyword lists. If an appendix is provided, include it in the assessment. If it is not provided, you can still name what the main paper expects the appendix to hold. Do not give credit for validation, coverage checks or robustness analyses that the paper neither reports nor references.


---

## FILE: references/scale.md

---
loaded_words:
  - "sloppy"
  - "fails"
  - "failed"
  - "failure"
  - "weak paper"
  - "poor"
  - "poorly"
  - "careless"
  - "lazy"
  - "flawed"
  - "fatal"
  - "unacceptable"
  - "naive"
  - "amateurish"
  - "misleading"
  - "dishonest"
  - "useless"
  - "worthless"
  - "inadequate"
  - "incompetent"
  - "trivial"
---

# Scale, fix tags and calibration

The scripts show excerpts of this file in the task blocks. The word list in the frontmatter is used by rule V21.

## Scale (short version)
3 = Fully meets the value. Nothing important to fix.
2 = Mostly meets it. Specific, contained gaps with a clear fix.
1 = Partly meets it. One gap that changes how a headline claim should be read, or several gaps that each need more than a small fix. Otherwise 2.
0 = Does not meet it, or does not attempt it.
"NA" = The criterion cannot apply to this design. Use it rarely and give the reason.
Weigh by headline claims: a gap behind a headline claim lowers the score more than the same gap in a side analysis.
Fix kind: writing (text, figures, framing, captions) or analysis (more work with the accepted data).
Fix size: small (a sentence, a caption, a number the authors have), moderate (a new panel, a short analysis, a rewritten section), substantial (new coding, a restructured paper). The score says how fully the value is met now; the size carries the effort.

## Fix tags
- **Kind `writing`:** text, figures, framing, captions.
- **Kind `analysis`:** more work with the accepted data: intervals, sensitivity checks, a benchmark line, hand-coding a validation sample.
- **Size `small`:** a sentence, a caption, a number the authors already have.
- **Size `moderate`:** a new figure panel, a short analysis, a rewritten section.
- **Size `substantial`:** new coding, a restructured paper.
- A score is not an effort estimate. A 1 can be one small fix away from a 3. The criteria evaluation adds a note to such criteria automatically.

## Calibration rules
Published JQD:DM papers, including strong ones, have gaps on several criteria. Do not be harsher than a fair reviewer.
1. Start from what the paper does. Every criterion with anything done well gets at least one strength.
2. Score 2 when the paper does most of what the criterion asks and the gap is a specific omission with a clear fix.
3. Reserve 1 for a gap that changes how a headline claim should be read, or for several gaps that each need more than a small fix. Name the claim under `affects`. Authors must respond to every criterion scored 0 or 1, so a 1 must be worth a response.
4. Reserve 0 for criteria the paper does not attempt.
5. Do not stack minor issues into a low score. Three small caption problems are a 2, not a 1.
6. Separate "missing" from "not reported here". A check that is described but not shown is usually a small writing fix.
7. If most criteria are 1 or 0, check each of them: was the criterion scored against the paper's claims, or against perfection?

## Tone
Describe what the paper does and does not do. Do not characterize the authors. Write "the manuscript" or "the paper", never names. Do not use the loaded words listed in the frontmatter; describe the specific gap instead.


---

## FILE: references/steps/01-orientation.md

# Step 1 · Orientation

## Task
Record the title, the names to redact, the layout, the paper type and the aims of the manuscript.

## Rules
- Use the title page, abstract, headings and captions shown under INPUT. Read more only if the aim is not stated there.
- Record what the manuscript says. Do not judge it in this step.
- The primary aim is the one descriptive aim the paper mainly pursues. Write it in your own words.
- If no primary descriptive aim can be identified, write the text "No primary descriptive aim could be identified." and page 1.
- A secondary aim is anything else the paper says it does: showing a data source can be used, a framework, a tool comparison.
- Choose "short" as paper type for research notes and short reports of about 2,500–4,000 words. Choose "full" otherwise.

## Fields
- `model`: the model name your platform reports for you. Write "unknown" if you cannot tell.
- `title`: the manuscript title as printed, without author names.
- `redact`: every author name, affiliation and funder that appears in the manuscript, each as printed. The script adds email addresses itself. Use `[]` if the manuscript is anonymized.
- `layout`: one value from the LAYOUTS list.
- `paper_type`: "full" or "short".
- `primary_aim`: `text` (≤ 220 characters), `page`, optional `quote` (≤ 15 words, copied verbatim).
- `secondary_aims`: 0–5 entries with `text`, `page` and `billing`. Use "subordinate" if the aim clearly supports the main description. Use "equal" if it gets as much room as the primary aim in abstract, introduction or conclusion.


---

## FILE: references/steps/02-loi-promises.md

# Step 2 · LOI promises

## Task
List what the Letter of Inquiry (LOI) promised the paper would do.

## Rules
- Use only the LOI text shown under INPUT.
- Write one entry per promise. Merge details that belong together. 4–10 entries are usual.
- Do not judge yet whether the manuscript keeps a promise. Criterion L1 does that later.
- Number the promises P1, P2, P3 … in the order of the LOI.

## Fields
- `id`: P1, P2, …
- `type`: "question" (a question the paper will answer), "data" (a dataset, sample or time span), "analysis" (a planned analysis, measure or comparison), "output" (a finding, figure, dataset or resource the paper said it would deliver).
- `text`: the promise in one sentence (≤ 220 characters).
- `loi_page`: the LOI page marker where the promise is made.


---

## FILE: references/steps/03-headline-claims.md

# Step 3 · Headline claims

## Task
Identify the 3–5 headline claims of the manuscript.

## Rules
- A headline claim is a finding that the abstract, the preview in the introduction or the conclusion presents as a main result.
- Read the abstract under INPUT first. Then run the READ commands for the introduction and the conclusion.
- Record claims the paper makes. Do not add claims you think it should make, and do not evaluate them.
- Order the claims by prominence: H1 is the finding the paper puts first.
- Copy each quote verbatim from the text. The script searches for it on the page you give.
- Every later step weighs gaps by these claims. Choose them with care.

## Fields
- `id`: H1 … H5, in order.
- `short`: a label of at most 60 characters. Readers of the criteria evaluation see it in place of the ID.
- `text`: the claim in your own words, with its number where the paper gives one (≤ 220 characters).
- `page`: the page marker where the claim is stated most clearly.
- `quote`: at most 15 words from that page, copied verbatim.
- `status`: "firm" if the body presents the result without reservation. "tentative" if the body hedges it (suggestive, preliminary, small sample, exploratory).


---

## FILE: references/steps/04-data-and-measures.md

# Step 4 · Data and measures

## Task
Record the data sources, the measures behind the headline claims and the analysis design.

## Rules
- Run the READ commands for the data and methods sections first.
- Record what the paper uses. Do not judge quality in this step.
- List a measure if a headline claim rests on it. Skip measures used only in side analyses.
- Decide the design from how the main analysis is built, not from single words. The EVIDENCE hits show where design words occur.
- Choose "descriptive" or "matched_comparison" unless the analysis is built on one of the causal designs below.
- If several designs apply, record the one the headline claims depend on most.
- Matching used only to hold a variable fixed while describing groups is "matched_comparison", not "matched_control".
- If an LOI promise describes or implies the design, put its ID in `loi_promise`.

## Fields
- `data_sources` (1–8): `id` S1, S2 …; `kind`; `text` (what it is, ≤ 220 characters); `page`; optional `n` as printed (e.g. "1.2M posts").
  Kinds: probability_survey, platform_census (full or near-full collection from a platform), vendor_collection, convenience_sample, keyword_collection, tracking_panel (browsing or app tracking), other.
- `subsets` (optional): subsets behind headline claims, with `text`, `page`, optional `n`.
- `measures` (0–12): `id` M1, M2 …; `kind`; `text`; `page`; `supports` (IDs of the headline claims that rest on it).
  Kinds: classifier, llm_coding, sentiment, topic_model, embedding, lexicon, pretrained_tool, manual_coding, survey_item, constructed_index (indices, weights, thresholds, category schemes, proxies), count_metric (plain counts and shares), other.
- `design`: `kind`, `text` (one sentence on how the main analysis is built), `page`; optional `loi_promise` (ID of the LOI promise that describes the design; omit without an LOI).
  Kinds: descriptive, matched_comparison (units matched to hold a variable fixed in a descriptive comparison), event_study, interrupted_time_series, diff_in_diff, discontinuity, matched_control (matched units used to estimate an effect), synthetic_control, placebo_test, shock_comparison (treated vs. untreated units around a shock), causal_question (the research question itself asks about an effect), other.


---

## FILE: references/steps/05-figure-mapping.md

# Step 5 · Figure mapping

## Task
Say which figures and tables support which headline claims.

## Rules
- Write one entry for every figure and table in the INPUT list. Use the labels exactly as listed, for example "Fig 2" or "Tab 1".
- A figure supports a claim if it shows the evidence for that claim.
- Use `"supports": []` for a figure that supports no headline claim.
- Decide from the captions. If a caption is unclear, run `review.py show --figure N`.
- If the list is empty, answer `{"map": []}`.

## Fields
- `figure`: the label from the list.
- `supports`: IDs of headline claims (H1 …), possibly empty.


---

## FILE: references/steps/06-21-criterion-assessment.md

# Steps 6–21 · Criterion assessment (one criterion per step)

## Task
Assess one criterion against the manuscript.

## Rules
The rules of a criterion step are the criterion file under `references/criteria/`. The script inserts it into the task block.

## Fields
- `checks`: one short answer per check question, in order (≤ 200 characters each). Write these first; the score follows from them.
- `score`: 0, 1, 2, 3 or "NA", chosen with the score decision. With "NA", add `na_reason`.
- `plus`: what the paper does well in this criterion. Each entry has `id` (criterion code, "+", number), `text` (one precise sentence) and `page`.
- `gaps`: what is missing or unclear. Each entry has `id` (criterion code, "-", number), `text` (neutral, specific), `page` (where it occurs or where the fix would go) and `fix`.
- `fix`: `kind` ("writing" or "analysis"), `size` ("small", "moderate" or "substantial"), `text` (the concrete fix; a proposed rewrite is welcome).
- Optional in a gap: `quote` (≤ 15 words copied verbatim; the script checks it), `affects` (IDs of the headline claims the gap bears on), `topic` (from the TOPICS line), `doc` ("appendix" or "loi" if the page is in that file).
- Write 2 strengths and gaps in total, usually one of each; 3 at most. Keep each to one line (≤ 180 characters). Put further small points under `minor`.
- A score below 3 needs at least one gap. A score of 3 allows only gaps with a small fix.
- A score of 1 needs a gap that changes how a headline claim should be read. List that claim under `affects`.
- Two gaps that each need more than a small fix also justify a 1. Otherwise score 2.
- Fill `affects` whenever a gap bears on a headline claim. It decides what the author must respond to.
- `features`: one status for every feature listed: "present", "partial", "absent" or "not_applicable".
- `minor` (optional, at most 3): small slips with `category` (figures, cross_references, numbers, citations, wording, other), `text`, `page`.
- Give credit first: if the paper does anything in this criterion well, write a strength.
- Write "the manuscript" or "the paper", never author names. Write names of data sources, measures and claims, not their S, M or H IDs.
- Do not list gaps named under NOT HERE. They belong to other criteria.
- One problem, one criterion: record it where NOT HERE points, and do not lower a second criterion for it.


---

## FILE: references/steps/22-consistency.md

# Step 22 · Consistency check

## Task
Decide every case the script found: move the gap, merge the duplicate, or keep it with a reason.

## Rules
- Each flaw goes in one criterion. The script lists gaps that may sit in the wrong criterion and pairs of gaps that may say the same thing.
- A ROUTE case names a gap and the criterion the routing table assigns. Choose "move" to let the script move it. Choose "keep" if the gap is about something else than the topic; say what.
- A DUPLICATE case names two gaps. Choose "merge" and name the gap that stays in `keep_gap`. Choose "keep" if they describe two different problems; say how they differ.
- Moving or merging changes criteria. If a criterion then breaks a rule, the script tells you. Adjust its score with `score_changes`.
- After moving a gap out, a criterion may deserve a higher score. After receiving one, a criterion may deserve a lower score. Check both.
- If the task block shows CALIBRATION, more than a third of the criteria are scored 1 or 0. Re-read each low criterion against the calibration rules shown. Raise criteria that were scored against perfection with `score_changes`. If the low scores stand, write `calibration_justification`.
- Change nothing else in this step.

## Fields
- `decisions`: one entry per case with `issue` (K1 …), `action` ("move", "merge" or "keep"), `reason` (one sentence) and, for "merge", `keep_gap`.
- `score_changes` (optional): entries with `row`, `score` (0–3) and `reason`.
- `calibration_justification` (only with CALIBRATION): one or two sentences on why the paper falls short this broadly.


---

## FILE: references/steps/23-synthesis.md

# Step 23 · Synthesis

## Task
Choose the critical issues, the strengths and the other changes from the entries already recorded.

## Rules
- Work only with the IDs listed under INPUT. Do not introduce new problems or new strengths in this step.
- Critical issues: at most 3. Choose the gaps that most affect whether readers can trust and use the headline findings. Rank them 1, 2, 3.
- Critical means the gap changes how a headline finding should be read. The size of the fix does not decide this.
- A gap with a moderate or substantial fix can be critical. A gap with a small fix can be critical only if it bears on a headline claim (its `affects` lists an H ID).
- A wording change to a single sentence is not critical by itself. Put it under other changes.
- Authors must respond to every critical issue at submission. Do not list a gap as critical unless a reviewer would want that response.
- No critical issues is a normal result for a strong paper. Then answer `"critical": []`. Do not promote smaller gaps.
- `why`: one sentence on why the gap matters for the headline findings. Do not repeat the gap text; the criteria evaluation prints it.
- Strengths: choose 2–4 strength IDs that show what the paper does best relative to what the journal values.
- Other changes: at most 4 changes beyond the critical issues. Each bundles 1–4 related gaps. Important gaps with small fixes belong here.
- `text` of an other change: one sentence that states the change. The script adds kind, size and the criteria it would raise.
- Do not give a verdict on the paper as a whole. Write one sentence per issue instead.

## Fields
- `critical`: 0–3 entries with `gap` (gap ID), `rank` (1 … n) and `why` (≤ 220 characters).
- `strengths`: 2–4 strength IDs, most important first.
- `other_changes`: 0–4 entries with `gaps` (1–4 gap IDs), `text` (≤ 200 characters) and optional `raises` (criterion codes; default: the criteria of the gaps).


---

## FILE: references/steps/24-one-sentence.md

# Step 24 · The paper in one sentence

## Task
Write one sentence that says what the paper primarily describes, from what data, and its headline finding.

## Rules
- Use the primary aim, the data sources and the headline claims under INPUT.
- At most 45 words. One sentence.
- State what the paper reports. Do not evaluate it, and do not use causal wording.
- Do not name the authors. Start with "The paper" or with the thing described.
- Sometimes no primary aim or no finding can be identified. Then say so: set `cannot_be_stated` to true and give the `reason`.

## Fields
- `one_sentence`: the sentence (≤ 45 words).
- Or: `cannot_be_stated`: true, and `reason`: one sentence (≤ 200 characters).


---

## FILE: references/steps/25-read-back.md

# Step 25 · Read-back as the author

## Task
Read the criteria evaluation preview as the author would and propose at most five corrections, or none.

## Rules
- Read the PREVIEW once from top to bottom. Imagine you wrote the manuscript and a reviewer and an editor will read this page.
- Correct only these things: an entry that is unclear or not specific; a wording that characterizes the authors instead of describing the paper; a fix whose size tag does not fit its text; a score that does not fit its own bullets under the calibration rules.
- Do not add new gaps or strengths. Use `review.py redo <step>` for that instead; the task block names the command.
- If most criteria are 1 or 0, check once more whether the paper really falls short that broadly.
- If nothing needs correcting, answer `{"changes": []}`. That is a normal result.

## Fields
`changes`: 0–5 entries. Each has `op`, `value`, `reason` (one sentence) and usually `target`.
- `"op": "edit_text"`: `target` is a strength or gap ID in square brackets in the preview; `value` is the new text (≤ 180 characters).
- `"op": "edit_fix_text"`: `target` is a gap ID; `value` is the new fix text (≤ 200 characters).
- `"op": "edit_why"`: `target` is the gap ID of a critical issue; `value` is the new sentence on why it matters.
- `"op": "set_fix_size"`: `target` is a gap ID; `value` is "small", "moderate" or "substantial".
- `"op": "set_score"`: `target` is a criterion code; `value` is 0, 1, 2 or 3.
- `"op": "edit_sentence"`: no target; `value` is the new one-sentence summary (≤ 45 words).


---

## FILE: references/criteria/L1.md

---
row: L1
title: Delivers what the LOI promised
group: Letter of Inquiry
depends_on: [loi_promises, orientation]
features:
  question_kept: "The manuscript answers the primary question the Letter of Inquiry set out"
  data_kept: "The data named in the Letter of Inquiry are the data analysed"
  analyses_delivered: "The analyses, measures and comparisons planned in the Letter of Inquiry are reported"
  changes_explained: "Changes since the Letter of Inquiry are named and briefly justified"
not_here:
  - "How clearly the manuscript states and keeps its own question → A1"
  - "Whether the findings answer the question in citable form → C1"
---

## What this criterion checks
Compare the manuscript with the Letter of Inquiry (LOI). Look at its question, its data, its planned analyses or measures, and the findings or outputs it promised.
Projects evolve. A change in methods, scope or emphasis is fine in two conditions. The manuscript delivers the substance of the accepted project. And it briefly says what changed and why.
Lower the score when a promised question, dataset, analysis or comparison is missing without explanation.
Lower it most when the primary question has shifted so that the paper no longer answers what was accepted.
Write one strength per group of promises kept and one gap per promise not kept. Put the promise IDs (P1 …) in "affects".

## Check questions
1. For each LOI promise in the context list: is it kept, changed with an explanation, changed without one, or missing?
2. Is the primary question of the manuscript the question the LOI set out?
3. Where methods, scope or emphasis changed: does the manuscript say what changed and why?
4. Does the manuscript still deliver the substance of the accepted project?

## Score decision
- 3: Every promise is kept, or changed with a brief explanation.
- 2: The substance is delivered. One or two promises are changed or missing without explanation, and none of them is the primary question.
- 1: Several promised analyses, datasets or comparisons are missing without explanation, or one that the primary question depends on.
- 0: The primary question has shifted; the paper no longer answers what was accepted.
- "NA": Only when no LOI was provided. The script sets this itself.


---

## FILE: references/criteria/A1.md

---
row: A1
title: Answers the accepted question clearly
group: Aim and framing
depends_on: [orientation, headline_claims]
features:
  aim_stated_early: "The research question or descriptive aim is stated plainly and early"
  aim_as_targets: "The aim is given as a short list of descriptive targets (how much, who, how concentrated, how it changed)"
  aim_stays_primary: "The same aim stays primary in abstract, introduction and conclusion"
  secondary_aims_subordinate: "Secondary aims (showing a data source can be used, a framework, a tool comparison) are clearly subordinate"
not_here:
  - "Drift from the Letter of Inquiry → L1"
  - "Whether the findings answer the question in citable form → C1"
  - "Order and placement of findings in title, abstract and sections → P3"
  - "An aim stated late, or findings not previewed → P3"
  - "Whether the question matters → out of scope; never a gap"
---

## What this criterion checks
The research question is stated plainly and early and stays primary throughout.
A reader can state in one sentence what the paper describes and what it found.
Secondary aims are fine when they are clearly subordinate and support the main description. A method or data-source aim that the description depends on (a new sampling method, a new dataset) is not a competing aim.
Lower the score when secondary aims get equal billing in the abstract, introduction or conclusion, or when analyses do not connect to the main aim.
This criterion judges the question the manuscript itself states.

## Check questions
1. On which page is the primary descriptive aim first stated, and is it stated plainly?
2. Can you state in one sentence what the paper describes and what it found?
3. Is the same aim primary in the abstract, the introduction and the conclusion?
4. Does any secondary aim from the context list get equal billing in one of these places?
5. Do all main analyses connect to the primary aim?

## Score decision
- 3: The aim is plain and early, stays primary, and the analyses connect to it.
- 2: The aim is identifiable and primary. One contained gap: stated late, one secondary aim competing in one place, or one analysis left unconnected.
- 1: A reader cannot tell which aim the headline claims answer: secondary aims compete throughout, or several main analyses do not connect to the main aim. Equal billing alone, with the description still clear, is a 2.
- 0: No primary descriptive aim can be identified, or the paper has drifted to a different question than the one it states.


---

## FILE: references/criteria/A2.md

---
row: A2
title: Non-causal framing
group: Aim and framing
depends_on: [design, headline_claims, loi_promises]
features:
  descriptive_stated: "The paper says explicitly that its analyses are descriptive"
  explanations_hedged_in_discussion: "Explanations are hedged (\"consistent with\", \"one plausible explanation\"), placed in the Discussion and supported by outside evidence"
  adjusted_differences_as_description: "Regressions with controls or fixed effects are reported as adjusted differences, omnibus tests as descriptive diagnostics"
not_here:
  - "A claim that outruns the evidence without causal wording → C3"
  - "Group differences asserted without variation → P2"
---

## What this criterion checks
Claims are about what is, how much, who, where, and how it changed.
Design-level problems: event study, interrupted time series, difference-in-differences, discontinuity, matched or synthetic controls, placebo tests used to show a shift is "unusual", treated vs. untreated comparisons built around a shock, a causal research question.
Language-level problems: the words effect, impact, leads to, facilitates, is a more important factor than; hypothesis-about-why framing ("if X causes Y we should find …"); results read against outside events as if those events explain them; mechanism claims made in the Results.
Fine, and common in strong papers; never list these as gaps: saying the analyses are descriptive; adjusted differences from regressions; descriptive omnibus tests; decomposition language ("driven by fewer new entrants"); hedged explanations in the Discussion.
Matching to hold a variable fixed while describing groups is fine too. It is a problem only when the matched comparison estimates an effect.
If the LOI described or implied the design, the editors accepted it at that stage.
Then do not treat the design as a problem or list it as a gap; judge the language only.

## Check questions
1. Does the analysis design in the context, or any analysis you find, belong to the design-level problems? Answer no if the LOI described it.
2. Is the research question itself causal?
3. Where do the language-level words appear (abstract, results, discussion), and how often?
4. Are results read against outside events as explanations, or are mechanism claims made in the Results?
5. Are explanations hedged and placed in the Discussion?

## Score decision
- 0: Question 1 or 2 is yes (a design-level problem the LOI did not describe).
- 1: Causal language is frequent, or a headline claim is stated causally. Hedged phrases, or one sentence in the abstract or results that a change of wording fixes, are a 2.
- 2: A few causal phrases or one mechanism claim, outside the headline claims.
- 3: No design-level problem and at most a stray phrase. List a stray phrase as a small gap or under "minor".


---

## FILE: references/criteria/D1.md

---
row: D1
title: Defined population and sample
group: Data
depends_on: [data_sources, headline_claims]
features:
  population_and_unit_explicit: "The population and the unit of analysis are explicit"
  non_coverage_stated: "The paper states what its estimates do not describe (accounts are not people; public content only; surviving feeds miss closed ones)"
  inclusion_rules_for_subsets: "Inclusion rules are given for the main data and for every subset behind a headline claim"
  scale_in_one_place: "The scale of the data is given in one place (units, items, time span, groups, N at each filtering step), often in a small summary table or panel"
not_here:
  - "What the source covers or misses, weights, benchmarks → D2"
  - "Whether a measure captures what it is meant to → D3"
  - "n shown next to a subgroup estimate or its interval → P2"
  - "Whether different data should have been used → out of scope; never a gap"
---

## What this criterion checks
The population and the unit of analysis are explicit.
The paper states what the estimates do not describe. Examples: accounts are not people; public content only; self-reported frequency is not content volume.
Inclusion rules are given for the main data and for every subset behind a headline claim. A subset chosen because the authors happened to know its members is not a rule.
Ns are reported and consistent, including for small subgroups behind headline numbers.

## Check questions
1. Are the population and the unit of analysis explicit?
2. Does the paper state what its estimates do not describe?
3. Are inclusion rules given for the main data and for every subset behind a headline claim?
4. Are the Ns reported, and do they agree across text, tables and figures?
5. Is the scale of the data given in one place?

## Score decision
- 3: Questions 1–4 are yes.
- 2: Questions 1–4 are yes apart from one contained omission. Examples: one subset without a rule; one N that does not reconcile; non-coverage stated only in part.
- 1: Several of questions 1–4 are no, or a missing rule or N behind a headline claim changes how that claim should be read.
- 0: The population and the unit of analysis cannot be identified.


---

## FILE: references/criteria/D2.md

---
row: D2
title: Characterizes what the data cover
group: Data
depends_on: [data_sources, headline_claims]
features:
  coverage_measured: "The share of the population captured is measured or estimated, and missing or deleted units are discussed"
  benchmark_against_outside_source: "Estimates are benchmarked against an outside source where one exists"
  assembly_and_misses_described: "The paper says how the collection was assembled and what it is likely to miss"
  collection_differences_aligned: "Differences in how compared data were collected are named, and the comparison is shown to hold once they are aligned"
  claims_limited_to_coverage: "Claims are limited to what the collection supports"
not_here:
  - "Whether these data should have been used at all → out of scope; never a gap"
  - "Population, unit, inclusion rules, Ns → D1"
  - "How a limitation moves a specific estimate → C4"
---

## What this criterion checks
The data source is accepted. What matters is whether the paper tells readers what it covers and limits its claims accordingly. Look for what fits each data source kind in the context list:
- probability_survey: weights described; estimates benchmarked against an outside source where one exists; wave-to-wave changes in mode or sample discussed; for compositional shifts, the population's own shift shown as a baseline.
- platform_census: share of the population captured measured or estimated; missing or deleted units discussed.
- vendor_collection, convenience_sample, keyword_collection, tracking_panel: how the collection was assembled and what it is likely to miss; differing sampling rates across sources handled; a comparison with another source, or of included and excluded units, where feasible.
- Comparisons across waves, samples or sources: each difference in collection (window, device, mode, category definitions) is named and aligned.
- Nested subsamples: score against the weakest frame behind a headline claim.

## Check questions
1. Which data source kinds stand behind the headline claims?
2. For each of these sources: does the paper do what fits its kind (list above)?
3. Where waves, samples or sources are compared: is each collection difference named and aligned?
4. Are the claims limited to what the collection supports?

## Score decision
- 3: Every source behind a headline claim is characterized as fits its kind, and claims stay within it.
- 2: Mostly so. One specific omission with a clear fix, such as one unjustified weight or a benchmark that exists but is not used.
- 1: Several omissions. Or the coverage of the source behind a headline claim is unknown, and this changes how the claim should be read.
- 0: The paper does not characterize what its data cover.


---

## FILE: references/criteria/D3.md

---
row: D3
title: Valid measurement
group: Data
depends_on: [measures, headline_claims]
features:
  validated_on_own_data: "Automated measures (classifiers, LLM coding, sentiment, topic models, embeddings) are validated on the paper's own data"
  error_rates_in_main_text: "Agreement or error rates are reported in the main text"
  tools_suited_to_context: "Off-the-shelf tools and lookup resources suit the text type, language, time period and platform they are applied to"
  manual_coding_reliability: "Manual coding is reported with reliability, and weak items are flagged rather than silently dropped"
  constructed_measures_justified: "Constructed measures (indices, weights, thresholds, category schemes, proxies) are explained and justified, ideally against the obvious alternative"
  terms_defined_operationally: "Key terms are defined operationally, edge cases included"
not_here:
  - "Classifier error carried into prevalence estimates → P1"
  - "Whether a headline number holds under another threshold or weight → P1"
  - "Sampling intervals → P2"
  - "Full codebooks, prompts and keyword lists belong in the appendix; their absence from the main text is not a gap"
---

## What this criterion checks
Every measure behind a headline claim is shown to capture what it is meant to. What to look for depends on the measure kind in the context list:
- Automated measures: validation on the paper's own data, with agreement or error rates in the main text.
- Off-the-shelf tools and lookup resources (lexicons, pretrained models, outlet ratings): suited to text type, language, period and platform.
- Manual coding: reliability reported; weak items flagged.
- Key terms and constructed measures: operational definitions; justification of indices, engagement weights, thresholds, category schemes and proxies (such as vote choice for partisanship); survey items comparable across waves or countries.
- Disagreement between alternative measures is reported, not dismissed as an outlier.
Use "NA" only if no measure in the context list needs validation or justification.

## Check questions
1. Which measures stand behind the headline claims, and of which kind is each?
2. Automated measures: validated on the paper's own data, with rates in the main text?
3. Off-the-shelf tools: suited to the text type, language, period and platform?
4. Manual coding: reliability reported, weak items flagged?
5. Key terms and constructed measures: defined operationally and justified?
6. Where alternative measures disagree: is the disagreement reported?

## Score decision
- 3: Every measure behind a headline claim is shown to capture what it is meant to.
- 2: Most are. One specific omission with a clear fix: a validation described but its rate not shown, or one unjustified threshold.
- 1: Several measures are unvalidated or unjustified, or the measure behind a headline claim is and plausible error in it would change how that claim reads. One unjustified threshold or mapping with a small fix is a 2.
- 0: No measure is validated or justified.


---

## FILE: references/criteria/P1.md

---
row: P1
title: Robustness to analytic choices
group: Presentation and analysis
depends_on: [headline_claims, measures]
features:
  alternatives_reported: "Headline numbers are shown under reasonable alternatives (thresholds, weights and mappings, snapshot timing, minimum-activity cutoffs, time windows, aggregation level)"
  sensitivity_shown_where_fragile: "Where a headline number depends on a choice, its sensitivity is shown rather than left out"
  classifier_error_carried_through: "Classifier error is carried into prevalence estimates"
  checks_findable: "Robustness results are findable in the text or an appendix, not only mentioned"
not_here:
  - "Whether a measure is valid in the first place → D3"
  - "Sampling intervals and variation across units → P2"
  - "How a data limitation moves an estimate → C4"
---

## What this criterion checks
Headline numbers are shown to hold, or their sensitivity is shown, under reasonable alternative analytic choices.
The choices that matter: thresholds, weights and mappings, snapshot timing, minimum-activity cutoffs, time windows, aggregation level (pooled vs. per unit).
The results may sit in the text or in an appendix.
Classifier error carried into prevalence estimates belongs here.
A check that the paper describes but does not show is usually a small writing fix.
Do not ask for every possible check. Ask for the ones a headline number plausibly depends on.
A paper with few consequential choices has little to check; that is not a failure on this criterion.

## Check questions
1. Which analytic choices stand behind each headline number?
2. For which of these choices does the paper show that the number holds, or show its sensitivity?
3. Which checks are described but not reported?
4. If a classifier produces a prevalence: is its error carried into the estimate?

## Score decision
- 3: The consequential choices behind the headline numbers are checked and the results are findable.
- 2: Most are. One check is missing, or described but not reported.
- 1: Several consequential choices are unchecked, or a headline number plausibly changes under an obvious alternative that is not examined.
- 0: A headline number depends on a consequential analytic choice, and the paper checks none of its choices.
- A paper whose headline numbers rest on few consequential choices (for example, counts from a complete archive) is not scored 0 for a missing check. Score 2 or 3 and record any small check as a gap.


---

## FILE: references/criteria/P2.md

---
row: P2
title: Uncertainty and variation
group: Presentation and analysis
depends_on: [headline_claims, data_sources]
features:
  intervals_for_headline_numbers: "Headline numbers carry intervals or the relevant variation, with the interval type stated"
  intervals_in_prose: "Intervals appear in the text, not only in figures"
  n_for_subgroups: "n is given for the subgroups behind headline claims"
  distributions_for_skew: "Skewed quantities are reported as distributions (medians, share at zero, concentration), not only as means"
  variation_across_units: "Group-level claims that rest on few units show the variation across those units"
not_here:
  - "Robustness to analytic choices → P1"
  - "A claim that outruns the evidence → C3"
  - "Ns of the dataset and its filtering steps → D1"
---

## What this criterion checks
Key quantities carry the relevant variation.
For surveys and samples this is a sampling interval.
When a group-level claim rests on few units (platforms, outlets, countries), it is the variation across those units.
For census-scale counts sampling error is trivial; look for the variation that matters instead.
Group differences are not asserted without that variation.
Intervals appear in prose as well as figures, with the interval type stated and n given for subgroups.
Skewed quantities are reported as distributions: medians, share at zero, concentration such as "the top x% account for y%".

## Check questions
1. Which headline claims rest on a number?
2. Does each of these numbers carry the relevant variation for its data source kind?
3. Do intervals appear in the prose, with the interval type stated and n for subgroups?
4. Is any difference between groups asserted without that variation?
5. Are skewed quantities reported as distributions, not only as means?

## Score decision
- 3: All headline numbers carry the relevant variation, and no group difference is asserted without it.
- 2: Variation is present for most headline numbers. The gaps are specific: intervals only in figures, one subgroup without n, one skewed quantity as a mean.
- 1: Several headline numbers lack variation. Or a group difference that is a headline claim has no variation, and is small enough that variation could change it.
- 0: No variation or uncertainty is reported anywhere.


---

## FILE: references/criteria/P3.md

---
row: P3
title: Findings-first presentation
group: Presentation and analysis
depends_on: [orientation, headline_claims, sections]
features:
  title_names_what_where_when: "The title names what is described, where and when, and often the headline finding"
  abstract_data_then_findings: "The abstract says within its first sentences what is described and from what data (source, scale, place, period), then gives headline findings with numbers"
  intro_previews_findings: "The introduction states the aim early and previews the findings, ideally in results order"
  sections_open_with_finding: "Each results section opens with its finding and has a takeaway (claim- or question-style headings, topic-sentence findings, a \"taken together\" sentence)"
  methods_in_one_place: "Methods sit in one findable place"
not_here:
  - "Whether the aim is clear and stays primary → A1"
  - "Generic tutorials, space and length → P4"
  - "Abstract length → P4"
  - "The layout type as such → never a gap; the journal requires no structure"
---

## What this criterion checks
Readers find the findings first.
The title names what is described, where and when, and often the headline finding.
The abstract says what is described and from what data, then gives a few headline findings with numbers where they exist.
The introduction states the aim early and previews the findings.
Results are organized around findings, research questions or units of analysis. Each section opens with its finding and has a takeaway.
Methods sit in one findable place.
Results ordered by technique, with no takeaway per section, score lower.
Any of the six common layouts can meet this criterion.

## Check questions
1. Does the title name what is described, where and when?
2. Does the abstract give data (source, scale, place, period) in its first sentences and then headline findings with numbers?
3. Does the introduction state the aim early and preview the findings?
4. Does each results section open with its finding and have a takeaway?
5. Do the methods sit in one findable place?

## Score decision
- 3: Questions 1–5 are yes, or one is partly met.
- 2: Findings are easy to find. One or two contained gaps: an abstract without numbers, no preview in the introduction, one section without a takeaway.
- 1: Results are ordered by technique with no takeaway per section, and the findings are not in the abstract or the introduction. Either problem alone is a 2.
- 0: A reader cannot locate the findings without reading the full results.


---

## FILE: references/criteria/P4.md

---
row: P4
title: Length and economy
group: Presentation and analysis
depends_on: [orientation, metrics, sections]
features:
  length_matches_delivery: "Main-text length matches what the paper delivers"
  space_on_substance: "Space goes to population, sampling, findings, validity, careful comparisons and limitations"
  detail_in_appendix: "Detail such as codebooks, full prompts and keyword lists sits in an appendix"
not_here:
  - "Background that never narrows → C2"
  - "Order of findings and placement of methods → P3"
  - "A figure or caption that is unclear → P5"
---

## What this criterion checks
Main-text length matches what the paper delivers. Use the size line and length norms in the context as context, not as rules.
Length outside the norms alone is not a gap. Say what the extra length goes to, or what a short paper leaves out.
Space should go to population, sampling, findings, validity, careful comparisons and limitations.
Space should not go to: tutorials on standard techniques; advertising a tool's reusability; tool comparisons presented as findings; raw lists of items in main-text tables; loosely related analyses stacked together.
Detail sits in an appendix.

## Check questions
1. How does the main-text length compare with the norms for this paper type, and does it match what the paper delivers?
2. Which passages (with pages) spend space on the five kinds of material listed above?
3. Does detail such as codebooks, prompts and keyword lists sit in an appendix?

## Score decision
- 3: Length matches delivery, and no notable passage is of the five kinds.
- 2: One or two passages could be cut or moved to an appendix; the paper otherwise uses its space on substance.
- 1: A substantial share of the main text is material of the five kinds. Or the length is far from the norms and the paper does not deliver correspondingly more or less.
- 0: Most of the main text is material of the five kinds.


---

## FILE: references/criteria/P5.md

---
row: P5
title: Self-contained figures and tables
group: Presentation and analysis
depends_on: [figure_map, metrics, headline_claims]
features:
  captions_say_what_is_plotted: "The caption, or the paragraph introducing the figure, says what is plotted, the N, and what panels, colours, marks and reference lines encode"
  takeaway_in_caption: "Captions often state the takeaway"
  labelled_exemplars: "A few labelled exemplars (typical, extreme, exception) anchor distributions"
  denominators_named: "Percentages name their denominator, and overlapping categories are flagged"
  axes_plain_language: "Axes are labelled in plain language and carry meaning, or the paper explains why they do not"
  cross_references_correct: "Figures are referenced by number, and cross-references to figures, tables and sections are correct"
not_here:
  - "Text and a figure disagree about a result → C3"
  - "Intervals missing from a figure → P2"
  - "A comparison point or benchmark line missing → C1"
  - "Main-text tables that are raw lists of items → P4"
---

## What this criterion checks
A reader can understand each figure and table from its caption or from the paragraph that introduces it.
You see captions and text, not the images. Judge captions, the introducing paragraphs and the cross-references. Do not state what an image shows or lacks unless the text says so.
The context lists every figure and table with its caption, the claims each supports, and the cross-references the script could not resolve.
The listed possible broken cross-references come from pattern matching and are often wrong (supplementary items, footnote markers like "Table 312").
Check each with `review.py find`. Report only references that point to nothing, in one "minor" item with category "cross_references": "Table 7 (p. 12) does not exist."
"??" references are already reported by the script.
Start with the figures that support headline claims.
Three small caption problems are a 2, not a 1. Collect single caption slips under "minor" with category "figures".

## Check questions
1. For the figures behind headline claims: do caption or introducing paragraph say what is plotted, the N and what the encodings mean?
2. Do percentages name their denominator, and are overlapping categories flagged?
3. Is what each caption claims consistent with how the text describes the figure?
4. Are axes and units described in plain language where the text or caption mentions them?
5. Are figures and tables referenced by number, and are the cross-references correct?

## Score decision
- 3: The figures behind headline claims are self-contained, and cross-references are correct.
- 2: Mostly so. A few captions lack the N, an encoding or a denominator, or a few cross-references are wrong.
- 1: The figures behind headline claims cannot be read without searching the text, or the problems run through most figures.
- 0: Figures and tables have no usable captions.


---

## FILE: references/criteria/C1.md

---
row: C1
title: Delivers on the question
group: Contribution and claims
depends_on: [orientation, headline_claims, figure_map]
features:
  citable_baseline_numbers: "Findings are reported in a form others can cite as a baseline: a prevalence, distribution, concentration, trend or comparison, with numbers"
  comparison_point_per_headline_number: "Each headline number has a comparison point (a prior estimate, an external benchmark, an equality or chance baseline, a reference group or year), drawn into the figure where possible"
  more_than_one_unit: "Key quantities are reported for more than one unit where they can diverge (people vs. activity, count vs. spend)"
  nulls_reported_as_findings: "Null and smaller-than-expected results are reported as findings, framed against what was expected"
  returns_to_motivating_assumption: "The paper is motivated by a common assumption or missing baseline and returns to it with the measured number"
  ending_says_what_changes: "The ending restates the headline numbers, what they change about how readers should see the platform, and which questions are now answerable"
not_here:
  - "Whether the question is stated clearly → A1"
  - "Whether the question matters → out of scope; never a gap"
  - "Prior work missing from the paper → C2"
  - "Claims stronger than the evidence → C3"
  - "Missing intervals or variation → P2"
---

## What this criterion checks
The findings directly answer the accepted question.
They are reported in a form others can cite as a baseline, with numbers. Some papers add a table of key values.
Strong papers give each headline number a comparison point and report nulls as findings.
Strong papers end on what the numbers change, rather than only restating numbers or arguing that the data or method is viable.

## Check questions
1. Do the headline claims directly answer the primary aim in the context?
2. Is each headline claim reported in a citable form with numbers?
3. Does each headline number have a comparison point?
4. Are null and smaller-than-expected results reported as findings?
5. Does the ending say what the headline numbers change?

## Score decision
- 3: The findings answer the question in citable form, and most headline numbers have a comparison point.
- 2: The findings answer the question with numbers. Specific omissions: one headline number without a comparison point, or an ending that only restates.
- 1: The question is only partly answered, or the headline findings come without numbers or citable form.
- 0: The findings do not answer the stated question.


---

## FILE: references/criteria/C2.md

---
row: C2
title: Literature matched to the scope of the claims
group: Contribution and claims
depends_on: [orientation, headline_claims, sections]
features:
  scope_matched: "The breadth of the literature matches the breadth of the claims"
  cited_work_bears_on_findings: "Cited work bears on the measures and the findings"
  prior_estimates_next_to_new_numbers: "Prior estimates are brought into the results, next to the new number they are compared with"
not_here:
  - "Space taken by tutorials or tool material → P4"
  - "Citation format and reference-list completeness → C5"
  - "Comparison points for headline numbers as such → C1"
---

## What this criterion checks
A narrow descriptive finding can rest on a short, closely related set of citations. A broader claim needs a broader literature.
Cited work bears on the measures and findings.
Lower the score when the literature is broader than the claims (background that never narrows), narrower than them, or misses closely related work.
Rule for missing work: say that related work is missing only if you can name it (works, authors, datasets, or a specific kind of study).
Name the works in the fix, for example "Engage with Author (Year) on …". Do not add a caveat; the script prints one under this criterion.
If you cannot name anything specific, do not list a gap for missing work and do not lower the score for it.

## Check questions
1. How broad are the headline claims: a narrow descriptive finding, or a broader claim?
2. Is the cited literature broader than the claims, narrower, or matched?
3. Does the cited work bear on the measures and findings?
4. Are prior estimates brought into the results next to the new numbers?
5. Which specific, closely related work is missing? Answer "none named" if you cannot name any.

## Score decision
- 3: The literature matches the scope of the claims and bears on measures and findings.
- 2: Matched overall. One specific gap: prior estimates stay in the background section, or one part of the background never narrows.
- 1: The literature is clearly broader or narrower than the claims throughout. Missing related work you can name is a 2, unless it reports an estimate that would change how a headline claim reads.
- 0: The paper does not engage with related work.


---

## FILE: references/criteria/C3.md

---
row: C3
title: Claims match evidence
group: Contribution and claims
depends_on: [headline_claims, figure_map]
features:
  abstract_matches_body: "Abstract and conclusion state as findings only what the body treats as findings"
  text_matches_figures: "Numbers and statements in the text match the figures and tables they cite"
  generalizations_within_units: "Generalizations stay within the units observed"
  closing_within_evidence: "Closing rhetoric stays within the evidence"
not_here:
  - "Causal wording or a causal design → A2"
  - "A caption that does not describe its own figure → P5"
  - "How a limitation moves an estimate → C4"
  - "Missing intervals → P2"
---

## What this criterion checks
The abstract and conclusion do not state as findings results the body calls tentative.
Text matches figures and tables.
Things that were not measured are not asserted.
Generalizations do not outrun the units observed.
Closing rhetoric stays within the evidence.
This criterion is the home for text–figure mismatches and overclaiming.
A single abstract sentence that states a tentative result too firmly is a 2 with a small wording fix.
The context shows each headline claim with its status (firm or tentative) and the figures that support it.

## Check questions
1. For each headline claim: does the body support it as firmly as the abstract and conclusion state it?
2. Do the numbers and statements in the text match the figures and tables they cite?
3. Is anything asserted that was not measured?
4. Do generalizations go beyond the units observed (platforms, countries, periods, account types)?
5. Does the closing rhetoric stay within the evidence?

## Score decision
- 3: Claims match the evidence throughout.
- 2: One contained mismatch between text and a figure, or one overreaching sentence. This includes a single abstract or conclusion sentence that a change of wording fixes.
- 1: Several overclaims or mismatches, or one that reverses or misstates a finding the body reports.
- 0: The headline claims are not supported by the evidence shown.


---

## FILE: references/criteria/C4.md

---
row: C4
title: Specific limitations
group: Contribution and claims
depends_on: [data_sources, measures, headline_claims]
features:
  threat_tied_to_estimates: "Each important threat is tied to the particular estimates it affects"
  direction_stated: "The paper says whether a threat would push the estimates up or down"
  limitations_findable: "The important limitations are findable: where the affected number is reported, in a headed section, or both"
not_here:
  - "What the data cover in the first place → D2"
  - "Overclaiming → C3"
  - "Sensitivity analyses → P1"
  - "A threat already recorded as a gap under D2, D3 or P1 → that criterion; here note at most its missing direction, without lowering C4 again"
---

## What this criterion checks
The paper says how each important threat would affect particular estimates, and whether it would push them up or down.
Saying only that limitations exist is not enough.
Limitations can sit where the affected number is reported, in a headed section, or both. Placement does not matter as long as the important ones are findable.
Few published papers quantify the size of a bias. Do not require it.

## Check questions
1. Which threats matter most for the headline claims, given the data sources and measures in the context?
2. For each of them: does the paper say which estimates it affects?
3. Does the paper say in which direction the estimates would move?
4. Are the important limitations findable?

## Score decision
- 3: The important threats are tied to estimates, with direction.
- 2: Most are. One important threat is named only in general terms.
- 1: Limitations are generic throughout and an important threat to a headline claim is not mentioned anywhere in the paper. Generic limitations alone, or one unmentioned threat with an otherwise specific discussion, are a 2. A threat already recorded as a gap under D2, D3 or P1 does not lower C4 again; note only the missing direction here.
- 0: The paper discusses no limitations.


---

## FILE: references/criteria/C5.md

---
row: C5
title: Transparency and end matter
group: Contribution and claims
depends_on: [metrics, data_sources]
features:
  keywords_present: "Keywords are given"
  availability_statement: "A data and code availability statement is given (sharing aggregates, IDs or a licensing route is acceptable when terms of service or privacy prevent more)"
  acknowledgments_and_funding: "Acknowledgments and funding are stated"
  ethics_information: "Ethics or IRB information is given when human subjects or sensitive data are involved"
  citations_consistent: "Citations are consistent author-year, and every in-text citation is in the reference list"
not_here:
  - "Whether related work is missing → C2"
  - "Wrong references to figures, tables or sections → P5"
---

## What this criterion checks
End matter: keywords; a data and code availability statement; acknowledgments and funding; ethics or IRB information when human subjects or sensitive data are involved; consistent author-year citations with every in-text citation in the reference list.
Missing end-matter items are small writing fixes. Several missing items make a 2, not a 0.
If the manuscript is anonymized for review, acknowledgments and funding may be withheld on purpose. Mark that feature "not_applicable" and do not list a gap.
There is no automated citation check. Note a missing reference only when you have confirmed it with `find`.
Do not copy names from the acknowledgments into your answer.

## Check questions
1. Are keywords given?
2. Is there a data and code availability statement?
3. Are acknowledgments and funding stated, or visibly withheld for blind review?
4. Is ethics or IRB information given where human subjects or sensitive data are involved?
5. Are citations consistent, and is every in-text citation in the reference list?

## Score decision
- 3: All applicable items are present.
- 2: One or more items are missing; each is a small writing fix.
- 1: Neither an availability statement nor needed ethics information is given, and citation problems are widespread.
- 0: The paper has no end matter and no reference list.
