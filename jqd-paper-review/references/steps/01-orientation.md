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
