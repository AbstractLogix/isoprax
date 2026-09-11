# Research: API Contract Cleanup

The KB ABC had concrete-looking ellipsis methods for retrieval, so incomplete
subclasses could instantiate and return `None`. Predeclaration validation and
provenance each had multiple aliases for the same callable, including a
`validate_` name bound to a constructor. The adequacy gate returned split names
in a field documented as row IDs.
