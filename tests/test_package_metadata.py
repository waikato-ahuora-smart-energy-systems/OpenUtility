from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import pytest

import OpenUtility


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_release_metadata_for_reusable_package() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["requires-python"] == ">=3.14.2"
    assert pyproject["project"]["license"] == "MIT"
    assert pyproject["project"]["license-files"] == ["LICENSE"]
    assert "highspy>=1.15.1" in pyproject["project"]["dependencies"]
    assert not any(
        dependency.lower().startswith("openpinch")
        for dependency in pyproject["project"]["dependencies"]
    )
    assert "scipy>=1.11" not in pyproject["project"]["dependencies"]
    assert "openpinch" not in pyproject["project"]["optional-dependencies"]
    assert "mypy>=1.18" in pyproject["project"]["optional-dependencies"]["dev"]
    assert "pytest-cov>=7.0" in pyproject["project"]["optional-dependencies"]["dev"]
    assert "build>=1.3" in pyproject["project"]["optional-dependencies"]["release"]
    assert "hatchling>=1.26" in pyproject["project"]["optional-dependencies"]["release"]
    assert "pip>=26.2" in pyproject["project"]["optional-dependencies"]["release"]
    assert "pip-audit>=2.9" in pyproject["project"]["optional-dependencies"]["release"]
    assert "twine>=6.2" in pyproject["project"]["optional-dependencies"]["release"]
    assert "scripts" not in pyproject["project"]
    assert pyproject["project"]["urls"]["Repository"] == (
        "https://github.com/waikato-ahuora-smart-energy-systems/OpenUtility"
    )
    assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "OpenUtility",
    ]
    assert (
        "/OpenUtility/py.typed"
        in pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["include"]
    )
    assert (PROJECT_ROOT / "OpenUtility" / "py.typed").exists()
    assert (PROJECT_ROOT / "LICENSE").exists()


def test_aidlc_v1_scaffold_is_installed() -> None:
    assert (PROJECT_ROOT / "AGENTS.md").exists()
    assert (
        PROJECT_ROOT / ".aidlc-rule-details" / "common" / "process-overview.md"
    ).exists()
    assert (
        PROJECT_ROOT / ".aidlc-rule-details" / "inception" / "workspace-detection.md"
    ).exists()
    state = (PROJECT_ROOT / "aidlc-docs" / "aidlc-state.md").read_text()
    assert "AI-DLC v1 scaffold installed" in state
    assert "Workspace Root**: /Users/timothyw/Github_Local/OpenUtility" in state


def test_root_api_exposes_generic_core_helpers() -> None:
    current_public_names = (
        "build_temperature_intervals",
        "heat_content_by_interval",
        "HprCandidate",
        "HprPerformanceMap",
        "HprPerformancePoint",
        "hpr_performance_map_from_mapping",
        "OperatingPeriod",
        "ThermalNode",
        "BestConfigurationBenchmarkRecord",
        "UtilitySystemBenchmarkRecord",
        "run_utility_system_scenario",
        "pyomo_utility_system_solver",
    )

    for name in current_public_names:
        assert name in OpenUtility.__all__
        assert hasattr(OpenUtility, name)


def test_root_api_does_not_expose_removed_compatibility_names() -> None:
    removed_names = (
        "openpinch_stream_collection_from_stream_records",
        "openpinch_streams_from_stream_records",
    )

    for name in removed_names:
        assert name not in OpenUtility.__all__
        assert not hasattr(OpenUtility, name)
        with pytest.raises(ImportError):
            _import_from_openutility(name)


def test_openutility_cold_import_does_not_import_openpinch_or_tespy() -> None:
    assert "OpenPinch" not in sys.modules
    assert "tespy" not in sys.modules


def _import_from_openutility(name: str) -> object:
    namespace: dict[str, object] = {}
    exec(f"from OpenUtility import {name}", namespace)
    return namespace[name]
