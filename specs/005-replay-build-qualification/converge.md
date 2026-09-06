# Convergence: Hermetic Replay Build Qualification

## Evidence obtained

- Preparation hashes ordered sample, legal records, runner descriptor, and recipe.
- Missing legal coverage and invalid runners block all rows before invocation.
- The injected runner retains one terminal row per commit and maps build failures to censored evidence.
- Qualification is unavailable for incomplete or blocked execution and rejects clustered or below-floor samples.
- `uv run pytest tests -q` passed: 59 tests.
- Focused Ruff lint and formatting checks passed.

## Remaining gate

No real candidate, legal source, container, or historical build was executed. A future integration may provide that runner only after its candidate-specific evidence is verified.
