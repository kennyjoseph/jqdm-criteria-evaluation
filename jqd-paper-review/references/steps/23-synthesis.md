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
