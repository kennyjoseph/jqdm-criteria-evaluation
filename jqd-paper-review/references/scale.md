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
