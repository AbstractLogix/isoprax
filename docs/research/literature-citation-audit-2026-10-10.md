# Literature and citation audit — 2026-10-10

This is a targeted audit through 2026-10-10, not a systematic review. It preserves the checked records from the 2026-10-09 audit and adds the foundational construct-validity and measurement-invariance citations used in the adversarial review. We checked title, author list, venue/year, DOI or archival record, and whether the paper supports the sentence that cites it. Primary publication or author records were preferred.

## Audit of the prior manuscript references

| Reference | Record checked | Use in revised paper | Audit result |
|---|---|---|---|
| Chen et al., AIOpsLab (2025) | [arXiv:2501.06706](https://arxiv.org/abs/2501.06706) and project artifact | Operational benchmark environment | Bibliographic record and use are consistent. Supports infrastructure description, not outcome equivalence. |
| Shetty et al. (2024) | [SoCC DOI](https://doi.org/10.1145/3698038.3698525) | AIOps evaluation vision and design | Supports environment motivation and design, not cross-family commensurability. |
| Yang et al., AOI (2026) | [arXiv:2603.03378](https://arxiv.org/abs/2603.03378) | Recent autonomous-cloud diagnosis work evaluated with AIOpsLab | Preprint. It reports a specific operational task and its own held-out fault evaluation; it does not pair outcomes with JIT targets or establish cross-family comparability. |
| Ni et al., JIT-Fine (2022) | [Official ESEC/FSE record](https://2022.esec-fse.org/details/fse-2022-research-papers/87/The-Best-of-Both-Worlds-Integrating-Semantic-Features-with-Expert-Features-for-Defec) | JIT prediction/localization example | Title, authors, venue, pages, DOI checked. It studies JIT-DP and JIT-DL; it does not validate operational outcomes. |
| Nam et al., ReDef (2026) | [FSE 2026 proceedings record](https://conf.researchr.org/details/fse-2026/fse-2026-research-papers/143/ReDef-Do-Code-Language-Models-Truly-Understand-Code-Changes-for-Just-in-Time-Softwar) and [DOI](https://doi.org/10.1145/3808179) | JIT label and code-change example | Correct final record is *Proceedings of the ACM on Software Engineering*, 3(FSE), Article FSE172, pp. 3909–3930, DOI 10.1145/3808179. Do not cite the preprint's differing title as the final title. |
| Lyu et al., data splitting (2021) | [TOSEM DOI](https://doi.org/10.1145/3447876) and author PDF | Evaluation sensitivity | Supports split choices affecting AIOps evaluation. It does not support cross-family target mismatch. |
| Lyu et al., interpretation (2022) | [TOSEM DOI](https://doi.org/10.1145/3488269) and author PDF | Interpretation stability | Supports consistency concerns in AIOps interpretation. It is not a target-equivalence study. |
| Poenaru-Olaru et al. (2024) | [ICSE SE4AI DOI](https://doi.org/10.1145/3644815.3644961) and author PDF | Temporal adaptation and drift | Supports adaptation and real-world change questions, not commensurability. |

## Added foundational and methods references

| Area | Source | What it supports | Boundary |
|---|---|---|---|
| Calibration | Guo et al. (2017), [PMLR ICML record](https://proceedings.mlr.press/v70/guo17a.html) | Confidence calibration and post-processing methods for neural-network outputs. | Studies its stated classification targets; does not equate distinct events. |
| Proper scoring | Gneiting and Raftery (2007), [JASA DOI](https://doi.org/10.1198/016214506000001437) | Proper scoring rules assess forecasts against outcomes. | Does not establish that different outcome variables have the same meaning. |
| Forecast pooling | Bates and Granger (1969), [DOI](https://doi.org/10.1057/jors.1969.103); Ranjan and Gneiting (2010), [DOI](https://doi.org/10.1111/j.1467-9868.2009.00726.x) | Forecast combination is a developed research area; dependence and combination form matter. | These methods assume a defined combination task. They are not evidence that arbitrary targets can be pooled. |
| Construct validity | Bean et al. (2025), [arXiv:2511.04703](https://arxiv.org/abs/2511.04703) | Recent review of construct-validity concerns in LLM benchmarks. | Preprint; not treated as settled consensus or evidence about IsoPrax directly. |
| Forecast calibration sequences | Wilkinson and Ferro (2026), [arXiv:2606.31621](https://arxiv.org/abs/2606.31621) | Extends auto-calibration analysis to repeated forecasts of a fixed observation and tests properties on sequences. | Preprint. It studies forecasts for the same observation; it does not establish equivalence between distinct outcome definitions. |
| Construct validity | Cronbach and Meehl (1955), [Psychological Bulletin DOI](https://doi.org/10.1037/h0040957) | Foundational account of construct validity and nomological networks. | Establishes why interpretations need evidence; it does not supply IsoPrax's typed operation interface. |
| Measurement invariance | Vandenberg and Lance (2000), [Organizational Research Methods DOI](https://doi.org/10.1177/109442810031002) | Reviews measurement-invariance practice and tests across groups. | Supports the novelty objection; it does not itself evaluate this software contract. |
| Data/label validity | Herbold et al. (2022), [Empirical Software Engineering DOI](https://doi.org/10.1007/s10664-021-10092-4) | Documents SZZ and feature data-collection problems in defect prediction. | Supports caution about JIT labels; does not adjudicate any IsoPrax outcome declaration. |
| Provenance | W3C, [PROV-DM](https://www.w3.org/TR/prov-dm/) | Vocabulary for provenance relations. | Provenance representation does not prove truth or measurement validity. |
| Evidence admission and formal conformance | IsoPrax Feature 014 specification and `isoprax/commensurability.py`; ACM SIGSOFT empirical/artifact guidance | The repository has a typed outcome declaration and executable equality/mismatch check; artifact guidance informs reproducibility. | This is a repository contract audit, not a systematic survey of formal verification, proof-carrying data, or evidence-admission systems. No novelty claim is made for formal conformance as a general idea. The current checker verifies declarations, not their truth. |
| Dataset/model reporting | Gebru et al. (2021), [CACM DOI](https://doi.org/10.1145/3458723); Mitchell et al. (2019), [Model Cards preprint](https://arxiv.org/abs/1810.03993) | Reporting context and limitations for datasets and models. | Reporting templates do not independently validate a construct. |
| Reproducibility | ACM SIGSOFT, [Empirical Standards](https://www2.sigsoft.org/EmpiricalStandards/) and [Artifact Evaluation](https://github.com/acmsigsoft/artifact-evaluation) | Expectations for empirical-software evidence and artifacts. | Automated artifact checks are not scientific peer review. |

## Positioning

The calibration/target relationship is not a novel statistical discovery. Forecast pooling is not new. The candidate IsoPrax contribution is narrower: encode outcome declarations and requested operations in an implementation-independent contract, provide an executable conformance check, and publish a falsifiable synthetic challenge that includes both valid and invalid operations. Novelty and practical value require independent review.
