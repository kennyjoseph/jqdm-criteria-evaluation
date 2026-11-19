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
