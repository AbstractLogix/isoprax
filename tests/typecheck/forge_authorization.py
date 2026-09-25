from isoprax.semantic_types import PooledComparisonAuthorization
from tests.typecheck.shared import LeftOutcome, RightOutcome

PooledComparisonAuthorization[LeftOutcome, RightOutcome]("left", "right")
