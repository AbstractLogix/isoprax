# Public Release Checklist

Use this checklist before opening the repository publicly.

## 1) Required project files

- [x] `LICENSE` present
- [x] `README.md` present and claim boundaries explicit
- [x] `CONTRIBUTING.md` present
- [x] `SECURITY.md` present
- [x] `CODE_OF_CONDUCT.md` present
- [x] CI workflow present (`.github/workflows/ci.yml`)

## 2) Hygiene gates

- [ ] `uv run ruff check .`
- [ ] `uv run pytest tests -q`
- [ ] `uv run python examples/demo_cross_family.py`
- [ ] `uv run pre-commit run --all-files`

## 3) Publication safety

- [x] `.vscode/` ignored
- [ ] No local machine paths remain in tracked docs
- [ ] No secrets/credentials included in tracked files

## 4) Curated initial commit strategy

Prefer a clean sequence instead of one giant commit:

1. **Scaffolding**: license, contributing, ignore rules, pre-commit, CI.
2. **Stage 0 implementation**: `isoprax/`, demo, baseline tests.
3. **Spec artifacts**: `specs/001-*` then `specs/002-*`.
4. **Docs polish**: README, security, conduct, convergence updates.

## 5) Final verification

- [ ] Open repository in a fresh clone and run quickstart commands
- [ ] Confirm CI passes on the default branch
- [ ] Confirm repository description/topics reflect "reference" status
