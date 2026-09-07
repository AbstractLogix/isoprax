import gzip
import hashlib
import json
from pathlib import Path

import pytest

from isoprax.stage1_public_validation import build_stage1_public_validation_report


def _write_sources(tmp_path: Path) -> tuple[Path, Path, Path]:
    apache = tmp_path / "apachejit_total.csv"
    apache.write_text(
        "commit_id,project,buggy,fix,year,author_date,la,ld,nf,nd,ns,ent,ndev,age,nuc,aexp,arexp,asexp\n"
        + "\n".join(
            f"c{i},apache/ignite,{str(i % 2 == 0)},False,{year},"
            f"{int(__import__('datetime').datetime(year, 6, 1, tzinfo=__import__('datetime').timezone.utc).timestamp())},10,2,1,1,1,1,1,1,1,1,1,1"
            for i, year in enumerate((2014, 2015, 2016, 2017))
        )
        + "\nother,apache/other,False,False,2014,1400000000,10,2,1,1,1,1,1,1,1,1,1,1"
        + "\noutside,apache/ignite,False,False,2020,1578009600,10,2,1,1,1,1,1,1,1,1,1,1"
        + "\n",
        encoding="utf-8",
    )
    google = tmp_path / "google-cluster-data-1.csv.gz"
    with gzip.open(google, "wt", encoding="utf-8") as stream:
        stream.write("Time ParentID TaskID JobType NrmlTaskCores NrmlTaskMem \n")
        stream.write("90000 1 1 0 0.001 0.001\n")
        stream.write("90001 1 2 0 0.01 0.01\n")
        stream.write("96000 2 1 0 0.001 0.001\n")
        stream.write("96001 2 2 0 0.001 0.001\n")
        stream.write("102000 3 1 0 0.001 0.001\n")
        stream.write("102001 3 2 0.01 0.01\n")
        stream.write("108000 4 1 0 0.001 0.001\n")
        stream.write("108001 4 2 0.001 0.001\n")
    predeclaration = tmp_path / "predeclaration.json"
    predeclaration.write_text('{"test": true}\n', encoding="utf-8")
    return apache, google, predeclaration


def test_missing_sources_fail_closed(tmp_path):
    _, _, predeclaration = _write_sources(tmp_path)
    with pytest.raises(FileNotFoundError):
        build_stage1_public_validation_report(
            tmp_path / "missing.csv",
            tmp_path / "missing.csv.gz",
            predeclaration_path=predeclaration,
        )


def test_changed_source_checksum_fails_closed(tmp_path):
    apache, google, predeclaration = _write_sources(tmp_path)
    with pytest.raises(ValueError, match="checksum mismatch"):
        build_stage1_public_validation_report(
            apache, google, predeclaration_path=predeclaration
        )


def test_report_has_separate_claim_bounded_families(tmp_path, monkeypatch):
    apache, google, predeclaration = _write_sources(tmp_path)
    import isoprax.stage1_public_validation as module

    monkeypatch.setitem(
        module._APACHE_SOURCE,
        "published_checksum",
        f"md5:{hashlib.md5(apache.read_bytes()).hexdigest()}",
    )
    monkeypatch.setitem(
        module._GOOGLE_SOURCE,
        "published_checksum",
        f"sha1:{hashlib.sha1(google.read_bytes()).hexdigest()}",
    )
    first = build_stage1_public_validation_report(
        apache, google, predeclaration_path=predeclaration
    )
    second = build_stage1_public_validation_report(
        apache, google, predeclaration_path=predeclaration
    )

    assert first == second
    assert len(first["families"]) == 2
    assert {item["evaluation"]["family"] for item in first["families"]} == {
        "change",
        "operational",
    }
    assert "withheld" in first["cross_family_pooling"]
    assert "Semantic" in first["claim_boundary"]
    json.dumps(first)


def test_validation_rejects_missing_predeclaration_and_bad_schemas(
    tmp_path, monkeypatch
):
    import isoprax.stage1_public_validation as module

    apache, google, _ = _write_sources(tmp_path)
    with pytest.raises(FileNotFoundError, match="predeclaration"):
        build_stage1_public_validation_report(
            apache, google, predeclaration_path=tmp_path / "missing.json"
        )

    bad_apache = tmp_path / "bad-apache.csv"
    bad_apache.write_text("wrong\n", encoding="utf-8")
    monkeypatch.setitem(
        module._APACHE_SOURCE,
        "published_checksum",
        f"md5:{hashlib.md5(bad_apache.read_bytes()).hexdigest()}",
    )
    with pytest.raises(ValueError, match="ApacheJIT schema"):
        module._build_apache_rows(bad_apache)

    bad_google = tmp_path / "bad-google.csv.gz"
    with gzip.open(bad_google, "wt", encoding="utf-8") as stream:
        stream.write("wrong header\n")
    monkeypatch.setitem(
        module._GOOGLE_SOURCE,
        "published_checksum",
        f"sha1:{hashlib.sha1(bad_google.read_bytes()).hexdigest()}",
    )
    with pytest.raises(ValueError, match="Google Trace v1 schema"):
        module._build_google_rows(bad_google)

    edge_google = tmp_path / "edge-google.csv.gz"
    with gzip.open(edge_google, "wt", encoding="utf-8") as stream:
        stream.write("Time ParentID TaskID JobType NrmlTaskCores NrmlTaskMem\n")
        stream.write("120000 7 1 0 0.001 0.001\n")
        stream.write("120001 7 2 0 0.01 0.01\n")
        stream.write("90000 8 1 0 0.001 0.001\n")
    monkeypatch.setitem(
        module._GOOGLE_SOURCE,
        "published_checksum",
        f"sha1:{hashlib.sha1(edge_google.read_bytes()).hexdigest()}",
    )
    rows, _ = module._build_google_rows(edge_google)
    assert rows == []


def test_split_rejects_outside_timestamp():
    import datetime as dt

    import isoprax.stage1_public_validation as module

    assert (
        module._split_for_timestamp(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc))
        == "outside"
    )
