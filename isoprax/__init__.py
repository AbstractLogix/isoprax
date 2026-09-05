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
