.DEFAULT_GOAL := help

.PHONY: help sync test coverage diff-coverage mutation audit lint format format-check demo hooks pre-commit check

help: ## Show available developer actions.

	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "%-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

sync: ## Install or update the locked development environment.

	uv sync --group dev

test: ## Run all tests with the enforced branch-coverage gate.

	uv run pytest tests -q

coverage: test ## Verify every production module meets 95% branch-aware coverage.

	uv run coverage json -o coverage.json
	uv run python scripts/check_module_coverage.py coverage.json --minimum 95

diff-coverage: test ## Require 95% coverage for changes relative to origin/main.

	uv run coverage xml -o coverage.xml
	uv run diff-cover coverage.xml --compare-branch origin/main --fail-under 95

mutation: ## Run mutation testing for the build-qualification evidence boundary.

	uv run mutmut run

audit: ## Audit locked third-party dependencies for known vulnerabilities.

	uv run pip-audit

lint: ## Run static lint checks.

	uv run ruff check .

format: ## Apply Ruff formatting to repository files.

	uv run ruff format .

format-check: ## Verify repository formatting without modifying files.

	uv run ruff format --check .

demo: ## Run the synthetic structural-conformance demonstration.

	uv run python examples/demo_cross_family.py

hooks: ## Install the repository pre-commit hooks.

	uv run pre-commit install --hook-type pre-commit --hook-type pre-push

pre-commit: ## Run all pre-commit hooks without installing them.

	uv run pre-commit run --all-files

check: lint format-check coverage audit demo ## Run the standard local verification suite.
