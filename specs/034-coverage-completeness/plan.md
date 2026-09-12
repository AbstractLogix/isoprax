# Implementation Plan

1. Derive expected production modules from the configured source root.
2. Normalize reported paths and fail for expected modules absent from the JSON.
3. Preserve the existing percentage threshold and add subprocess regression
   tests for missing, passing, and below-threshold cases.
