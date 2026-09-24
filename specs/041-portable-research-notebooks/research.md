# Research: Guided Research Notebooks

## Decisions

### 1. Keep portable Jupyter and the verifier as the entry gate

**Decision**: Preserve the standard version-4 notebooks, isolated locked kernel, local-only path convention, headless execution gate, and existing Isoprax verifier/report projections. Expand only the post-verification exploration.

**Rationale**: Verification establishes the identity and structural integrity of the exact artifact before descriptive or model analysis. The notebooks should reuse that authority while showing the data behind the summary charts.

**Alternatives considered**: A second loader/verifier path would risk disagreeing with Isoprax checks. Downloading through a notebook helper or `ucimlrepo` would make the research path network-dependent and obscure the verified local artifact.

### 2. Keep raw-data analysis read-only, optional, and testable

**Decision**: Add pandas only to the optional notebook extra. Put deterministic split, metric-support, and alignment primitives in `notebooks/_analysis.py`; keep feature selection, model pipelines, and dataset-specific interpretation visible in notebook cells. Test helpers only on clearly labeled synthetic fixtures.

**Rationale**: Tabular exploration is materially clearer with data frames. pandas supports streaming the 208 MB MetroPT-3 file in bounded chunks. Tests of analytical mechanics do not require checking in or downloading benchmark data.

**Alternatives considered**: Implementing all summaries in the verifier would mix research display with artifact validation. Loading all of MetroPT-3 into memory or materializing another dataset copy is unnecessary. Fabricated benchmark examples would be easy to mistake for public-dataset evidence.

### 3. AI4I 2020: describe label construction and use an ordered holdout

**Decision**: Show composite/mode prevalence, overlap/discrepancies, and feature distributions. For an illustrative binary baseline, order by UDI and hold out the final 20%; do not describe UDI as observed production time. Exclude UDI, Product ID, and all mode-label columns from the composite-failure predictors. Compare one logistic-regression pipeline with a constant-prior baseline; report prevalence, average precision, ROC-AUC when both classes are present, Brier score, and a fixed-threshold confusion table.

**Rationale**: UCI identifies the data as synthetic and time-series-like, labels the six outcomes as targets, and describes composite machine failure as the union of five failure modes. IDs and mode labels would leak identity/outcome information into the illustrative composite target. An ordered holdout avoids an adjacent-row random split while remaining explicitly non-production evidence.

**Alternatives considered**: Random row splitting could put adjacent generated records on both sides. Treating failure-mode labels as input features would directly leak label construction. A pooled cross-family score has no coherent target.

