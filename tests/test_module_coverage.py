import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts/check_module_coverage.py"


def _run(tmp_path, report):
    source = tmp_path / "isoprax"
    source.mkdir()
    (source / "__init__.py").write_text("", encoding="utf-8")
    (source / "covered.py").write_text("", encoding="utf-8")
    (source / "missing.py").write_text("", encoding="utf-8")
    report_path = tmp_path / "coverage.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(report_path),
            "--source-root",
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def _file(path, percent=100.0):
    return {"files": {str(path): {"summary": {"percent_covered": percent}}}}


def test_missing_production_module_fails_closed(tmp_path):
    covered = tmp_path / "isoprax" / "covered.py"
    report = _file(covered)

    result = _run(tmp_path, report)

    assert result.returncode == 1
    assert "missing.py: missing coverage data" in result.stdout


def test_all_reported_modules_pass(tmp_path):
    source = tmp_path / "isoprax"
    report = {
        "files": {
            str(source / "covered.py"): {"summary": {"percent_covered": 100.0}},
            str(source / "missing.py"): {"summary": {"percent_covered": 100.0}},
        }
    }

    result = _run(tmp_path, report)

    assert result.returncode == 0
    assert "Every production module meets" in result.stdout


def test_below_threshold_module_still_fails(tmp_path):
    source = tmp_path / "isoprax"
    report = {
        "files": {
            str(source / "covered.py"): {"summary": {"percent_covered": 94.9}},
            str(source / "missing.py"): {"summary": {"percent_covered": 100.0}},
        }
    }

    result = _run(tmp_path, report)

    assert result.returncode == 1
    assert "94.90% < 95.00%" in result.stdout
