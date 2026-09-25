from isoprax.commensurability import check_commensurable
from isoprax.semantic_types import authorize_pooled_comparison
from tests.typecheck.shared import (
    left_calibration,
    left_definition,
    right_calibration,
    right_definition,
)

relation = check_commensurable(left_definition, right_definition)
authorize_pooled_comparison(relation, left_calibration, right_calibration)
