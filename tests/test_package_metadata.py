from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

import OpenUtility
from case_study.jimenez_romero_utility_system_optimization.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_cli_entry_point_and_packages_case_study_data() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert "OpenPinch>=0.4.5" in pyproject["project"]["dependencies"]
    assert "openpinch" not in pyproject["project"]["optional-dependencies"]
    assert pyproject["project"]["scripts"]["openutility-style-table2-9"] == (
        "case_study.jimenez_romero_utility_system_optimization.cli:main"
    )
    assert pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "OpenUtility",
        "case_study",
    ]
    assert callable(main)


def test_root_api_exposes_generic_core_helpers() -> None:
    current_public_names = (
        "build_temperature_intervals",
        "heat_content_by_interval",
        "BestConfigurationBenchmarkRecord",
        "StyleBenchmarkRecord",
        "run_static_style_scenario",
        "pyomo_static_style_solver",
        "scipy_milp_static_style_solver",
    )

    for name in current_public_names:
        assert name in OpenUtility.__all__
        assert hasattr(OpenUtility, name)


def test_root_api_does_not_expose_removed_compatibility_names() -> None:
    removed_names = (
        "StyleTableCaseStudyNotebookRun",
        "run_style_table_2_9_case_study",
        "ThesisTableCaseStudyNotebookRun",
        "run_thesis_table_2_9_case_study",
        "openpinch_stream_collection_from_stream_records",
        "openpinch_streams_from_stream_records",
        "openpinch_stream_collection_from_case_study_streams",
        "openpinch_streams_from_case_study_streams",
        "openpinch_stream_collection_from_thesis_streams",
        "openpinch_streams_from_thesis_streams",
        "style_case_study_2_contribution2_physical_profile_catalog",
    )

    for name in removed_names:
        assert name not in OpenUtility.__all__
        assert not hasattr(OpenUtility, name)
        with pytest.raises(ImportError):
            _import_from_openutility(name)


def test_openutility_does_not_import_case_study_package() -> None:
    source_files = (PROJECT_ROOT / "OpenUtility").rglob("*.py")

    for path in source_files:
        source = path.read_text()
        assert "from case_study" not in source
        assert "import case_study" not in source


def test_case_study_data_is_not_reexported_from_root_api() -> None:
    benchmarks = importlib.import_module(
        "case_study.jimenez_romero_utility_system_optimization.benchmarks",
    )
    case_study_dataset_names = (
        "CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS",
        "CONTRIBUTION2_COMPUTATIONAL_RESULTS",
        "CONTRIBUTION2_MODEL_STATISTICS",
        "CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS",
        "Contribution2BestConfiguration",
        "Contribution2ComputationalResult",
        "Contribution2ModelStatistic",
        "Contribution2SteamPropertyComparison",
        "STYLE_CASE_STUDY_1_HOT_OIL_RESULTS",
        "STYLE_CASE_STUDY_1_STEAM_TARGETS",
        "STYLE_CASE_STUDY_2_EQUIPMENT_COSTS",
        "STYLE_CASE_STUDY_2_RESOURCES",
        "STYLE_CASE_STUDY_2_RESULTS",
        "STYLE_CASE_STUDY_2_SITE_CONFIG",
        "STYLE_CASE_STUDY_2_STREAMS",
        "STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE",
        "STYLE_GAS_TURBINE_AMBIENT_CORRECTION",
        "STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS",
        "STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS",
        "StyleBenchmarkResult",
        "StyleEquipmentCostCoefficient",
        "StyleGasTurbineAmbientCorrection",
        "StyleGasTurbineFullLoadCoefficient",
        "StyleGasTurbinePartLoadCoefficient",
        "StyleHotOilDesignResult",
        "StyleResource",
        "StyleSiteConfig",
        "StyleSteamSystemTarget",
    )

    for name in case_study_dataset_names:
        assert name in benchmarks.__all__
        assert hasattr(benchmarks, name)
        assert name not in OpenUtility.__all__
        assert not hasattr(OpenUtility, name)


def _import_from_openutility(name: str) -> object:
    namespace: dict[str, object] = {}
    exec(f"from OpenUtility import {name}", namespace)
    return namespace[name]
