# Research and Decisions

## Decision: document rather than add a container engine

The existing specification intentionally leaves engine selection and
provisioning to the integrating environment. Adding a runtime would expand
security, platform, and release scope without closing a requirement of the
reference evidence contract.

The minimal correction is to align the module and README with the already
implemented injected-backend design and prevent hermeticity from being inferred
from the filename.
