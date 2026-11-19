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
