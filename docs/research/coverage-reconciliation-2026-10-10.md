# Local and hosted coverage reconciliation — 2026-10-10

## Result

The difference is explained by the installed optional GPU extra, which supplies PyTorch and enables the EB-JEPA test module. It is not a different coverage threshold or a test-discovery configuration change.

| Run | Python | Dependencies | Tests | Coverage |
|---|---|---|---:|---:|
| Earlier local report | 3.14.7 | Dev environment without the `gpu` extra; `torch` was absent | 649 passed, 4 skipped | 94.33% |
| Hosted Actions, run `38000986319`, Python 3.12 | 3.12.15 | `uv sync --group dev --extra gpu`; `torch==2.14.0` | 678 passed, 4 skipped | 98.06% |
| Hosted Actions, run `38000986319`, Python 3.14 | 3.14.8 | Same lock and `gpu` extra; `torch==2.14.0` | 678 passed, 4 skipped | 98.06% |
| Local CI-equivalent reproduction at the stacked PR #55 head | 3.12.13 | Same lock and `gpu` extra; `torch==2.14.0` | 678 passed, 4 skipped | 98.09% |
| Local full suite on this main-based standalone branch | 3.12.13 | Same lock and `gpu` extra; `torch==2.14.0` | 630 passed, 4 skipped | 98.09% |

For like-for-like runs at PR #55 head `803761414c8c8bb4ede00f719cc7a2d009f4a6a2`, `tests/test_eb_jepa.py` uses `pytest.importorskip("torch")`. Without the extra, its 29 tests are not collected. With the extra, those tests execute and cover `isoprax/eb_jepa.py`. This explains the original 649-versus-678 difference. The current branch starts from `main` and excludes the 48 test cases introduced in PR #54's companion-study ancestry; its 630 passing tests are therefore expected. This is a branch-scope difference, not a coverage-setting difference. No source file was excluded, and no threshold or test was changed to obtain these results.

## Configuration comparison

- CI tests `tests` on Python 3.10, 3.12, and 3.14. The recorded local failure used Python 3.14.7; the CI run used 3.12.15 and 3.14.8.
- Both runs use the checked-in `uv.lock`. The local run omitted the CI `gpu` extra; CI installs `uv sync --group dev --extra gpu`.
- CI runs `uv run pytest tests -q --cov-report=xml`. The project `pyproject.toml` supplies the same `--cov=isoprax`, branch coverage, terminal report, and 95% total gate for local runs.
- CI also checks each module at 95% and changed-line coverage at 95%. The earlier local hook ran `uv run pytest tests -q` and did not run the CI per-module and diff-coverage steps.
- All four reports show four skipped tests. The main collection difference is 29 EB-JEPA tests that require PyTorch. CI's run record does not retain the names of skipped tests, so skip identities cannot be compared from that run log.

## Remaining difference

The local Python 3.12.13 run reached 98.09%; hosted Python 3.12.15 and 3.14.8 reported 98.06%. Both hosted jobs had 6 missed statements in `isoprax/eb_jepa.py`; the local 3.12.13 run had 3 missed statements. The coverage report therefore has a 0.03 percentage-point patch/runtime difference after the main collection cause is fixed. All three results clear the 95% total, module, and CI gates. The exact 3.12.15 patch is not available in the local uv interpreter cache, so that last 0.03-point difference was not reproduced byte-for-byte.

The project config stays unchanged. Run the CI command with the locked `gpu` extra when checking the repository-wide coverage gate.

## Source evidence

- CI workflow: `.github/workflows/ci.yml`.
- Coverage configuration: `pyproject.toml`.
- Hosted run: [GitHub Actions run 38000986319](https://github.com/AbstractLogix/isoprax/actions/runs/38000986319).
- Local reproduction used the locked dependency set with Python 3.12.13 and the CI `gpu` extra.
