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
