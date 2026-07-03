from __future__ import annotations

import importlib.util
from pathlib import Path

from case_study.jimenez_romero_utility_system_optimization import benchmarks
from case_study.jimenez_romero_utility_system_optimization.contribution2_computational_performance import (
    CONTRIBUTION2_MODEL_SIZE_STATISTICS,
    CONTRIBUTION2_SOLVER_PERFORMANCE_RESULTS,
)
from case_study.jimenez_romero_utility_system_optimization.contribution2_integrated_hot_oil_fsr import (
    CONTRIBUTION2_INTEGRATED_HOT_OIL_FSR_BEST_CONFIGURATIONS,
    STYLE_CASE_STUDY_2_TOTAL_SITE_PROCESS_STREAMS,
    STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE,
)
from case_study.jimenez_romero_utility_system_optimization.style_stage1_hot_oil_and_steam_mains import (
    STYLE_STAGE1_HOT_OIL_AND_STEAM_MAIN_DESIGN_RESULTS,
    STYLE_STAGE1_STEAM_SYSTEM_TARGETS,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_extracted_dataset_lives_outside_core_package() -> None:
    core_file = PROJECT_ROOT / "OpenUtility" / "benchmarks.py"
    case_study_file = (
        PROJECT_ROOT
        / "case_study"
        / "jimenez_romero_utility_system_optimization"
        / "benchmarks.py"
    )

    case_study_text = case_study_file.read_text()

    assert not core_file.exists()
    assert "STYLE_CASE_STUDY_2_STREAMS" in case_study_text
    assert "Stream(" in case_study_text
    assert "StyleProcessStream(" not in case_study_text


def test_openutility_benchmarks_compatibility_import_path_is_removed() -> None:
    assert importlib.util.find_spec("OpenUtility.benchmarks") is None


def test_descriptive_case_study_folders_alias_extracted_datasets() -> None:
    assert STYLE_STAGE1_HOT_OIL_AND_STEAM_MAIN_DESIGN_RESULTS is (
        benchmarks.STYLE_CASE_STUDY_1_HOT_OIL_RESULTS
    )
    assert STYLE_STAGE1_STEAM_SYSTEM_TARGETS is (
        benchmarks.STYLE_CASE_STUDY_1_STEAM_TARGETS
    )
    assert CONTRIBUTION2_INTEGRATED_HOT_OIL_FSR_BEST_CONFIGURATIONS is (
        benchmarks.CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS
    )
    assert STYLE_CASE_STUDY_2_TOTAL_SITE_PROCESS_STREAMS is (
        benchmarks.STYLE_CASE_STUDY_2_STREAMS
    )
    assert STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE is (
        benchmarks.STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE
    )
    assert CONTRIBUTION2_SOLVER_PERFORMANCE_RESULTS is (
        benchmarks.CONTRIBUTION2_COMPUTATIONAL_RESULTS
    )
    assert CONTRIBUTION2_MODEL_SIZE_STATISTICS is (
        benchmarks.CONTRIBUTION2_MODEL_STATISTICS
    )


def test_case_study_dataset_exports_descriptive_type_names_only() -> None:
    old_type_names = (
        "ThesisGasTurbineAmbientCorrection",
        "ThesisGasTurbineFullLoadCoefficient",
        "ThesisGasTurbinePartLoadCoefficient",
        "ThesisStyleEquipmentCostCoefficient",
        "ThesisStyleHotOilResult",
        "ThesisStyleResource",
        "ThesisStyleResult",
        "ThesisStyleSiteConfig",
        "ThesisStyleSteamTarget",
        "ThesisStyleStream",
    )
    descriptive_type_names = (
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

    for name in old_type_names:
        assert name not in benchmarks.__all__
        assert not hasattr(benchmarks, name)

    for name in descriptive_type_names:
        assert name in benchmarks.__all__
        assert hasattr(benchmarks, name)
