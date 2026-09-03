from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_readthedocs_config_builds_sphinx_docs() -> None:
    config = (PROJECT_ROOT / ".readthedocs.yaml").read_text()

    assert "configuration: docs/conf.py" in config
    assert 'python: "3.14"' in config
    assert "extra_requirements:" in config
    assert "- docs" in config


def test_docs_index_prioritizes_reusable_package_api() -> None:
    index = (PROJECT_ROOT / "docs" / "index.rst").read_text()

    assert "reusable package" in index
    assert "api" in index


def test_notebook_workflow_docs_describe_package_local_examples() -> None:
    docs = (PROJECT_ROOT / "docs" / "notebook_workflow.rst").read_text()

    assert "minimal reproducible example" in docs
    assert "OpenUtility" in docs


def test_input_docs_explain_plain_thermal_and_hpr_data_boundary() -> None:
    docs = (PROJECT_ROOT / "docs" / "inputs.rst").read_text()

    assert "stream-like object" in docs
    assert "OpenUtility does not import OpenPinch" in docs
    assert "HPR is the umbrella term for heat pump and refrigeration assets" in docs
    assert "HprPerformanceMap" in docs
    assert "HprCandidate" in docs
