"""Validate and execute repository notebooks without saving generated output."""

from __future__ import annotations

import os
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import nbformat
from nbclient import NotebookClient
from nbformat.notebooknode import NotebookNode

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIRECTORY = REPOSITORY_ROOT / "notebooks"
KERNEL_NAME = "python3"
KERNEL_DISPLAY_NAME = "Python 3 (Isoprax)"
EXECUTION_TIMEOUT_SECONDS = 180
EXPECTED_NOT_RUN_REPORTS = {
    "01_ai4i2020": 1,
    "02_apachejit": 1,
    "03_nasa_cmapss": 4,
    "04_metropt3": 1,
}
_MACHINE_PATH = re.compile(
    r"(?:/home/[^/\s]+/|/Users/[^/\s]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)",
    re.IGNORECASE,
)


def main() -> int:
    notebook_paths = sorted(NOTEBOOK_DIRECTORY.glob("*.ipynb"))
    if not notebook_paths:
        raise SystemExit(f"No notebooks found in {NOTEBOOK_DIRECTORY}")

    with TemporaryDirectory(prefix="isoprax notebook check ") as empty_data_dir:
        os.environ["ISOPRAX_DATA_DIR"] = empty_data_dir
        for notebook_path in notebook_paths:
            notebook = nbformat.read(notebook_path, as_version=4)
            nbformat.validate(notebook)
            _validate_metadata_and_clean_source(notebook_path, notebook)
            executed = NotebookClient(
                notebook,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                kernel_name=KERNEL_NAME,
                resources={"metadata": {"path": str(NOTEBOOK_DIRECTORY)}},
            ).execute()
            _validate_missing_input_reports(notebook_path, executed)
            print(f"PASS {notebook_path.relative_to(REPOSITORY_ROOT)}")

    print(f"Executed {len(notebook_paths)} notebooks without saving outputs.")
    return 0


def _validate_metadata_and_clean_source(
    notebook_path: Path, notebook: NotebookNode
) -> None:
    metadata = notebook.metadata
    kernelspec = metadata.get("kernelspec", {})
    if (
        kernelspec.get("name") != KERNEL_NAME
        or kernelspec.get("language") != "python"
        or kernelspec.get("display_name") != KERNEL_DISPLAY_NAME
    ):
        raise ValueError(
            f"{notebook_path} must declare the standard Isoprax Python kernel"
        )

    for index, cell in enumerate(notebook.cells):
        if not isinstance(cell.get("id"), str) or not cell.id:
            raise ValueError(f"{notebook_path} cell {index} has no stable cell id")
        source = cell.source if isinstance(cell.source, str) else "".join(cell.source)
        if _MACHINE_PATH.search(source):
            raise ValueError(
                f"{notebook_path} cell {index} contains a machine-specific path"
            )
        if cell.cell_type == "code" and (
            cell.execution_count is not None or cell.outputs
        ):
            raise ValueError(
                f"{notebook_path} cell {index} has saved outputs or an execution count"
            )


def _validate_missing_input_reports(
    notebook_path: Path, notebook: NotebookNode
) -> None:
    expected_reports = EXPECTED_NOT_RUN_REPORTS.get(notebook_path.stem)
    if expected_reports is None:
        return

    not_run_reports = sum(
        "**Verification status:** `not_run`" in output.data.get("text/markdown", "")
        for cell in notebook.cells
        for output in cell.get("outputs", [])
        if output.output_type == "display_data"
    )
    if not_run_reports != expected_reports:
        raise ValueError(
            f"{notebook_path} must display {expected_reports} missing-input `not_run` "
            f"report(s), found {not_run_reports}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
