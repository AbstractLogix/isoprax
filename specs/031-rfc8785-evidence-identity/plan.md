# Implementation Plan

1. Add `rfc8785` as a direct runtime dependency.
2. Implement `canonical_json` through `rfc8785.dumps` and preserve the string
   API used by existing reducers.
3. Add RFC 8785 Unicode, number, rejection, and known-hash tests.
4. Constrain property tests to JCS's safe integer domain.
