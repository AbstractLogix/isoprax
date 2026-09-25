from isoprax.commensurability import ObservationProcess, Threshold, Window
from isoprax.evaluation import authorized_pooled_ece
from isoprax.semantic_types import authorize_pooled_comparison
from tests.typecheck.shared import (
    calibration_outcomes,
    calibration_scores,
    left_calibration,
    left_definition,
    left_relation,
    right_calibration,
)

stored_observation: ObservationProcess = left_definition.observation_process
stored_window: Window = left_definition.window
stored_thresholds: tuple[Threshold, ...] = left_definition.thresholds

authorization = authorize_pooled_comparison(
    left_relation,
    left_calibration,
    right_calibration,
)
pooled_ece: float = authorized_pooled_ece(
    authorization,
    calibration_scores,
    calibration_outcomes,
    calibration_scores,
    calibration_outcomes,
)
