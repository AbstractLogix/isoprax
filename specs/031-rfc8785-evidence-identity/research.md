# Research and Decisions

## Decision: RFC 8785 over Python `json.dumps`

`sort_keys=True` makes mapping order deterministic only inside Python's JSON
behavior. It does not specify number formatting, Unicode escaping, or safe
integer behavior across languages. RFC 8785 specifies those choices and is
already available as a small direct dependency.

## Decision: reject unsupported values

The previous `default=str` fallback silently changed values into
implementation-specific strings. JCS errors for unsupported values and
non-representable numbers, which is the safer identity boundary.
