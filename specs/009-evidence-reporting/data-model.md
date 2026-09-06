# Data Model: Stage 1 Evidence Reporting

## EvidenceReportProfile

Frozen public-report configuration.

| Field | Validation |
|---|---|
| `assembly_profile_identity` | Non-empty; equals the assembly report identity. |
| `release_scope` | Non-empty; equals assembly and admission manifest scope. |
| `predeclaration_artifact_hash` | Non-empty safe hash/reference. |
| `predeclaration_anchor_reference` | Non-empty independent safe reference. |
| `published_artifacts` | Non-empty unique public artifact identifiers; equals assembly/admission publication metadata. |
| `required_evidence_categories` | Canonical unique names; missing categories become unavailable. |

## UnavailableEvidence

One expected public evidence category not fully available.

| Field | Rule |
|---|---|
| `category` | Required canonical category name. |
| `reason` | Required bounded reason; never raw source content. |

## GateSummary

Safe reduction of one `GateResult`.

| Field | Rule |
|---|---|
| `gate_id` | Copied from the evaluated admission result. |
| `passed` | Copied boolean. |
| `message` | Copied public gate message. |
| `failed_count` | Count only; never row identifiers. |

## EvidenceReport

Deterministic report output.

| Field | Rule |
|---|---|
| `report_identity` | SHA-256 of canonical public representation. |
| `status` | `admission_evidence`, `blocked`, or `inconclusive`. |
| `assembly_profile_identity` | Links to the frozen corpus assembly. |
| `release_scope` | Publicly allowed scope only. |
| `predeclaration` | Safe hash/anchor pair only. |
| `capture_evidence` | Ordered safe lane, qualification, execution, deployment, artifact-state/hash, and outcome references. |
| `counts` | Accepted/rejected, outcome, and censoring counts. |
| `provenance` | Safe source system and privacy flags. |
| `gates` | Ordered gate summaries. |
| `unavailable_evidence` | Ordered explicit absences/incompleteness. |
| `claim_boundary` | Fixed admission-evidence-only statement. |

## Relationships and transitions

`EvidenceReportProfile` + `CorpusAssemblyReport` + matching
`ReplayCaptureRecord` values + `AdmissionProfile` + `AdmissionReport` produce
one `EvidenceReport`. Any mismatch, private/privileged provenance, or unsafe
claim scope rejects generation. Valid but incomplete evidence produces
`inconclusive`; valid evidence with a failed gate produces `blocked`; only
complete evidence plus passing gates produces `admission_evidence`.
