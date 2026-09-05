# Data Model

- **Event**: ChangeEvent, RunEvent, or MetricSample; every event has a stable
  ID, UTC timestamp, source, and type-derived family.
- **OutcomeDefinition**: Event, observation process, window, and thresholds;
  determines whether two probability scores are commensurable.
- **Signal**: Strategy output with explanation and provenance. Probability
  signals carry an OutcomeDefinition ID and calibration status.
- **Outcome**: Observed condition linked to an event, producing strategy, and
  the same OutcomeDefinition used by the signal.
- **KnowledgeBase**: Stores definitions, events, signals, and outcomes while
  exposing time-ordered and family/type queries.
