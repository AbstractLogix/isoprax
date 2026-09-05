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
from .events import ChangeEvent, Event, Family, MetricSample, RunEvent
from .kb import KnowledgeBase, Outcome, SQLiteKB
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
