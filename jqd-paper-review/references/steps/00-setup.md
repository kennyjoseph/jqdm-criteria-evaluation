# Step 0 · Setup (script only)

## Task
Run `review.py init` once to extract the text, count its parts and build the section map.

## Rules
- Command: `python <skill-folder>/scripts/review.py init --manuscript FILE [--loi FILE] [--appendix FILE] [--depth full|compact] [--workdir DIR]`.
- Accepted file types: PDF, DOCX, Markdown, plain text.
- The script creates the working directory `jqd-review-<run-id>/` with `state.json`, `text/`, `metrics.json`, `answers/` and `out/`.
- If the script reports pages without text, ask the user for a text version or an OCR'd PDF. Do not continue with a guess.
- After `init`, always run the command printed after `NEXT COMMAND:`.

## Fields
No answer file. The script writes `meta`, `metrics`, `sections` and `steps` in `state.json`.
