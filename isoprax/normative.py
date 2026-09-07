"""Machine-checkable resolution of implementation citations.

The vendored Isoprax v0.3 document is the authority. This module only locates
numbered references in implementation source and resolves them to headings;
it does not interpret or rewrite normative text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_REFERENCE_RE = re.compile(
    r"(?ix)"
    r"(?:\bspec(?:ification)?\s*|§\s*)"
    r"(?P<section>\d+(?:\.\d+)+|[A-F](?:\.\d+)*)"
    r"|\bAppendix\s+(?P<appendix>[A-F](?:\.\d+)?)"
)
_HEADING_RE = re.compile(
    r"^\s{0,3}#{1,6}\s+"
    r"(?:(?P<section>\d+(?:\.\d+)*)|Appendix\s+(?P<appendix>[A-F](?:\.\d+)?))"
    r"(?:[.:\s]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class NormativeCitation:
    source_path: str
    line: int
    reference: str
    resolved_heading: str | None

    @property
    def resolved(self) -> bool:
        return self.resolved_heading is not None


def _references(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in _REFERENCE_RE.finditer(line):
            found.append(
                (line_number, match.group("section") or match.group("appendix"))
            )
    return found


def _headings(spec_text: str) -> dict[str, str]:
    headings: dict[str, str] = {}
    for line in spec_text.splitlines():
        match = _HEADING_RE.match(line)
        if not match:
            continue
        reference = match.group("section") or match.group("appendix")
        headings[reference.upper()] = line.strip()
    return headings


def _authority_headings(specification_path: Path) -> dict[str, str]:
    headings = _headings(specification_path.read_text(encoding="utf-8"))
    index_path = specification_path.with_name("isoprax-v0.3-poc-citation-index.md")
    if index_path.exists():
        headings.update(_headings(index_path.read_text(encoding="utf-8")))
    return headings


def resolve_citations(
    source_root: str | Path, specification_path: str | Path
) -> list[NormativeCitation]:
    """Resolve all supported normative citations in implementation sources."""

    root = Path(source_root)
    headings = _authority_headings(Path(specification_path))
    citations: list[NormativeCitation] = []
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root.parent).as_posix()
        text = path.read_text(encoding="utf-8")
        for line, reference in _references(text):
            key = reference.upper()
            resolved_heading = headings.get(key)
            if resolved_heading is None and "." in key:
                resolved_heading = headings.get(key.split(".", 1)[0])
            citations.append(
                NormativeCitation(relative, line, reference, resolved_heading)
            )
    return citations


def unresolved_citations(
    source_root: str | Path, specification_path: str | Path
) -> list[NormativeCitation]:
    return [
        citation
        for citation in resolve_citations(source_root, specification_path)
        if not citation.resolved
    ]
