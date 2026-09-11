import re
from pathlib import Path

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").is_file()
)


def test_project_version_has_a_matching_changelog_entry():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
    assert version_match is not None
    version = version_match.group(1)
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert re.search(rf"^## \[{re.escape(version)}\]", changelog, re.MULTILINE)
