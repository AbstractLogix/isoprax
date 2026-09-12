# Implementation Plan

1. Change the SQLite signal uniqueness constraint and add schema migration for
   pre-versioned tables.
2. Add version-aware signal reads, outcomes, and labeled-pair queries.
3. Migrate legacy outcome rows only when exactly one signal version can be
   resolved; reject otherwise.
4. Add coexistence, ambiguity, and migration regression tests.
