# Research: Evidence Metric Integrity

`_macro_precision` counted selected positives, but the result fields and
documentation called it recall. `_family_rows` assigned one score to every row,
so `_top_k` selected positives only because IDs were sorted after the score tie.
The repair keeps precision and makes the ranking signal explicit.
