from pathlib import Path

import pytest

from isoprax.normative import resolve_citations

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "docs" / "isoprax-v0.3-poc.md").is_file()
)
SPEC = ROOT / "docs" / "isoprax-v0.3-poc.md"


def test_all_implementation_citations_resolve_to_vendored_authority():
    citations = resolve_citations(ROOT / "isoprax", SPEC)

    assert citations
    unresolved = [citation for citation in citations if not citation.resolved]
    assert unresolved == []
    assert any(citation.reference == "5.6.1" for citation in citations)


@pytest.mark.parametrize("reference", ["5.2", "5.6.3", "8.2", "D"])
def test_numbered_and_appendix_anchors_exist(reference):
    citations = resolve_citations(ROOT / "isoprax", SPEC)
    matching = [
        citation for citation in citations if citation.reference.upper() == reference
    ]
    assert matching
    if reference == "8.2":
        assert all("8.2" in citation.resolved_heading for citation in matching)


def test_example_citations_also_resolve():
    citations = resolve_citations(ROOT / "examples", SPEC)

    assert citations
    assert any(citation.reference.upper() == "D.3" for citation in citations)
    assert [citation for citation in citations if not citation.resolved] == []


def test_generated_cache_files_are_excluded(tmp_path):
    source = tmp_path / "isoprax"
    (source / "__pycache__").mkdir(parents=True)
    (source / "__pycache__" / "generated.py").write_text(
        '"""spec 999.1"""\n', encoding="utf-8"
    )
    (source / "real.py").write_text('"""spec 5.2"""\n', encoding="utf-8")

    citations = resolve_citations(source, SPEC)

    assert [citation.source_path for citation in citations] == ["isoprax/real.py"]
