from isoprax.commensurability import OutcomeDefinition
from isoprax.semantic_types import (
    CalibrationEvidence,
    CommensurabilityEvidence,
    establish_calibration,
    establish_commensurability,
)


class LeftOutcome:
    pass


class RightOutcome:
    pass


class OtherOutcome:
    pass


left_definition = OutcomeDefinition("left", "defect", "telemetry", "one day")
right_definition = OutcomeDefinition("right", "defect", "telemetry", "one day")
other_definition = OutcomeDefinition("other", "defect", "telemetry", "one day")

left_relation: CommensurabilityEvidence[LeftOutcome, RightOutcome]
left_relation = establish_commensurability(
    left_definition,
    right_definition,
    left_tag=LeftOutcome,
    right_tag=RightOutcome,
)

calibration_scores = [0.0, 1.0] * 250
calibration_outcomes = [0, 1] * 250

left_calibration: CalibrationEvidence[LeftOutcome]
left_calibration = establish_calibration(
    left_definition,
    calibration_scores,
    calibration_outcomes,
    tag=LeftOutcome,
)
right_calibration: CalibrationEvidence[RightOutcome]
right_calibration = establish_calibration(
    right_definition,
    calibration_scores,
    calibration_outcomes,
    tag=RightOutcome,
)
other_calibration: CalibrationEvidence[OtherOutcome]
other_calibration = establish_calibration(
    other_definition,
    calibration_scores,
    calibration_outcomes,
    tag=OtherOutcome,
)
