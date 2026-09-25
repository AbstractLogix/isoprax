"""Isoprax reference implementation (proof-of-concept)."""

from .admission import (
    AdmissionProfile,
    AdmissionReport,
    CalibrationEvidence,
    CorpusProvenance,
    CorpusRow,
    GateResult,
    PredeclarationEvidence,
    SplitDefinition,
    evaluate_admission,
)
from .ai4i2020 import (
    AI4I2020_CLAIM_BOUNDARY,
    AI4I2020_COLUMNS,
    AI4I2020_EXPECTATIONS,
    AI4I2020_EXPECTED_CSV_SHA256,
    AI4I2020_FEATURE_COLUMNS,
    AI4I2020_IDENTIFIER_COLUMNS,
    AI4I2020_LABEL_COLUMNS,
    AI4I2020_MODE_COLUMNS,
    AI4I2020Expectations,
    AI4I2020VerificationReport,
    ai4i2020_outcome_definitions,
    verify_ai4i2020_csv,
)
from .apachejit import (
    APACHEJIT_CLAIM_BOUNDARY,
    APACHEJIT_COLUMNS,
    APACHEJIT_EXPECTATIONS,
    APACHEJIT_EXPECTED_SHA256,
    ApacheJITExpectations,
    ApacheJITVerificationReport,
    apachejit_outcome_definition,
    verify_apachejit_csv,
)
from .baseline_strategies import (
    DistributionAnomalyStrategy,
    HeuristicRiskStrategy,
    HistoricalMeanForecastStrategy,
)
from .build_qualification import (
    BuildPreparation,
    BuildQualificationReport,
    BuildRowResult,
    BuildSample,
    LegalCoverageRecord,
    RunnerDescriptor,
    execute_prepared_sample,
    prepare_build_sample,
    reduce_build_qualification,
)
from .candidate_selection import (
    CandidateRecord,
    ScreeningResult,
    derive_build_floor,
    evaluate_candidate_screening,
    screen_candidate,
    screen_candidate_system,
    screen_candidates,
    screen_early_candidate,
)
from .commensurability import (
    Attestation,
    CommensurabilityResult,
    IncommensurableError,
    ObservationProcess,
    OutcomeDefinition,
    OutcomeDefinitionRegistry,
    Threshold,
    Window,
    check_commensurable,
    require_commensurable,
)
from .corpus_assembly import (
    AssemblyRejection,
    CorpusAssemblyProfile,
    CorpusAssemblyReport,
    ReplayCaptureInput,
    assemble_corpus,
)
from .corpus_manifest import (
    CorpusManifest,
    build_corpus_manifest,
    validate_corpus_manifest,
)
from .eb_jepa import (
    EBJEPAAnomalyStrategy,
    EBJEPAConfig,
    EBJEPARiskStrategy,
    EBJEPATrainingReport,
    EBJEPAWorldModel,
)
from .efficacy import (
    EfficacyEvaluationProfile,
    EfficacyFamilyScores,
    EfficacyReport,
    FamilyEfficacyResult,
    evaluate_eb_jepa_efficacy,
)
from .events import ChangeEvent, Event, Family, MetricSample, RunEvent
from .evidence import PoolingHarmEvidence, build_pooling_harm_evidence
from .evidence_reporting import (
    EvidenceReport,
    EvidenceReportProfile,
    GateSummary,
    UnavailableEvidence,
    build_evidence_report,
)
from .external_anchor import (
    ExternalAnchorVerification,
    build_stage2_statement,
    stage2_statement_payload,
    verify_sigstore_attestation,
)
from .hermetic_runner import (
    ApprovedRunnerConfiguration,
    ArtifactEvidence,
    EffectiveRunnerControls,
    ExecutionEvidenceRecord,
    RunnerBackend,
    RunnerBackendResult,
    run_prepared_execution,
)
from .jepa import (
    JEPA_DEFECT_RISK,
    JEPA_OPERATIONAL_FAILURE,
    EvidenceProvenance,
    JEPAAnomalyStrategy,
    JEPAAssessment,
    JEPABackendConfig,
    JEPARiskStrategy,
    JEPASemanticEvidence,
    JEPATrainingPair,
    JEPATrainingReport,
    JEPAWorldModel,
)
from .kb import KnowledgeBase, Outcome, SQLiteKB
from .metropt3 import (
    METROPT3_CLAIM_BOUNDARY,
    METROPT3_COLUMNS,
    METROPT3_EXPECTATIONS,
    METROPT3_EXPECTED_INTERVAL_ROWS,
    METROPT3_EXPECTED_SHA256,
    MetroPT3Expectations,
    MetroPT3FailureInterval,
    MetroPT3VerificationReport,
    metropt3_outcome_definition,
    verify_metropt3_csv,
)
from .nasa_cmaps import (
    CMAPSS_CLAIM_BOUNDARY,
    CMAPSS_EXPECTATIONS,
    CMapssVerificationReport,
    cmapss_outcome_definitions,
    verify_cmapss,
)
from .normative import NormativeCitation, resolve_citations, unresolved_citations
from .per_family_evaluation import (
    PerFamilyEvaluationProfile,
    PerFamilyEvaluationReport,
    UnavailableEvaluationEvidence,
    evaluate_per_family,
)
from .predeclaration import (
    ExclusionEntry,
    PredeclarationArtifact,
    ProvenanceRecord,
    build_replay_justification_exclusion,
    evaluate_predeclaration_provenance,
    hash_predeclaration_artifact,
    record_exclusion_entry,
    validate_predeclaration_artifact,
)
from .public_corpus import (
    PublicCorpusMaterializationProfile,
    PublicCorpusRecord,
    PublicCorpusReport,
    PublicCorpusSnapshot,
    WithheldEvidenceRecord,
    materialize_public_corpus,
    normalize_public_corpus,
)
from .public_evidence import (
    PublicEvidenceRecord,
    PublicEvidenceSnapshot,
    normalize_public_evidence,
)
from .public_label_evidence import (
    PublicLabelComparison,
    PublicLabelComparisonStatus,
    PublicLabelDefinition,
    PublicLabelEvidenceManifest,
    PublicLabelEvidenceRecord,
    PublicLabelProcedure,
    PublicLabelSemanticsReport,
    PublicLabelSource,
    PublicLabelStatus,
    build_public_label_semantics_report,
    reduce_public_label_evidence,
)
from .public_observation import (
    PublicObservationRecord,
    PublicObservationSnapshot,
    normalize_public_observations,
)
from .replay_capture import (
    DeploymentEvidence,
    ObservationArtifactEvidence,
    ObservationEvidence,
    ReplayCaptureBackend,
    ReplayCaptureBackendResult,
    ReplayCaptureRecord,
    ReplayLaneDefinition,
    capture_replay_lane,
)
from .replay_constraints import (
    ReplayConstraint,
    ReplayConstraintError,
    build_replay_constraints,
    validate_replay_constraints,
    validate_replay_constraints_dict,
)
from .semantic_types import (
    CalibrationEvidence as SemanticCalibrationEvidence,
)
from .semantic_types import (
    CommensurabilityEvidence,
    PooledComparisonAuthorization,
    authorize_pooled_comparison,
    establish_calibration,
    establish_commensurability,
)
from .signals import (
    AnomalySignal,
    CalibrationStatus,
    ForecastSignal,
    ProbabilitySignal,
    RiskSignal,
    Signal,
)
from .stage1_public_validation import build_stage1_public_validation_report
from .stage2_corpus_evaluation import (
    CORPUS_MIN_TEST_NEGATIVES,
    CORPUS_MIN_TEST_POSITIVES,
    CORPUS_MIN_TEST_ROWS,
    CorpusEvaluationGate,
    CorpusEvaluationProfile,
    CorpusEvaluationReport,
    evaluate_stage2_corpus,
    validate_stage2_corpus_evaluation_report,
)
from .stage2_feasibility import (
    CLAIM_BOUNDARY,
    BootstrapYieldEstimate,
    FeasibilityGate,
    FeasibilityReport,
    RepeatabilityCheck,
    ReplayPilotProfile,
    ReplayTerminalRecord,
    build_stage2_feasibility_report,
    compare_repeatability,
    estimate_stage2_yield,
    normalize_replay_records,
    validate_stage2_feasibility_report,
)
from .strategies import (
    AnomalyStrategy,
    Calibrator,
    ForecastStrategy,
    RiskStrategy,
)

__version__ = "0.2.0"
