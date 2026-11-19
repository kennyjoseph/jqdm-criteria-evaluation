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
