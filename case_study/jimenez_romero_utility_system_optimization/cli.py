"""Command-line entry points for OpenUtility reports."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import TextIO

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    CONTRIBUTION2_COMPUTATIONAL_RESULTS,
    CONTRIBUTION2_MODEL_STATISTICS,
    CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS,
    get_contribution2_case_study2_best_configuration,
)
from OpenUtility.style import (
    StaticStyleScenarioCatalog,
    best_configuration_comparison_rows,
    best_configuration_summary_row,
    build_static_style_binary_selection_master,
    compatible_bilevel_candidate_assignments,
    compare_static_style_result_to_best_configuration,
    format_comparison_rows,
    format_style_operating_cost_component_rows,
    format_style_operating_cost_target_rows,
    format_style_candidate_pool_comparison_rows,
    format_style_candidate_pool_rows,
    format_style_candidate_audit_bundle_rows,
    format_style_candidate_selection_delta_rows,
    format_style_candidate_selection_delta_summary_rows,
    format_style_candidate_source_filter_detail_rows,
    format_style_candidate_source_filter_summary_rows,
    format_style_candidate_source_filter_variable_rows,
    format_style_decomposition_objective_comparison_rows,
    format_style_decomposition_skipped_candidate_rows,
    format_style_decomposition_trajectory_rows,
    format_style_fuel_calibration_target_rows,
    format_style_fuel_consumption_capacity_rows,
    format_style_fuel_consumption_diagnosis_rows,
    format_style_fuel_consumption_equipment_rows,
    format_style_fuel_consumption_family_rows,
    format_style_fuel_consumption_residual_ranking_rows,
    format_style_skipped_candidate_delta_summary_rows,
    format_summary_rows,
    style_operating_cost_adjustment_map_from_target_rows,
    style_operating_cost_component_rows,
    style_operating_cost_target_rows,
    run_static_style_binary_selection_candidate_decomposition,
    run_static_style_fixed_assignment_decomposition,
    run_static_style_scenario,
    pyomo_static_style_solver,
    style_binary_selection_candidate_records_from_scenarios,
    style_candidate_audit_bundle_rows,
    style_candidate_pool_comparison_rows,
    style_candidate_pool_rows,
    style_candidate_selection_delta_rows,
    style_candidate_selection_delta_summary_rows,
    style_candidate_source_filter_detail_rows,
    style_candidate_source_filter_summary_rows,
    style_candidate_source_filter_variable_rows,
    style_decomposition_objective_comparison_rows,
    style_decomposition_skipped_candidate_rows,
    style_decomposition_trajectory_rows,
    style_fuel_calibration_target_rows,
    style_fuel_consumption_diagnosis_rows,
    style_fuel_consumption_factor_map_from_calibration_target_rows,
    style_fuel_consumption_capacity_rows,
    style_fuel_consumption_equipment_rows,
    style_fuel_consumption_family_rows,
    style_fuel_consumption_residual_ranking_rows,
    style_skipped_candidate_delta_summary_rows,
)
from case_study.jimenez_romero_utility_system_optimization.contribution2_computational_performance.reporting import (
    contribution2_bilevel_benchmark_trajectory_rows,
    contribution2_computational_best_method_rows,
    contribution2_computational_method_summary_rows,
    contribution2_computational_result_rows,
    contribution2_model_statistic_rows,
    format_contribution2_bilevel_benchmark_trajectory_rows,
    format_contribution2_computational_best_method_rows,
    format_contribution2_computational_method_summary_rows,
    format_contribution2_computational_result_rows,
    format_contribution2_model_statistic_rows,
    format_steam_property_comparison_rows,
    model_derived_steam_property_comparison_rows,
    steam_property_comparison_rows,
)
from case_study.jimenez_romero_utility_system_optimization.style_model_builders import (
    style_case_study_2_contribution2_best_configuration_catalog,
    style_case_study_2_contribution2_physical_profile_catalog,
)


def main(argv: Sequence[str] | None = None, *, stdout: TextIO | None = None) -> int:
    """Run the OpenUtility Table 2-9 report CLI."""

    args = _parse_args(argv)
    output = sys.stdout if stdout is None else stdout
    if args.report == "steam-properties":
        rows = (
            model_derived_steam_property_comparison_rows(
                CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS,
            )
            if args.computed
            else steam_property_comparison_rows(
                CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS
            )
        )
        output.write(
            format_steam_property_comparison_rows(
                rows,
                output_format=args.format,
            ),
        )
        output.write("\n")
        return 0
    if args.report == "model-statistics":
        output.write(
            format_contribution2_model_statistic_rows(
                contribution2_model_statistic_rows(CONTRIBUTION2_MODEL_STATISTICS),
                output_format=args.format,
            ),
        )
        output.write("\n")
        return 0
    if args.report == "computational-results":
        output.write(_format_computational_result_report(args.view, args.format))
        output.write("\n")
        return 0
    if args.report == "style-decomposition":
        if args.view in {
            "candidate-audit-bundle",
            "candidate-trajectory",
            "candidate-summary",
            "candidate-pool",
            "candidate-pool-comparison",
            "candidate-selection-delta",
            "candidate-selection-summary",
            "candidate-skip-delta-summary",
            "candidate-source-detail",
            "candidate-source-summary",
            "candidate-source-variables",
            "candidate-skips",
        }:
            rows = _style_candidate_decomposition_rows(
                solver_time_limit=args.solver_time_limit,
                view=args.view,
            )
            output.write(
                _format_style_candidate_decomposition_rows(
                    rows,
                    view=args.view,
                    output_format=args.format,
                ),
            )
            output.write("\n")
            return 0
        catalog = _style_table_2_9_catalog(
            args.catalog,
            calibrated=not args.uncalibrated,
            apply_fuel_targets=args.apply_fuel_targets,
            apply_operating_targets=args.apply_operating_targets,
            solver_time_limit=args.solver_time_limit,
        )
        rows = _style_decomposition_rows(
            catalog_name=args.catalog,
            catalog=catalog,
            solver_time_limit=args.solver_time_limit,
            view=args.view,
        )
        formatter = (
            format_style_decomposition_objective_comparison_rows
            if args.view == "summary"
            else format_style_decomposition_trajectory_rows
        )
        output.write(
            formatter(rows, output_format=args.format),
        )
        output.write("\n")
        return 0

    catalog = _style_table_2_9_catalog(
        args.catalog,
        calibrated=not args.uncalibrated,
        apply_fuel_targets=args.apply_fuel_targets,
        apply_operating_targets=args.apply_operating_targets,
        solver_time_limit=args.solver_time_limit,
    )
    rows = _style_table_2_9_report_rows(
        catalog_name=args.catalog,
        catalog=catalog,
        solver_time_limit=args.solver_time_limit,
        view=args.view,
    )
    if args.view == "fuel-families":
        output.write(
            format_style_fuel_consumption_family_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-capacity":
        output.write(
            format_style_fuel_consumption_capacity_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-diagnosis":
        output.write(
            format_style_fuel_consumption_diagnosis_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-targets":
        output.write(
            format_style_fuel_calibration_target_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "operating-components":
        output.write(
            format_style_operating_cost_component_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "operating-targets":
        output.write(
            format_style_operating_cost_target_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-equipment":
        output.write(
            format_style_fuel_consumption_equipment_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-ranking":
        output.write(
            format_style_fuel_consumption_residual_ranking_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "summary":
        output.write(format_summary_rows(rows, output_format=args.format))
    else:
        output.write(format_comparison_rows(rows, output_format=args.format))
    output.write("\n")
    return 0


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OpenUtility STYLE case-study replication reports.",
    )
    parser.add_argument(
        "--report",
        choices=(
            "table-2-9",
            "steam-properties",
            "model-statistics",
            "computational-results",
            "style-decomposition",
        ),
        default="table-2-9",
        help="Report to run.",
    )
    parser.add_argument(
        "--computed",
        action="store_true",
        help="Recompute steam-property report values from provider conditions.",
    )
    parser.add_argument(
        "--catalog",
        choices=("reported-equipment", "physical-profile"),
        default="reported-equipment",
        help="Scenario catalog to run.",
    )
    parser.add_argument(
        "--uncalibrated",
        action="store_true",
        help="Run the catalog without benchmark-calibration controls.",
    )
    parser.add_argument(
        "--apply-fuel-targets",
        action="store_true",
        help=(
            "Apply computed physical-profile fuel target factors before running "
            "Table 2-9 reports."
        ),
    )
    parser.add_argument(
        "--apply-operating-targets",
        action="store_true",
        help=(
            "Apply computed physical-profile operating-cost target adjustments "
            "before running Table 2-9 reports."
        ),
    )
    parser.add_argument(
        "--view",
        choices=(
            "detailed",
            "summary",
            "fuel-capacity",
            "fuel-diagnosis",
            "fuel-equipment",
            "fuel-families",
            "fuel-ranking",
            "fuel-targets",
            "operating-components",
            "operating-targets",
            "best-method",
            "method-summary",
            "bilevel-trajectory",
            "candidate-audit-bundle",
            "candidate-trajectory",
            "candidate-summary",
            "candidate-pool",
            "candidate-pool-comparison",
            "candidate-selection-delta",
            "candidate-selection-summary",
            "candidate-skip-delta-summary",
            "candidate-source-detail",
            "candidate-source-summary",
            "candidate-source-variables",
            "candidate-skips",
        ),
        default="detailed",
        help="Report detail level.",
    )
    parser.add_argument(
        "--format",
        choices=("csv", "json"),
        default="csv",
        help="Report output format.",
    )
    parser.add_argument(
        "--solver-time-limit",
        type=float,
        default=20.0,
        help="Pyomo/HiGHS MILP time limit in seconds.",
    )
    return parser.parse_args(argv)


def _style_table_2_9_catalog(
    catalog_name: str,
    *,
    calibrated: bool,
    apply_fuel_targets: bool = False,
    apply_operating_targets: bool = False,
    solver_time_limit: float = 20.0,
) -> StaticStyleScenarioCatalog:
    if catalog_name == "reported-equipment":
        if apply_fuel_targets or apply_operating_targets:
            raise ValueError("target bridges are only available for physical-profile")
        return style_case_study_2_contribution2_best_configuration_catalog(
            match_reported_economics=calibrated,
        )
    if catalog_name == "physical-profile":
        fuel_factors = (
            _physical_profile_fuel_target_factors(
                calibrated=calibrated,
                solver_time_limit=solver_time_limit,
            )
            if apply_fuel_targets
            else None
        )
        operating_adjustments = (
            _physical_profile_operating_cost_target_adjustments(
                calibrated=calibrated,
                solver_time_limit=solver_time_limit,
                fuel_factors_by_scenario=fuel_factors,
            )
            if apply_operating_targets
            else None
        )
        return style_case_study_2_contribution2_physical_profile_catalog(
            calibrated=calibrated,
            fuel_consumption_factors_by_scenario=fuel_factors,
            operating_cost_adjustments_by_scenario=operating_adjustments,
        )
    raise ValueError(f"unsupported STYLE Table 2-9 catalog {catalog_name!r}")


def _physical_profile_fuel_target_factors(
    *,
    calibrated: bool,
    solver_time_limit: float,
) -> dict[str, dict[tuple[str, str], float]]:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=calibrated,
    )
    capacity_rows = _style_table_2_9_report_rows(
        catalog_name="physical-profile",
        catalog=catalog,
        solver_time_limit=solver_time_limit,
        view="fuel-capacity",
    )
    target_rows = style_fuel_calibration_target_rows(capacity_rows)
    return style_fuel_consumption_factor_map_from_calibration_target_rows(target_rows)


def _physical_profile_operating_cost_target_adjustments(
    *,
    calibrated: bool,
    solver_time_limit: float,
    fuel_factors_by_scenario: dict[str, dict[tuple[str, str], float]] | None,
) -> dict[str, dict[str, float]]:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=calibrated,
        fuel_consumption_factors_by_scenario=fuel_factors_by_scenario,
    )
    component_rows = _style_table_2_9_report_rows(
        catalog_name="physical-profile",
        catalog=catalog,
        solver_time_limit=solver_time_limit,
        view="operating-components",
    )
    target_rows = style_operating_cost_target_rows(component_rows)
    return style_operating_cost_adjustment_map_from_target_rows(target_rows)


def _style_table_2_9_report_rows(
    *,
    catalog_name: str,
    catalog: StaticStyleScenarioCatalog,
    solver_time_limit: float,
    view: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    for scenario in catalog:
        run = run_static_style_scenario(scenario, solve=solve)
        if view in {"fuel-capacity", "fuel-diagnosis", "fuel-targets"}:
            rows.extend(
                style_fuel_consumption_capacity_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    model=run.model,
                    benchmark=get_contribution2_case_study2_best_configuration(
                        scenario.scenario,
                    ),
                ),
            )
            continue
        if view == "fuel-equipment":
            rows.extend(
                style_fuel_consumption_equipment_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    model=run.model,
                    benchmark=get_contribution2_case_study2_best_configuration(
                        scenario.scenario,
                    ),
                ),
            )
            continue
        if view in {"fuel-families", "fuel-ranking"}:
            rows.extend(
                style_fuel_consumption_family_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    model=run.model,
                    benchmark=get_contribution2_case_study2_best_configuration(
                        scenario.scenario,
                    ),
                ),
            )
            continue
        if view in {"operating-components", "operating-targets"}:
            rows.extend(
                style_operating_cost_component_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    model=run.model,
                    benchmark=get_contribution2_case_study2_best_configuration(
                        scenario.scenario,
                    ),
                ),
            )
            continue
        comparison = compare_static_style_result_to_best_configuration(
            run.result,
            get_contribution2_case_study2_best_configuration(scenario.scenario),
            absolute_tolerance=scenario.absolute_tolerance,
        )
        if view == "summary":
            rows.append(
                best_configuration_summary_row(
                    catalog=catalog_name,
                    comparison=comparison,
                ),
            )
        else:
            rows.extend(
                best_configuration_comparison_rows(
                    catalog=catalog_name,
                    comparison=comparison,
                ),
            )
    if view == "fuel-ranking":
        return style_fuel_consumption_residual_ranking_rows(rows)
    if view == "fuel-diagnosis":
        return style_fuel_consumption_diagnosis_rows(rows)
    if view == "fuel-targets":
        return style_fuel_calibration_target_rows(rows)
    if view == "operating-targets":
        return style_operating_cost_target_rows(rows)
    return tuple(rows)


def _style_decomposition_rows(
    *,
    catalog_name: str,
    catalog: StaticStyleScenarioCatalog,
    solver_time_limit: float,
    view: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    for scenario in catalog:
        run = run_static_style_fixed_assignment_decomposition(
            scenario,
            solve_master=solve,
            solve_subproblem=solve,
            max_iterations=1,
        )
        if view == "summary":
            rows.extend(
                style_decomposition_objective_comparison_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    run=run,
                    benchmark=get_contribution2_case_study2_best_configuration(
                        scenario.scenario,
                    ),
                ),
            )
        else:
            rows.extend(
                style_decomposition_trajectory_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    run=run,
                ),
            )
    return tuple(rows)


def _style_candidate_decomposition_rows(
    *,
    solver_time_limit: float,
    view: str,
) -> tuple[dict[str, object], ...]:
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    calibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog()
    uncalibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )
    calibrated_scenarios = tuple(calibrated_catalog)
    uncalibrated_scenarios = tuple(uncalibrated_catalog)
    target = calibrated_catalog.get(
        "contribution-2-case-study-2-physical-profile",
        "hot-oil-fsr-microgrid",
    )
    target_variables = build_static_style_binary_selection_master(
        target.data,
    ).master_choice
    candidate_records = style_binary_selection_candidate_records_from_scenarios(
        calibrated_scenarios + uncalibrated_scenarios,
        solve=solve,
        source_label_factory=_candidate_source_label_factory(calibrated_scenarios),
    )
    candidates = compatible_bilevel_candidate_assignments(
        candidate_records,
        variable_names=target_variables,
    )
    if view == "candidate-source-summary":
        return style_candidate_source_filter_summary_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidate_records,
            variable_names=target_variables,
        )
    if view == "candidate-source-detail":
        return style_candidate_source_filter_detail_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidate_records,
            variable_names=target_variables,
        )
    if view == "candidate-source-variables":
        return style_candidate_source_filter_variable_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidate_records,
            variable_names=target_variables,
        )
    if view == "candidate-pool":
        return style_candidate_pool_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
        )
    run = run_static_style_binary_selection_candidate_decomposition(
        target,
        candidates=candidates,
        solve_subproblem=solve,
        max_iterations=2,
    )
    if view == "candidate-summary":
        return style_decomposition_objective_comparison_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            run=run,
            benchmark=get_contribution2_case_study2_best_configuration(
                target.scenario,
            ),
        )
    if view == "candidate-pool-comparison":
        return style_candidate_pool_comparison_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-selection-delta":
        return style_candidate_selection_delta_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-selection-summary":
        return style_candidate_selection_delta_summary_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-skips":
        return style_decomposition_skipped_candidate_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            run=run,
        )
    if view == "candidate-skip-delta-summary":
        return style_skipped_candidate_delta_summary_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            run=run,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-audit-bundle":
        return style_candidate_audit_bundle_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            run=run,
            accepted_assignment=run.best_incumbent().assignment,
        )
    return style_decomposition_trajectory_rows(
        catalog="physical-profile-candidates",
        scenario=target,
        run=run,
    )


def _format_style_candidate_decomposition_rows(
    rows: tuple[dict[str, object], ...],
    *,
    view: str,
    output_format: str,
) -> str:
    if view == "candidate-summary":
        return format_style_decomposition_objective_comparison_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-pool":
        return format_style_candidate_pool_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-pool-comparison":
        return format_style_candidate_pool_comparison_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-selection-delta":
        return format_style_candidate_selection_delta_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-selection-summary":
        return format_style_candidate_selection_delta_summary_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-source-summary":
        return format_style_candidate_source_filter_summary_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-source-detail":
        return format_style_candidate_source_filter_detail_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-source-variables":
        return format_style_candidate_source_filter_variable_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-skips":
        return format_style_decomposition_skipped_candidate_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-skip-delta-summary":
        return format_style_skipped_candidate_delta_summary_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-audit-bundle":
        return format_style_candidate_audit_bundle_rows(
            rows,
            output_format=output_format,
        )
    return format_style_decomposition_trajectory_rows(
        rows,
        output_format=output_format,
    )


def _pyomo_highs_solver(*, solver_time_limit: float):
    return pyomo_static_style_solver(
        "appsi_highs",
        options={"time_limit": solver_time_limit},
    )


def _candidate_source_label_factory(
    calibrated_scenarios: tuple[object, ...],
):
    calibrated_scenario_ids = {id(scenario) for scenario in calibrated_scenarios}

    def source_label(scenario: object) -> str:
        source_catalog = (
            "calibrated" if id(scenario) in calibrated_scenario_ids else "uncalibrated"
        )
        return f"{source_catalog}:{scenario.case_study}:{scenario.scenario}"

    return source_label


def _format_computational_result_report(view: str, output_format: str) -> str:
    if view == "best-method":
        return format_contribution2_computational_best_method_rows(
            contribution2_computational_best_method_rows(
                CONTRIBUTION2_COMPUTATIONAL_RESULTS,
            ),
            output_format=output_format,
        )
    if view == "method-summary":
        return format_contribution2_computational_method_summary_rows(
            contribution2_computational_method_summary_rows(
                CONTRIBUTION2_COMPUTATIONAL_RESULTS,
            ),
            output_format=output_format,
        )
    if view == "bilevel-trajectory":
        return format_contribution2_bilevel_benchmark_trajectory_rows(
            contribution2_bilevel_benchmark_trajectory_rows(
                CONTRIBUTION2_COMPUTATIONAL_RESULTS,
            ),
            output_format=output_format,
        )
    return format_contribution2_computational_result_rows(
        contribution2_computational_result_rows(CONTRIBUTION2_COMPUTATIONAL_RESULTS),
        output_format=output_format,
    )


if __name__ == "__main__":
    raise SystemExit(main())
