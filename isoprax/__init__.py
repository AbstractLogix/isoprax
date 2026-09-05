"""Isoprax reference implementation (proof-of-concept)."""

from . import evaluation
from .admission import (
    AdmissionProfile,
    AdmissionReport,
    CorpusRow,
    GateResult,
    SplitDefinition,
    evaluate_admission,
)
from .baseline_strategies import (
    DistributionAnomalyStrategy,
    HeuristicRiskStrategy,
)
from .candidate_selection import (
    CandidateRecord,
    ScreeningResult,
    evaluate_candidate_screening,
    screen_candidate,
    screen_candidate_system,
    screen_candidates,
)
from .commensurability import (
    CommensurabilityResult,
    IncommensurableError,
    OutcomeDefinition,
    OutcomeDefinitionRegistry,
    check_commensurable,
    require_commensurable,
)
from .corpus_manifest import (
    CorpusManifest,
    build_corpus_manifest,
    validate_corpus_manifest,
)
from .events import ChangeEvent, Event, Family, MetricSample, RunEvent
from .kb import KnowledgeBase, Outcome, SQLiteKB
from .predeclaration import (
    ExclusionEntry,
    PredeclarationArtifact,
    ProvenanceRecord,
    build_replay_justification_exclusion,
    check_predeclaration_provenance,
    compute_predeclaration_hash,
    evaluate_predeclaration_provenance,
    hash_predeclaration_artifact,
    record_exclusion_entry,
    validate_exclusion_entry,
    validate_predeclaration,
    validate_predeclaration_artifact,
    validate_predeclaration_provenance,
)
from .replay_constraints import (
    ReplayConstraint,
    ReplayConstraintError,
    build_replay_constraints,
    validate_replay_constraints,
    validate_replay_constraints_dict,
)
from .signals import (
    AnomalySignal,
    CalibrationStatus,
    ForecastSignal,
    ProbabilitySignal,
    RiskSignal,
    Signal,
)
from .strategies import (
    AnomalyStrategy,
    Calibrator,
    ForecastStrategy,
    RiskStrategy,
)

__version__ = "0.1.0"
