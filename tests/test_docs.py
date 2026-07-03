from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_readthedocs_config_builds_sphinx_docs() -> None:
    config = (PROJECT_ROOT / ".readthedocs.yaml").read_text()

    assert "configuration: docs/conf.py" in config
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
