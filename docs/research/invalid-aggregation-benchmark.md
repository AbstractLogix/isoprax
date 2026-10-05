# Invalid-Aggregation Benchmark

**Status**: Public synthetic benchmark specification. It is not an efficacy benchmark.

## Benchmark A: Same probability, different event

### Question

Does matching calibration or matching probability values permit a system to interpret two different outcome definitions as one failure probability?

### Synthetic setup

Create two independent 100-record lanes:

| Lane | Outcome definition | Forecasts | Observed positives |
|---|---|---:|---:|
| Change | A repository-derived fix-linked defect label within 30 days | `0.80` for each record | 80 of 100 |
| Operational | A service-level threshold breach within 30 minutes of a deployment | `0.80` for each record | 80 of 100 |

Each lane has zero empirical calibration error at this single forecast value. The equal-weight numeric pool also reports `0.80`. The lane definitions use different source and observation processes, events, and windows.

The invalid inference is: “0.80 is the probability of one common failure event across both lanes.” The numbers are calibrated against separate targets. The pooled number only has an interpretation if a new mixture target and its lane weights are declared. Calibration cannot create that target after the results are seen.

### Valid control

Use the same outcome event, observation process, window, threshold, and unit in both lanes. Declare the evaluation population and weights before scoring. In a second control, define a mixture event explicitly and report it under that name. The benchmark must distinguish a valid mixture estimand from an unsupported claim that the source outcomes are identical.

### Expected result

- Per-lane calibration remains reportable.
- An operation that claims a common event probability is refused or marked unknown for Benchmark A.
- Pooling may be reported only as a declared mixture estimand, not as target equivalence.
- The valid control permits only the operations supported by its shared definition and sampling design.

## Benchmark B: Calibrated windows, changed ranking

The repository already contains a deterministic synthetic fixture in `isoprax/evidence.py`. It creates separate seven-day and ninety-day windows, sets scores near each lane's event rate, calculates per-lane and pooled ECE, and compares per-family top-k selection with pooled ranking. The default uses 100 records per lane and a top-20 selection per lane.

Use this fixture to study whether a pooled ranking changes which family contributes selected cases. Keep both window definitions visible. The source docstring's “same-event” phrase means, at most, the same broad event class; it must not imply the two window-defined targets are identical. The evaluation must not treat pooled ECE as proof of semantic alignment.

## Measures and controls

- Report sample counts and event rates by lane.
- Report reliability plots, Brier score, and ECE by lane; state ECE binning and its limits.
- Report pooled calibration only with its target mixture and weights stated.
- Report top-k overlap, per-family precision, macro precision, and decision changes.
- Include a same-target control and a deliberately shifted mixture-weight control.
- Preserve target identity and source lineage for every row.

## Falsification and claim boundary

The benchmark does not support the operation-specific thesis if simple metadata or naive aggregation performs equivalently on realistic follow-on benchmarks and produces no harmful interpretation or decision change. A synthetic counterexample establishes that the specified failure can occur; it does not measure how often it occurs in production.

This is structural and synthetic evidence only. It is not Semantic/Full Conformance, real-world predictive efficacy, or evidence that every cross-family aggregate is invalid.

## Reproduction

From the repository root, run `uv run python examples/demo_cross_family.py` to view the existing window-based fixture output. Benchmark A is a separately specified minimal case for a future research runner; this document does not claim it has been executed in code.
