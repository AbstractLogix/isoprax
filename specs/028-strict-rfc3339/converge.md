# Convergence

The parser now requires the RFC 3339 `T` separator and an explicit UTC
designator (`Z` or `+00:00`) before using `datetime.fromisoformat`. The change
is limited to admission timestamp syntax and retains the existing fail-closed
domain error.
