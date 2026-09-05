# Contributing

Contributions are welcome under [Apache-2.0](LICENSE).

Before opening a pull request:

1. Do not add credentials, private telemetry, personal data, or downloaded
   datasets. The repository ignores common credential and generated-data paths.
2. Treat `AGENTS.md`, the authoritative Isoprax v0.3 POC, and the active
   Spec Kit workspace as the decision boundary. Do not convert unresolved
   research choices into defaults.
3. Keep conformance claims honest. Synthetic evidence and structural tests do
   not establish real-world predictive performance, Semantic conformance, or
   Full Conformance.
4. Add focused tests for behavior changes, then run:

   ```sh
   uv sync --group dev
   uv run ruff check .
   uv run ruff format --check .
   uv run pytest tests -q
   uv run pre-commit run --all-files
   ```

5. For non-trivial work, update `spec.md`, `plan.md`, `tasks.md`, and
   `converge.md` under `specs/`. Preserve blocked gates rather than bypassing
   them with invented assumptions.

By submitting a contribution, you agree that it is licensed under Apache-2.0.
