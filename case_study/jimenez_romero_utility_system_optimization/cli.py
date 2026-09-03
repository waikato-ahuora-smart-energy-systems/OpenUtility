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
from OpenUtility.utility_system import (
    UtilitySystemScenarioCatalog,
    best_configuration_comparison_rows,
    best_configuration_summary_row,
    build_utility_system_binary_selection_master,
    compatible_bilevel_candidate_assignments,
    compare_utility_system_result_to_best_configuration,
    format_comparison_rows,
    format_utility_system_operating_cost_component_rows,
    format_utility_system_operating_cost_target_rows,
    format_utility_system_candidate_pool_comparison_rows,
    format_utility_system_candidate_pool_rows,
    format_utility_system_candidate_audit_bundle_rows,
    format_utility_system_candidate_selection_delta_rows,
    format_utility_system_candidate_selection_delta_summary_rows,
    format_utility_system_candidate_source_filter_detail_rows,
    format_utility_system_candidate_source_filter_summary_rows,
    format_utility_system_candidate_source_filter_variable_rows,
    format_utility_system_decomposition_objective_comparison_rows,
    format_utility_system_decomposition_skipped_candidate_rows,
    format_utility_system_decomposition_trajectory_rows,
    format_utility_system_fuel_calibration_target_rows,
    format_utility_system_fuel_consumption_capacity_rows,
    format_utility_system_fuel_consumption_diagnosis_rows,
    format_utility_system_fuel_consumption_equipment_rows,
    format_utility_system_fuel_consumption_family_rows,
    format_utility_system_fuel_consumption_residual_ranking_rows,
    format_utility_system_skipped_candidate_delta_summary_rows,
    format_summary_rows,
    utility_system_operating_cost_adjustment_map_from_target_rows,
    utility_system_operating_cost_component_rows,
    utility_system_operating_cost_target_rows,
    run_utility_system_binary_selection_candidate_decomposition,
    run_utility_system_fixed_assignment_decomposition,
    run_utility_system_scenario,
    pyomo_utility_system_solver,
    utility_system_binary_selection_candidate_records_from_scenarios,
    utility_system_candidate_audit_bundle_rows,
    utility_system_candidate_pool_comparison_rows,
    utility_system_candidate_pool_rows,
    utility_system_candidate_selection_delta_rows,
    utility_system_candidate_selection_delta_summary_rows,
    utility_system_candidate_source_filter_detail_rows,
    utility_system_candidate_source_filter_summary_rows,
    utility_system_candidate_source_filter_variable_rows,
    utility_system_decomposition_objective_comparison_rows,
    utility_system_decomposition_skipped_candidate_rows,
    utility_system_decomposition_trajectory_rows,
    utility_system_fuel_calibration_target_rows,
    utility_system_fuel_consumption_diagnosis_rows,
    utility_system_fuel_consumption_factor_map_from_calibration_target_rows,
    utility_system_fuel_consumption_capacity_rows,
    utility_system_fuel_consumption_equipment_rows,
    utility_system_fuel_consumption_family_rows,
    utility_system_fuel_consumption_residual_ranking_rows,
    utility_system_skipped_candidate_delta_summary_rows,
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
    if args.report == "utility-system-decomposition":
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
            rows = _utility_system_candidate_decomposition_rows(
                solver_time_limit=args.solver_time_limit,
                view=args.view,
            )
            output.write(
                _format_utility_system_candidate_decomposition_rows(
                    rows,
                    view=args.view,
                    output_format=args.format,
                ),
            )
            output.write("\n")
            return 0
        catalog = _table_2_9_catalog(
            args.catalog,
            calibrated=not args.uncalibrated,
            apply_fuel_targets=args.apply_fuel_targets,
            apply_operating_targets=args.apply_operating_targets,
            solver_time_limit=args.solver_time_limit,
        )
        rows = _utility_system_decomposition_rows(
            catalog_name=args.catalog,
            catalog=catalog,
            solver_time_limit=args.solver_time_limit,
            view=args.view,
        )
        formatter = (
            format_utility_system_decomposition_objective_comparison_rows
            if args.view == "summary"
            else format_utility_system_decomposition_trajectory_rows
        )
        output.write(
            formatter(rows, output_format=args.format),
        )
        output.write("\n")
        return 0

    catalog = _table_2_9_catalog(
        args.catalog,
        calibrated=not args.uncalibrated,
        apply_fuel_targets=args.apply_fuel_targets,
        apply_operating_targets=args.apply_operating_targets,
        solver_time_limit=args.solver_time_limit,
    )
    rows = _table_2_9_report_rows(
        catalog_name=args.catalog,
        catalog=catalog,
        solver_time_limit=args.solver_time_limit,
        view=args.view,
    )
    if args.view == "fuel-families":
        output.write(
            format_utility_system_fuel_consumption_family_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-capacity":
        output.write(
            format_utility_system_fuel_consumption_capacity_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-diagnosis":
        output.write(
            format_utility_system_fuel_consumption_diagnosis_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-targets":
        output.write(
            format_utility_system_fuel_calibration_target_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "operating-components":
        output.write(
            format_utility_system_operating_cost_component_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "operating-targets":
        output.write(
            format_utility_system_operating_cost_target_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-equipment":
        output.write(
            format_utility_system_fuel_consumption_equipment_rows(
                rows,
                output_format=args.format,
            ),
        )
    elif args.view == "fuel-ranking":
        output.write(
            format_utility_system_fuel_consumption_residual_ranking_rows(
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
        description="Run packaged OpenUtility case-study replication reports.",
    )
    parser.add_argument(
        "--report",
        choices=(
            "table-2-9",
            "steam-properties",
            "model-statistics",
            "computational-results",
            "utility-system-decomposition",
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


def _table_2_9_catalog(
    catalog_name: str,
    *,
    calibrated: bool,
    apply_fuel_targets: bool = False,
    apply_operating_targets: bool = False,
    solver_time_limit: float = 20.0,
) -> UtilitySystemScenarioCatalog:
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
    raise ValueError(f"unsupported Table 2-9 catalog {catalog_name!r}")


def _physical_profile_fuel_target_factors(
    *,
    calibrated: bool,
    solver_time_limit: float,
) -> dict[str, dict[tuple[str, str], float]]:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=calibrated,
    )
    capacity_rows = _table_2_9_report_rows(
        catalog_name="physical-profile",
        catalog=catalog,
        solver_time_limit=solver_time_limit,
        view="fuel-capacity",
    )
    target_rows = utility_system_fuel_calibration_target_rows(capacity_rows)
    return utility_system_fuel_consumption_factor_map_from_calibration_target_rows(target_rows)


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
    component_rows = _table_2_9_report_rows(
        catalog_name="physical-profile",
        catalog=catalog,
        solver_time_limit=solver_time_limit,
        view="operating-components",
    )
    target_rows = utility_system_operating_cost_target_rows(component_rows)
    return utility_system_operating_cost_adjustment_map_from_target_rows(target_rows)


def _table_2_9_report_rows(
    *,
    catalog_name: str,
    catalog: UtilitySystemScenarioCatalog,
    solver_time_limit: float,
    view: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    for scenario in catalog:
        run = run_utility_system_scenario(scenario, solve=solve)
        if view in {"fuel-capacity", "fuel-diagnosis", "fuel-targets"}:
            rows.extend(
                utility_system_fuel_consumption_capacity_rows(
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
                utility_system_fuel_consumption_equipment_rows(
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
                utility_system_fuel_consumption_family_rows(
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
                utility_system_operating_cost_component_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    model=run.model,
                    benchmark=get_contribution2_case_study2_best_configuration(
                        scenario.scenario,
                    ),
                ),
            )
            continue
        comparison = compare_utility_system_result_to_best_configuration(
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
        return utility_system_fuel_consumption_residual_ranking_rows(rows)
    if view == "fuel-diagnosis":
        return utility_system_fuel_consumption_diagnosis_rows(rows)
    if view == "fuel-targets":
        return utility_system_fuel_calibration_target_rows(rows)
    if view == "operating-targets":
        return utility_system_operating_cost_target_rows(rows)
    return tuple(rows)


def _utility_system_decomposition_rows(
    *,
    catalog_name: str,
    catalog: UtilitySystemScenarioCatalog,
    solver_time_limit: float,
    view: str,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    for scenario in catalog:
        run = run_utility_system_fixed_assignment_decomposition(
            scenario,
            solve_master=solve,
            solve_subproblem=solve,
            max_iterations=1,
        )
        if view == "summary":
            rows.extend(
                utility_system_decomposition_objective_comparison_rows(
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
                utility_system_decomposition_trajectory_rows(
                    catalog=catalog_name,
                    scenario=scenario,
                    run=run,
                ),
            )
    return tuple(rows)


def _utility_system_candidate_decomposition_rows(
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
    target_variables = build_utility_system_binary_selection_master(
        target.data,
    ).master_choice
    candidate_records = utility_system_binary_selection_candidate_records_from_scenarios(
        calibrated_scenarios + uncalibrated_scenarios,
        solve=solve,
        source_label_factory=_candidate_source_label_factory(calibrated_scenarios),
    )
    candidates = compatible_bilevel_candidate_assignments(
        candidate_records,
        variable_names=target_variables,
    )
    if view == "candidate-source-summary":
        return utility_system_candidate_source_filter_summary_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidate_records,
            variable_names=target_variables,
        )
    if view == "candidate-source-detail":
        return utility_system_candidate_source_filter_detail_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidate_records,
            variable_names=target_variables,
        )
    if view == "candidate-source-variables":
        return utility_system_candidate_source_filter_variable_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidate_records,
            variable_names=target_variables,
        )
    if view == "candidate-pool":
        return utility_system_candidate_pool_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
        )
    run = run_utility_system_binary_selection_candidate_decomposition(
        target,
        candidates=candidates,
        solve_subproblem=solve,
        max_iterations=2,
    )
    if view == "candidate-summary":
        return utility_system_decomposition_objective_comparison_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            run=run,
            benchmark=get_contribution2_case_study2_best_configuration(
                target.scenario,
            ),
        )
    if view == "candidate-pool-comparison":
        return utility_system_candidate_pool_comparison_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-selection-delta":
        return utility_system_candidate_selection_delta_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-selection-summary":
        return utility_system_candidate_selection_delta_summary_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-skips":
        return utility_system_decomposition_skipped_candidate_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            run=run,
        )
    if view == "candidate-skip-delta-summary":
        return utility_system_skipped_candidate_delta_summary_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            run=run,
            accepted_assignment=run.best_incumbent().assignment,
        )
    if view == "candidate-audit-bundle":
        return utility_system_candidate_audit_bundle_rows(
            catalog="physical-profile-candidates",
            scenario=target,
            candidates=candidates,
            run=run,
            accepted_assignment=run.best_incumbent().assignment,
        )
    return utility_system_decomposition_trajectory_rows(
        catalog="physical-profile-candidates",
        scenario=target,
        run=run,
    )


def _format_utility_system_candidate_decomposition_rows(
    rows: tuple[dict[str, object], ...],
    *,
    view: str,
    output_format: str,
) -> str:
    if view == "candidate-summary":
        return format_utility_system_decomposition_objective_comparison_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-pool":
        return format_utility_system_candidate_pool_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-pool-comparison":
        return format_utility_system_candidate_pool_comparison_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-selection-delta":
        return format_utility_system_candidate_selection_delta_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-selection-summary":
        return format_utility_system_candidate_selection_delta_summary_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-source-summary":
        return format_utility_system_candidate_source_filter_summary_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-source-detail":
        return format_utility_system_candidate_source_filter_detail_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-source-variables":
        return format_utility_system_candidate_source_filter_variable_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-skips":
        return format_utility_system_decomposition_skipped_candidate_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-skip-delta-summary":
        return format_utility_system_skipped_candidate_delta_summary_rows(
            rows,
            output_format=output_format,
        )
    if view == "candidate-audit-bundle":
        return format_utility_system_candidate_audit_bundle_rows(
            rows,
            output_format=output_format,
        )
    return format_utility_system_decomposition_trajectory_rows(
        rows,
        output_format=output_format,
    )


def _pyomo_highs_solver(*, solver_time_limit: float):
    return pyomo_utility_system_solver(
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
