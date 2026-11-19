# Calibration anchors

One file per criterion, three or four anchors each, with a 2/1 pair where the source papers allow it. Several are boundary cases on purpose.

**Status: agreed (2026-11-16), switched on.** The scripts show a criterion's anchors in its task block when the file has `status: agreed` in its frontmatter. Set a file back to `status: draft` to switch its anchors off.

These anchors are paraphrased from ten published JQD:DM papers, plus a few synthetic ones where no paper showed the case (published papers rarely score 0 or 1). They are anonymized: this folder is distributed to authors, who may include the source papers' authors. Leave out titles, platform–year–N combinations and anything else that identifies a paper. The map from anchor to source is kept outside this folder. Keep the format `**<code> · Score <n>.** <situation> *Justification:* <one sentence>`.

Every change to an anchor or criterion file should be followed by a regression run on at least two test manuscripts (see `tests/README.md`).
