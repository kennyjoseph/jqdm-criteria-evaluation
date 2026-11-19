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
