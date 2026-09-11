# Research: Durable Knowledge-Base Integrity

## Existing contracts

- `OutcomeDefinitionRegistry.register` already rejects a reused identifier
  whose content differs.
- `SQLiteKB.store_outcome_definition` and `store_event` currently use
  `INSERT OR REPLACE`, which bypasses that invariant at the durable boundary.
- `signals` has no uniqueness constraint and `get_labeled_pairs` joins all
  matching signal and outcome rows.

## Decisions

- Identical retries are idempotent to support safe replay and transaction retry.
- Conflicting writes fail closed and preserve the first persisted value.
- Legacy duplicate signal rows are not auto-deduplicated because choosing a
  survivor would be an evidence mutation that requires human adjudication.
