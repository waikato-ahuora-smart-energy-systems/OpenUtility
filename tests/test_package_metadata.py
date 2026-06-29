from __future__ import annotations

import tomllib
from pathlib import Path

import OpenUtility
from OpenUtility.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_declares_cli_entry_point() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())

    assert pyproject["project"]["scripts"]["openutility-style-table2-9"] == (
        "OpenUtility.cli:main"
    )
    assert callable(main)


def test_root_api_exports_reporting_and_physical_profile_catalog() -> None:
    case_study_dataset_exports = (
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
        "STYLE_GAS_TURBINE_AMBIENT_CORRECTION",
        "STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS",
        "STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS",
        "StyleBenchmarkResult",
        "StyleEquipmentCostCoefficient",
        "StyleGasTurbineAmbientCorrection",
        "StyleGasTurbineFullLoadCoefficient",
        "StyleGasTurbinePartLoadCoefficient",
        "StyleHotOilDesignResult",
        "StyleProcessStream",
        "StyleResource",
        "StyleSiteConfig",
        "StyleSteamSystemTarget",
    )

    for name in case_study_dataset_exports:
        assert name not in OpenUtility.__all__
        assert not hasattr(OpenUtility, name)

    assert "BilevelCandidateAssignment" in OpenUtility.__all__
    assert "BilevelDecompositionIteration" in OpenUtility.__all__
    assert "BilevelDecompositionRun" in OpenUtility.__all__
    assert "BilevelIncumbent" in OpenUtility.__all__
    assert "BilevelIntegerAssignment" in OpenUtility.__all__
    assert "BilevelSkippedCandidate" in OpenUtility.__all__
    assert "BilevelSolutionPool" in OpenUtility.__all__
    assert "BilevelSubproblemResult" in OpenUtility.__all__
    assert "FuelConsumptionAccountingFactor" in OpenUtility.__all__
    assert "OperatingCostAccountingAdjustment" in OpenUtility.__all__
    assert "StyleTableCaseStudyNotebookRun" in OpenUtility.__all__
    assert "ThesisTableCaseStudyNotebookRun" not in OpenUtility.__all__
    assert not hasattr(OpenUtility, "ThesisTableCaseStudyNotebookRun")
    assert "StaticStyleFuelCapacityContext" in OpenUtility.__all__
    assert "StaticStyleFuelConsumptionEquipment" in OpenUtility.__all__
    assert "StaticStyleFuelConsumptionFamily" in OpenUtility.__all__
    assert "StaticStyleOperatingCostComponent" in OpenUtility.__all__
    assert "add_bilevel_no_good_cuts" in OpenUtility.__all__
    assert "bilevel_incumbents_from_computational_results" in OpenUtility.__all__
    assert "bilevel_no_good_cut_expression" in OpenUtility.__all__
    assert "build_bilevel_master_with_no_good_cuts" in OpenUtility.__all__
    assert "build_static_style_binary_selection_master" in OpenUtility.__all__
    assert "compatible_bilevel_candidate_assignments" in OpenUtility.__all__
    assert "compatible_bilevel_integer_assignments" in OpenUtility.__all__
    assert "bilevel_candidate_audit_bundle_rows" in OpenUtility.__all__
    assert "bilevel_decomposition_run_rows" in OpenUtility.__all__
    assert "bilevel_candidate_pool_rows" in OpenUtility.__all__
    assert "bilevel_candidate_pool_comparison_rows" in OpenUtility.__all__
    assert "bilevel_candidate_selection_delta_rows" in OpenUtility.__all__
    assert "bilevel_candidate_selection_delta_summary_rows" in OpenUtility.__all__
    assert "bilevel_candidate_source_filter_detail_rows" in OpenUtility.__all__
    assert "bilevel_candidate_source_filter_summary_rows" in OpenUtility.__all__
    assert "bilevel_candidate_source_filter_variable_rows" in OpenUtility.__all__
    assert "bilevel_skipped_candidate_rows" in OpenUtility.__all__
    assert "bilevel_skipped_candidate_delta_summary_rows" in OpenUtility.__all__
    assert "contribution2_bilevel_benchmark_trajectory_rows" in OpenUtility.__all__
    assert "contribution2_bilevel_trajectory_comparison_rows" in OpenUtility.__all__
    assert "contribution2_synthetic_bilevel_decomposition_run" in OpenUtility.__all__
    assert "fix_style_master_integer_assignment" in OpenUtility.__all__
    assert "format_bilevel_candidate_audit_bundle_rows" in OpenUtility.__all__
    assert "format_bilevel_decomposition_run_rows" in OpenUtility.__all__
    assert "format_bilevel_candidate_pool_rows" in OpenUtility.__all__
    assert "format_bilevel_candidate_pool_comparison_rows" in OpenUtility.__all__
    assert "format_bilevel_candidate_selection_delta_rows" in OpenUtility.__all__
    assert "format_bilevel_candidate_selection_delta_summary_rows" in (
        OpenUtility.__all__
    )
    assert "format_bilevel_candidate_source_filter_detail_rows" in (
        OpenUtility.__all__
    )
    assert "format_bilevel_candidate_source_filter_summary_rows" in (
        OpenUtility.__all__
    )
    assert "format_bilevel_candidate_source_filter_variable_rows" in (
        OpenUtility.__all__
    )
    assert "format_bilevel_skipped_candidate_rows" in OpenUtility.__all__
    assert "format_bilevel_skipped_candidate_delta_summary_rows" in (
        OpenUtility.__all__
    )
    assert "format_contribution2_bilevel_benchmark_trajectory_rows" in (
        OpenUtility.__all__
    )
    assert "format_contribution2_bilevel_trajectory_comparison_rows" in (
        OpenUtility.__all__
    )
    assert "format_style_decomposition_objective_comparison_rows" in (
        OpenUtility.__all__
    )
    assert "format_style_candidate_audit_bundle_rows" in OpenUtility.__all__
    assert "format_style_candidate_pool_rows" in OpenUtility.__all__
    assert "format_style_candidate_pool_comparison_rows" in OpenUtility.__all__
    assert "format_style_candidate_selection_delta_rows" in OpenUtility.__all__
    assert "format_style_candidate_selection_delta_summary_rows" in (
        OpenUtility.__all__
    )
    assert "format_style_candidate_source_filter_detail_rows" in OpenUtility.__all__
    assert "format_style_candidate_source_filter_summary_rows" in OpenUtility.__all__
    assert "format_style_candidate_source_filter_variable_rows" in OpenUtility.__all__
    assert "format_style_decomposition_skipped_candidate_rows" in OpenUtility.__all__
    assert "format_style_skipped_candidate_delta_summary_rows" in (
        OpenUtility.__all__
    )
    assert "format_style_decomposition_trajectory_rows" in OpenUtility.__all__
    assert "format_style_operating_cost_component_rows" in OpenUtility.__all__
    assert "format_style_operating_cost_target_rows" in OpenUtility.__all__
    assert "format_style_fuel_calibration_target_rows" in OpenUtility.__all__
    assert "format_style_fuel_consumption_capacity_rows" in OpenUtility.__all__
    assert "format_style_fuel_consumption_diagnosis_rows" in OpenUtility.__all__
    assert "format_style_fuel_consumption_equipment_rows" in OpenUtility.__all__
    assert "format_style_fuel_consumption_family_rows" in OpenUtility.__all__
    assert "format_style_fuel_consumption_residual_ranking_rows" in (
        OpenUtility.__all__
    )
    assert "contribution2_reported_bilevel_decomposition_run" in OpenUtility.__all__
    assert "run_bilevel_decomposition" in OpenUtility.__all__
    assert "run_bilevel_decomposition_iteration" in OpenUtility.__all__
    assert "run_static_style_binary_selection_candidate_decomposition" in (
        OpenUtility.__all__
    )
    assert "run_static_style_binary_selection_decomposition" in OpenUtility.__all__
    assert "run_static_style_fixed_assignment_decomposition" in OpenUtility.__all__
    assert "run_style_table_2_9_case_study" in OpenUtility.__all__
    assert "run_thesis_table_2_9_case_study" not in OpenUtility.__all__
    assert not hasattr(OpenUtility, "run_thesis_table_2_9_case_study")
    assert "style_binary_selection_candidate_from_scenario" in OpenUtility.__all__
    assert "style_binary_selection_candidate_records_from_scenarios" in (
        OpenUtility.__all__
    )
    assert "style_binary_selection_candidate_solver" in OpenUtility.__all__
    assert "style_binary_selection_candidates_from_scenarios" in OpenUtility.__all__
    assert "style_binary_selection_master_assignment_from_model" in OpenUtility.__all__
    assert "style_operating_cost_adjustment_map_from_target_rows" in (
        OpenUtility.__all__
    )
    assert "style_candidate_audit_bundle_rows" in OpenUtility.__all__
    assert "style_candidate_pool_rows" in OpenUtility.__all__
    assert "style_candidate_pool_comparison_rows" in OpenUtility.__all__
    assert "style_candidate_selection_delta_rows" in OpenUtility.__all__
    assert "style_candidate_selection_delta_summary_rows" in OpenUtility.__all__
    assert "style_candidate_source_filter_detail_rows" in OpenUtility.__all__
    assert "style_candidate_source_filter_summary_rows" in OpenUtility.__all__
    assert "style_candidate_source_filter_variable_rows" in OpenUtility.__all__
    assert "style_decomposition_objective_comparison_rows" in OpenUtility.__all__
    assert "style_operating_cost_component_rows" in OpenUtility.__all__
    assert "style_operating_cost_target_rows" in OpenUtility.__all__
    assert "style_skipped_candidate_delta_summary_rows" in OpenUtility.__all__
    assert "style_decomposition_skipped_candidate_rows" in OpenUtility.__all__
    assert "style_decomposition_trajectory_rows" in OpenUtility.__all__
    assert "style_fuel_calibration_target_rows" in OpenUtility.__all__
    assert (
        "style_fuel_consumption_factor_map_from_calibration_target_rows"
        in OpenUtility.__all__
    )
    assert "style_fuel_consumption_capacity_rows" in OpenUtility.__all__
    assert "style_fuel_consumption_diagnosis_rows" in OpenUtility.__all__
    assert "style_fuel_consumption_equipment_rows" in OpenUtility.__all__
    assert "style_fuel_consumption_family_rows" in OpenUtility.__all__
    assert "style_fuel_consumption_residual_ranking_rows" in OpenUtility.__all__
    assert "style_fixed_assignment_subproblem_result" in OpenUtility.__all__
    assert "static_style_fuel_capacity_context_by_equipment" in OpenUtility.__all__
    assert "static_style_fuel_consumption_by_equipment" in OpenUtility.__all__
    assert "static_style_fuel_consumption_by_family" in OpenUtility.__all__
    assert "static_style_operating_cost_components" in OpenUtility.__all__
    assert "style_master_binary_variables" in OpenUtility.__all__
    assert "style_master_integer_assignment_from_model" in OpenUtility.__all__
    assert "best_configuration_comparison_rows" in OpenUtility.__all__
    assert "best_configuration_summary_row" in OpenUtility.__all__
    assert "format_comparison_rows" in OpenUtility.__all__
    assert "format_summary_rows" in OpenUtility.__all__
    assert "openpinch_stream_collection_from_case_study_streams" in (
        OpenUtility.__all__
    )
    assert "openpinch_stream_collection_from_thesis_streams" not in OpenUtility.__all__
    assert not hasattr(OpenUtility, "openpinch_stream_collection_from_thesis_streams")
    assert "openpinch_streams_from_case_study_streams" in OpenUtility.__all__
    assert "openpinch_streams_from_thesis_streams" not in OpenUtility.__all__
    assert not hasattr(OpenUtility, "openpinch_streams_from_thesis_streams")
    assert "style_case_study_2_contribution2_physical_profile_catalog" in (
        OpenUtility.__all__
    )
