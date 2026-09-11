# Implementation Plan

1. Add an explicit RFC 3339 UTC shape check before `datetime` parsing.
2. Preserve the existing UTC-aware datetime validation and error contract.
3. Add regression coverage for the previously accepted space separator.
