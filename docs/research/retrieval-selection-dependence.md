# Retrieval and Interpretation Dependence

**Status**: Research proposal with a completed, bounded synthetic pilot. The full replay did not match; see the [results report](retrieval-selection-dependence-results.md). The separate model-role experiment remains pending.
**Paper reviewed**: UNREAL arXiv version 1, submitted 6 October 2026.

## Research question

When one learned representation or model selects evidence and the same model later interprets it, can errors in selection and interpretation become dependent in a way that changes a downstream evidence operation?

This is an IsoPrax hypothesis. It is not a finding of the paper reviewed here.

## What the paper reports

The paper title is *UNREAL: Unifying Retrieval and Long-Context with a Single Model*. Its authors use a frozen language model to encode candidate chunks and form retrieval queries from its internal states. A small trained retrieval module ranks chunks. The same frozen model then generates an answer from the selected text. The paper evaluates retrieval on public question-answering benchmarks and evaluates answer quality and efficiency on long-context tasks. It reports gains on several retrieval and long-context measures.

The paper tests whether one model-internal selector can serve both corpus retrieval and long-context selection. On a 3-billion-token, 21-million-chunk Wikipedia index, it reports retrieval results across eight question-answering data sets. Its abstract reports that the best model raises recall@10 from 49.1% to 73.2% on HotpotQA, from 31.7% to 60.1% on 2WikiMultiHopQA, and from 8.8% to 14.4% on MuSiQue. It also reports NoLiMa accuracy rising from 1.0% to 24.83% at 128K tokens and LV-Eval F1 rising from 49.97% to 54.66% at 256K. These are paper-reported results for its tested settings.

The paper reports retrieval recall and end-task answer scores. It does not report conditional error rates between selection and interpretation, source validity, evidence independence, calibration of retrieval scores as evidence confidence, or permission to combine evidence from different selectors. The paper also notes limits in domain and language transfer and studies a single-pass retrieval stage rather than a full iterative reasoning pipeline.

The paper's results support a retrieval-performance claim for its tested models, datasets, and settings. They do not establish that shared model identity makes evidence more or less trustworthy, that two selectors provide independent corroboration, or that one model identity makes targets commensurable.

The request that prompted this work gives a different expansion of UNREAL. This note uses the title and method stated in arXiv version 1.

Source: [UNREAL, arXiv:2610.08463v1](https://arxiv.org/abs/2610.08463v1) and [full text](https://arxiv.org/html/2610.08463v1).

## IsoPrax hypotheses

The proposed experiment tests these claims:

- **H1 — correlated failure**: Under at least one misleading-evidence condition, a same-model selector and interpreter have more dependent errors than a pipeline with a separate selector or interpreter.
- **H2 — retrieval is not epistemic reliability**: Better retrieval recall does not by itself establish more reliable interpretation or more trustworthy evidence.
- **H3 — evidence budget**: More selected items may help, have no effect, or harm interpretation. The study must test these outcomes and must not assume an inverted-U.
- **H4 — lineage and independence**: Selector and interpreter lineage may affect the validity of an independence claim. Model identity alone may also be too coarse to explain the errors.
- **H5 — simpler rule may suffice**: A source-lineage or metadata rule may perform as well as an operation-specific rule. The experiment must try to falsify the need for added complexity.

H1-H5 remain hypotheses. The protocol in [the benchmark specification](retrieval-selection-dependence-benchmark.md) defines the test.

## Evidence classes

### Established in this repository

Feature 046 ran deterministic synthetic tests of outcome commensurability and shared predictor identity. It found that one shared JEPA backend did not make different event families or horizons poolable in those fixtures. Its authored operation-gate challenge set favored an operation-specific rule over the tested simpler rules. These results concern forecast targets and an authored synthetic challenge set. They do not test evidence retrieval, selector error, or selector/interpreter dependence.

See [Feature 046 results](experimental-evidence.md) and [its machine-readable output](experimental-results.json).

### Supported by the cited literature

UNREAL version 1 reports retrieval and answer-quality results for the benchmark settings described in that paper. It uses the same frozen model for model-native selection and answer generation. This motivates a controlled test of selection and interpretation errors.

The listed results do not measure source trust, selection-error dependence, or evidence-independence rules. Applying them to those questions would be an inference beyond the paper's measures.

### New experimental findings

The prompted UNREAL-inspired IsoPrax pilot has run twice on its fixed synthetic
case set. The case set and selection traces matched, but interpretation outputs
and the complete result digests did not. Treat the run tables as descriptive
pilot results, not a stable replay estimate. See the
[pilot results report](retrieval-selection-dependence-results.md). A separate
Bouleusis retrieval sweep has been reanalyzed from its JSONL records. Its ten
seeds vary one defect and do not add ten independent bugs. See the
[measurement-validity assessment](bouleusis-retrieval-measurement-validity.md)
and its [prospective iterative-retrieval preregistration](iterative-retrieval-preregistration.md).

### Remaining hypotheses

The pilot did not meet H1's preregistered support gate. It showed retrieval
recall and interpretation error can differ on some paired cases; a lineage
feature improved a descriptive prediction on this authored fixture; and the
operation-specific rule did not increase either permission-error count over
the metadata-only rule. These results do not establish those effects beyond
this fixture. H1-H5 remain general hypotheses. No result supports Semadmit
enforcement for shared selector/interpreter lineage, or says that a retrieval
score measures source validity or confidence in the evidence.

## Three separate evidence properties

For each retrieved item, the benchmark records these separately:

1. **Relevance**: does the item relate to the question or target?
2. **Source status**: is the item verified, invalid, conflicting, or unknown?
3. **Use for an operation**: may the item support this named operation, such as root-cause ranking or independent corroboration?

A relevant item may have unknown source status and may be inadmissible as independent support. A retrieval score is a ranking output. It is not evidence that the source is valid or independent.

## Boundaries

IsoPrax studies what selection provenance supports for later interpretation and combination. It does not select evidence for Bouleusis or implement a runtime trust policy. Bouleusis owns deliberation and epistemic-state behavior. Semadmit owns runtime admission and verification enforcement.

Recommend a Semadmit review only after a reproducible, held-out result supports a bounded rule. Any handoff must state its conditions, evidence, scope, limits, falsifier, and the runtime metadata needed to check it. This proposal does not send a policy or add runtime behavior.

## Recommendation

The paper creates a concrete setting in which one model selects and interprets evidence, but it does not test the dependence question. Feature 046 supports caution about inferring semantic equivalence from shared model identity, but it does not answer the retrieval question. A small, synthetic, controlled experiment is therefore justified. Product or enforcement complexity is not justified by current evidence.

**EVIDENCE-SELECTION DEPENDENCE WARRANTS FURTHER STUDY**