**Source**: [UCI AI4I 2020 dataset record](https://archive.ics.uci.edu/dataset/601/ai4i%2B2020%2Bpredictive%2Bmaint), especially its Additional Variable Information and Variables Table.

### 4. ApacheJIT: use a release-aligned time boundary and commit metrics only

**Decision**: Show class balance and project/year positive yields; build one logistic-regression diagnostic from the 12 commit metrics only. Split the pinned `apachejit_total.csv` by parsed `author_date` at 2017-01-01 UTC: earlier records train, later records test. Report the cutoff, row/class support, model versus constant-prior metrics, and per-project test support. Never use `buggy`, `fix`, identifiers, project, or date fields as predictors. Surface the known year/epoch mismatch count and base ordering on parsed epoch timestamps.

**Rationale**: The ApacheJIT Zenodo record describes `apachejit_total.csv` as the complete dataset, `buggy` as the target, and a time-ordered design with 2003–2016 training history and the last three years as an imbalanced future test. The repository has pinned the total artifact and verifier, rather than the separately balanced train CSV; deriving the boundary from `author_date` retains the full pinned artifact and does not balance the test. The current verifier independently reports 53,487 timestamp inversions in source row order and 1,314 year/epoch mismatches, so source row order and `year` cannot silently define the split.

**Alternatives considered**: Random row split mixes past/future commits. The separately distributed balanced `apachejit_train.csv` changes prevalence and is not the repository-pinned `total.csv` artifact. Project identity, fix status, and commit date are not available commit metrics for the target prediction.

**Source**: [ApacheJIT Zenodo v1 record used by the repository](https://zenodo.org/records/5907002); [newer ApacheJIT Zenodo v2 record](https://zenodo.org/records/5907847). The v2 record still describes the full dataset, balanced 2003–2016 train subset, and unbalanced final-three-years test subset. The repository remains pinned to its existing v1 artifact until a separate verifier/data-snapshot change is reviewed.

### 5. NASA C-MAPSS: derive train RUL and use official test RUL per subset

**Decision**: For each FD001–FD004 subset independently, display unit counts, train life/RUL distributions, and selected sensor traces. Derive each training row's RUL as that training unit's final cycle minus the row cycle. Fit a fixed HistGradientBoostingRegressor on training sensor/settings/cycle features with unit ID excluded. Evaluate only the final observed row of each official test unit against the matching official RUL vector; compare to a training-label median predictor and report MAE/RMSE. Do not tune on the test labels or average results across subsets.

**Rationale**: NASA describes training trajectories as separate engines run to failure and test trajectories as different engines that stop before failure, with a true RUL value supplied for each test case. This supports a held-out engine-level RUL demonstration without synthesizing operational labels. FD subsets differ in conditions and fault modes and remain independently reported.

**Alternatives considered**: Random row splitting would leak repeated trajectory rows between train and validation. Treating test cycles as run-to-failure would invent labels. Pooling FD errors would obscure condition/fault-mode differences.

**Source**: [NASA C-MAPSS dataset record](https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data), including the train/test description and FD001–FD004 population summaries.

### 6. MetroPT-3: visualize anchors and preserve censoring; do not score a predictor

**Decision**: After verification, stream only timestamp and selected sensor columns in 100,000-row chunks. Compute exact count-weighted hourly means for the full stream and minute means only within bounded six-hour context windows around each externally reported interval. Measure timestamp cadence from the verifier's observed adjacent-gap counts. Shade only the reported intervals; rows outside those anchors remain unlabeled/censored. Do not construct a supervised train/test score from these interval anchors.

**Rationale**: UCI describes the stream as unlabeled with a small table of company failure reports and suggests a time split for learning. However, those reports do not label the non-event state or establish complete event coverage; the local Isoprax manifest and verifier explicitly preserve the external-anchor/censoring boundary. The UCI page also gives conflicting nominal sampling descriptions (1 Hz and 0.1 Hz), so notebooks must display cadence measured from the verified file rather than assume a fixed rate.

**Alternatives considered**: Converting every row outside the reports to a negative label creates unsupported supervision. A full in-memory load needlessly increases peak memory. Plotting a single whole-file unaggregated trace hides interval structure.

**Source**: [UCI MetroPT-3 dataset record](https://archive.ics.uci.edu/dataset/791/metropt3%2Bdataset), especially Failure Information, recommended split, and sampling description.

### 7. Keep metrics descriptive and claims bounded

**Decision**: Baselines are fixed, single-pass methodological examples. Classification reports average precision, ROC-AUC only when both test classes exist, Brier score, support, prevalence, and one prespecified 0.5-threshold confusion table. RUL reports MAE/RMSE and support. Missing support produces an explicit not-estimable reason. Every result is labeled as exploratory and local to its dataset/split; no result upgrades Isoprax conformance or claims real-world efficacy.

**Rationale**: These corpora have different outcomes and observation processes. Metrics can be useful within one declared label/split but cannot make labels cross-family commensurable. AI4I is synthetic; ApacheJIT labels are repository-derived; C-MAPSS is simulated; MetroPT-3 labels depend on external reports.

**Alternatives considered**: Single accuracy is uninformative for imbalanced labels. Reporting an undefined metric as zero confuses lack of support with measured performance. Calibrating scores does not repair different outcome definitions.
