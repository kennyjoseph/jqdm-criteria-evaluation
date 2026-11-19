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
