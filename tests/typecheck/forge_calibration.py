from isoprax.semantic_types import CalibrationEvidence
from tests.typecheck.shared import LeftOutcome

CalibrationEvidence[LeftOutcome]("left", object())
