from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_readthedocs_config_builds_sphinx_docs() -> None:
    config = (PROJECT_ROOT / ".readthedocs.yaml").read_text()

    assert "configuration: docs/conf.py" in config
    assert 'python: "3.14"' in config
    assert "extra_requirements:" in config
    assert "- docs" in config


def test_docs_index_prioritizes_notebook_workflow() -> None:
    index = (PROJECT_ROOT / "docs" / "index.rst").read_text()

    assert "Notebook-first workflow" in index
    assert "notebook_workflow" in index


def test_notebook_workflow_docs_link_checked_example_notebook() -> None:
    docs = (PROJECT_ROOT / "docs" / "notebook_workflow.rst").read_text()
    notebook = (
        PROJECT_ROOT
        / "case_study"
        / "jimenez_romero_utility_system_optimization"
        / "contribution2_integrated_hot_oil_fsr"
        / "notebooks"
        / "replication.ipynb"
    )

    assert notebook.exists()
    assert (
        "case_study/jimenez_romero_utility_system_optimization/"
        "contribution2_integrated_hot_oil_fsr/notebooks/replication.ipynb"
    ) in docs
    assert "run_contribution2_table_2_9_case_study" in docs


def test_input_docs_explain_openpinch_stream_reuse() -> None:
    docs = (PROJECT_ROOT / "docs" / "inputs.rst").read_text()

    assert "OpenPinch ``Stream``" in docs
    assert "OpenPinch ``StreamCollection``" in docs
    assert "OpenPinch ``Zone``" in docs
    assert "``heat_load`` is mapped to OpenPinch ``heat_flow``" in docs
    assert "``dt_cont`` is half the extracted minimum temperature difference" in docs


def test_case_study_notebooks_advertise_python_314_kernel() -> None:
    notebook_paths = sorted(
        (
            PROJECT_ROOT / "case_study" / "jimenez_romero_utility_system_optimization"
        ).glob("**/notebooks/*.ipynb"),
    )

    assert len(notebook_paths) == 3
    for path in notebook_paths:
        notebook = json.loads(path.read_text())
        metadata = notebook["metadata"]
        assert metadata["kernelspec"]["display_name"] == "Python 3.14"
        assert metadata["kernelspec"]["name"] == "python3"
        assert metadata["language_info"]["version"] == "3.14"
