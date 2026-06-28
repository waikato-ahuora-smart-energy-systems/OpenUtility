"""Reporting helpers for solved STYLE benchmark comparisons."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Sequence
from io import StringIO
from typing import Any

from OpenUtility.benchmarks import (
    CONTRIBUTION2_COMPUTATIONAL_RESULTS,
    CONTRIBUTION2_MODEL_STATISTICS,
    CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS,
    Contribution2BestConfiguration,
    Contribution2ComputationalResult,
    Contribution2ModelStatistic,
    Contribution2SteamPropertyComparison,
)

from .bilevel import (
    BilevelCandidateAssignment,
    BilevelDecompositionRun,
    BilevelDecompositionIteration,
    compatible_bilevel_candidate_assignments,
)
from .properties import CoolPropSteamPropertyProvider, SteamPropertyProvider
from .results import (
    StaticStyleBestConfigurationComparison,
    static_style_fuel_capacity_context_by_equipment,
    static_style_fuel_consumption_by_equipment,
    static_style_fuel_consumption_by_family,
    static_style_operating_cost_components,
)
from .runner import StaticStyleScenario

COMPARISON_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "field",
    "actual",
    "benchmark",
    "absolute_deviation",
    "within_tolerance",
)
SUMMARY_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "within_tolerance",
    "max_absolute_deviation",
    "failing_fields",
)
STEAM_PROPERTY_ROW_FIELDS = (
    "configuration",
    "turbine",
    "inlet_temperature",
    "inlet_pressure",
    "outlet_pressure",
    "real_isentropic_enthalpy_change",
    "model_isentropic_enthalpy_change",
    "enthalpy_change_deviation",
    "iapws_power_generation",
    "model_power_generation",
    "power_generation_deviation",
)
MODEL_STATISTIC_ROW_FIELDS = (
    "test_number",
    "reference",
    "steam_mains",
    "power_demand",
    "integrates_hot_oil_and_fsr",
    "variable_count",
    "binary_count",
    "equation_count",
)
COMPUTATIONAL_RESULT_ROW_FIELDS = (
    "test_number",
    "scenario",
    "method",
    "best_solution_found",
    "best_possible",
    "optimality_gap",
    "computational_time_seconds",
    "hit_time_limit",
)
COMPUTATIONAL_BEST_METHOD_ROW_FIELDS = (
    "test_number",
    "scenario",
    "best_method",
    "best_solution_found",
    "best_possible",
    "optimality_gap",
    "computational_time_seconds",
    "hit_time_limit",
)
COMPUTATIONAL_METHOD_SUMMARY_ROW_FIELDS = (
    "method",
    "result_count",
    "best_solution_count",
    "time_limit_count",
    "mean_computational_time_seconds",
)
BILEVEL_DECOMPOSITION_RUN_ROW_FIELDS = (
    "iteration_index",
    "candidate_source",
    "objective_value",
    "best_bound",
    "optimality_gap",
    "elapsed_seconds",
    "hit_time_limit",
    "selected_binary_count",
    "unselected_binary_count",
    "subproblem_status",
    "stop_reason",
    "skipped_candidate_count",
)
BILEVEL_SKIPPED_CANDIDATE_ROW_FIELDS = (
    "skip_index",
    "candidate_label",
    "candidate_source",
    "selected_binary_count",
    "unselected_binary_count",
    "selected_variables",
    "reason",
)
BILEVEL_CANDIDATE_POOL_ROW_FIELDS = (
    "candidate_index",
    "candidate_source",
    "selected_binary_count",
    "unselected_binary_count",
    "selected_variables",
)
BILEVEL_CANDIDATE_POOL_COMPARISON_ROW_FIELDS = (
    "candidate_index",
    "candidate_source",
    "hamming_distance_to_accepted",
    "matches_accepted",
    "selected_binary_count",
    "unselected_binary_count",
)
BILEVEL_CANDIDATE_SELECTION_DELTA_ROW_FIELDS = (
    "candidate_index",
    "candidate_source",
    "variable_name",
    "accepted_value",
    "candidate_value",
    "delta_type",
)
BILEVEL_CANDIDATE_SELECTION_DELTA_SUMMARY_ROW_FIELDS = (
    "candidate_index",
    "candidate_source",
    "component_name",
    "accepted_only_count",
    "candidate_only_count",
    "total_delta_count",
)
BILEVEL_CANDIDATE_SOURCE_FILTER_SUMMARY_ROW_FIELDS = (
    "source_record_count",
    "compatible_candidate_count",
    "incompatible_candidate_count",
    "target_variable_count",
    "candidate_sources",
    "compatible_candidate_sources",
    "incompatible_candidate_sources",
)
BILEVEL_CANDIDATE_SOURCE_FILTER_DETAIL_ROW_FIELDS = (
    "candidate_index",
    "source_catalog",
    "candidate_source",
    "target_variable_count",
    "candidate_variable_count",
    "selected_binary_count",
    "unselected_binary_count",
    "compatible_with_target",
    "missing_target_variable_count",
    "extra_candidate_variable_count",
)
BILEVEL_CANDIDATE_SOURCE_FILTER_VARIABLE_ROW_FIELDS = (
    "candidate_index",
    "source_catalog",
    "candidate_source",
    "difference_type",
    "variable_name",
)
BILEVEL_CANDIDATE_AUDIT_BUNDLE_ROW_FIELDS = (
    "audit_section",
    "candidate_index",
    "skip_index",
    "candidate_label",
    "candidate_source",
    "component_name",
    "objective_value",
    "best_bound",
    "optimality_gap",
    "selected_binary_count",
    "unselected_binary_count",
    "hamming_distance_to_accepted",
    "matches_accepted",
    "accepted_only_count",
    "candidate_only_count",
    "total_delta_count",
    "selected_variables",
    "reason",
)
BILEVEL_SKIPPED_CANDIDATE_DELTA_SUMMARY_ROW_FIELDS = (
    "skip_index",
    "candidate_label",
    "candidate_source",
    "component_name",
    "accepted_only_count",
    "candidate_only_count",
    "total_delta_count",
    "reason",
)
STYLE_DECOMPOSITION_TRAJECTORY_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_DECOMPOSITION_RUN_ROW_FIELDS,
)
STYLE_DECOMPOSITION_SKIPPED_CANDIDATE_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_SKIPPED_CANDIDATE_ROW_FIELDS,
)
STYLE_CANDIDATE_POOL_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_POOL_ROW_FIELDS,
)
STYLE_CANDIDATE_POOL_COMPARISON_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_POOL_COMPARISON_ROW_FIELDS,
)
STYLE_CANDIDATE_SELECTION_DELTA_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_SELECTION_DELTA_ROW_FIELDS,
)
STYLE_CANDIDATE_SELECTION_DELTA_SUMMARY_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_SELECTION_DELTA_SUMMARY_ROW_FIELDS,
)
STYLE_CANDIDATE_SOURCE_FILTER_SUMMARY_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_SOURCE_FILTER_SUMMARY_ROW_FIELDS,
)
STYLE_CANDIDATE_SOURCE_FILTER_DETAIL_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_SOURCE_FILTER_DETAIL_ROW_FIELDS,
)
STYLE_CANDIDATE_SOURCE_FILTER_VARIABLE_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_SOURCE_FILTER_VARIABLE_ROW_FIELDS,
)
STYLE_CANDIDATE_AUDIT_BUNDLE_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_CANDIDATE_AUDIT_BUNDLE_ROW_FIELDS,
)
STYLE_SKIPPED_CANDIDATE_DELTA_SUMMARY_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    *BILEVEL_SKIPPED_CANDIDATE_DELTA_SUMMARY_ROW_FIELDS,
)
STYLE_DECOMPOSITION_OBJECTIVE_COMPARISON_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "iteration_index",
    "objective_value",
    "benchmark_total_cost",
    "absolute_deviation",
    "within_tolerance",
)
STYLE_FUEL_CONSUMPTION_FAMILY_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "equipment_family",
    "included_in_table_fuel_consumption",
    "fuel_consumption",
    "benchmark_fuel_consumption",
    "table_fuel_consumption",
    "fuel_consumption_residual",
)
STYLE_FUEL_CONSUMPTION_EQUIPMENT_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "equipment_family",
    "equipment_name",
    "fuel_variable",
    "fuel_multiplier",
    "included_in_table_fuel_consumption",
    "fuel_consumption",
    "family_fuel_consumption",
    "share_of_family",
    "benchmark_fuel_consumption",
    "table_fuel_consumption",
    "fuel_consumption_residual",
)
STYLE_FUEL_CONSUMPTION_CAPACITY_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "equipment_family",
    "equipment_name",
    "fuel_variable",
    "fuel_consumption",
    "selection_variable",
    "selected",
    "capacity_basis",
    "actual_capacity_basis_value",
    "capacity_value",
    "capacity_utilization",
    "benchmark_fuel_consumption",
    "table_fuel_consumption",
    "fuel_consumption_residual",
)
STYLE_FUEL_CONSUMPTION_DIAGNOSIS_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "residual_rank",
    "residual_driver",
    "largest_included_equipment_family",
    "largest_included_equipment_name",
    "largest_included_fuel_consumption",
    "largest_included_capacity_utilization",
    "hot_oil_heat_load",
    "auxiliary_vhp_fuel_consumption",
    "benchmark_fuel_consumption",
    "table_fuel_consumption",
    "fuel_consumption_residual",
    "absolute_fuel_consumption_residual",
)
STYLE_FUEL_CALIBRATION_TARGET_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "residual_rank",
    "calibration_action",
    "target_equipment_family",
    "target_equipment_name",
    "capacity_basis",
    "capacity_utilization",
    "current_equipment_fuel_consumption",
    "required_equipment_fuel_consumption",
    "fuel_consumption_adjustment",
    "fuel_consumption_adjustment_factor",
    "benchmark_fuel_consumption",
    "table_fuel_consumption",
    "target_table_fuel_consumption",
    "fuel_consumption_residual",
)
STYLE_OPERATING_COST_COMPONENT_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "operating_cost_component",
    "actual_operating_cost",
    "benchmark_operating_cost",
    "operating_cost_residual",
)
STYLE_OPERATING_COST_TARGET_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "residual_rank",
    "target_operating_cost_component",
    "current_component_operating_cost",
    "required_component_operating_cost",
    "operating_cost_adjustment",
    "operating_cost_adjustment_factor",
    "benchmark_operating_cost",
    "actual_operating_cost",
    "target_operating_cost",
    "operating_cost_residual",
)
STYLE_FUEL_CONSUMPTION_RESIDUAL_RANKING_ROW_FIELDS = (
    "catalog",
    "case_study",
    "scenario",
    "residual_rank",
    "largest_fuel_family",
    "largest_family_fuel_consumption",
    "largest_family_share_of_table",
    "benchmark_fuel_consumption",
    "table_fuel_consumption",
    "fuel_consumption_residual",
    "absolute_fuel_consumption_residual",
    "residual_percent_of_benchmark",
)
CONTRIBUTION2_BILEVEL_BENCHMARK_TRAJECTORY_ROW_FIELDS = (
    "test_number",
    "scenario",
    "iteration_index",
    "objective_value",
    "best_bound",
    "optimality_gap",
    "elapsed_seconds",
    "hit_time_limit",
    "selected_binary_count",
    "unselected_binary_count",
    "subproblem_status",
    "stop_reason",
)
CONTRIBUTION2_BILEVEL_TRAJECTORY_COMPARISON_ROW_FIELDS = (
    "test_number",
    "scenario",
    "iteration_index",
    "field",
    "actual",
    "benchmark",
    "absolute_deviation",
    "within_tolerance",
)
CONTRIBUTION2_BILEVEL_TRAJECTORY_COMPARISON_FIELDS = (
    "objective_value",
    "best_bound",
    "optimality_gap",
    "elapsed_seconds",
    "subproblem_status",
    "stop_reason",
)


def best_configuration_comparison_rows(
    *,
    catalog: str,
    comparison: StaticStyleBestConfigurationComparison,
) -> tuple[dict[str, Any], ...]:
    """Flatten a best-configuration comparison into tabular rows."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": comparison.actual.case_study,
            "scenario": comparison.actual.scenario,
            "field": deviation.field,
            "actual": deviation.actual,
            "benchmark": deviation.benchmark,
            "absolute_deviation": deviation.absolute_deviation,
            "within_tolerance": deviation.within_tolerance,
        }
        for deviation in comparison.deviations
    )


def best_configuration_summary_row(
    *,
    catalog: str,
    comparison: StaticStyleBestConfigurationComparison,
) -> dict[str, Any]:
    """Summarize one best-configuration comparison in one row."""

    failing_fields = tuple(
        deviation.field
        for deviation in comparison.deviations
        if not deviation.within_tolerance
    )
    return {
        "catalog": catalog,
        "case_study": comparison.actual.case_study,
        "scenario": comparison.actual.scenario,
        "within_tolerance": comparison.within_tolerance,
        "max_absolute_deviation": comparison.max_absolute_deviation,
        "failing_fields": ";".join(failing_fields),
    }


def format_comparison_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format comparison rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_comparison_rows_csv(materialized_rows)
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported comparison output format {output_format!r}")


def format_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format comparison summary rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(materialized_rows, SUMMARY_ROW_FIELDS)
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported summary output format {output_format!r}")


def bilevel_decomposition_run_rows(
    run: BilevelDecompositionRun,
) -> tuple[dict[str, Any], ...]:
    """Return flat trajectory rows for a bounded bilevel decomposition run."""

    return tuple(
        _bilevel_decomposition_iteration_row(
            iteration,
            stop_reason=run.stop_reason,
            skipped_candidate_count=run.skipped_candidate_count,
        )
        for iteration in run.iterations
    )


def bilevel_skipped_candidate_rows(
    run: BilevelDecompositionRun,
) -> tuple[dict[str, Any], ...]:
    """Return audit rows for candidates skipped after subproblem failure."""

    return tuple(
        _bilevel_skipped_candidate_row(skip_index, skipped_candidate)
        for skip_index, skipped_candidate in enumerate(
            run.skipped_candidates,
            start=1,
        )
    )


def bilevel_candidate_pool_rows(
    candidates: Iterable[BilevelCandidateAssignment],
) -> tuple[dict[str, Any], ...]:
    """Return audit rows for a candidate assignment pool."""

    return tuple(
        _bilevel_candidate_pool_row(candidate_index, candidate)
        for candidate_index, candidate in enumerate(candidates, start=1)
    )


def bilevel_candidate_pool_comparison_rows(
    candidates: Iterable[BilevelCandidateAssignment],
    *,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Compare candidate assignments with the accepted incumbent assignment."""

    return tuple(
        _bilevel_candidate_pool_comparison_row(
            candidate_index,
            candidate,
            accepted_assignment=accepted_assignment,
        )
        for candidate_index, candidate in enumerate(candidates, start=1)
    )


def bilevel_candidate_selection_delta_rows(
    candidates: Iterable[BilevelCandidateAssignment],
    *,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Return binary-selection deltas from the accepted assignment."""

    rows: list[dict[str, Any]] = []
    for candidate_index, candidate in enumerate(candidates, start=1):
        rows.extend(
            _bilevel_candidate_selection_delta_rows(
                candidate_index,
                candidate,
                accepted_assignment=accepted_assignment,
            ),
        )
    return tuple(rows)


def bilevel_candidate_selection_delta_summary_rows(
    candidates: Iterable[BilevelCandidateAssignment],
    *,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Summarize binary-selection deltas by component family."""

    delta_rows = bilevel_candidate_selection_delta_rows(
        candidates,
        accepted_assignment=accepted_assignment,
    )
    summaries: dict[tuple[int, str, str], dict[str, Any]] = {}
    for row in delta_rows:
        component_name = _binary_selection_component_name(row["variable_name"])
        key = (row["candidate_index"], row["candidate_source"], component_name)
        summary = summaries.setdefault(
            key,
            {
                "candidate_index": row["candidate_index"],
                "candidate_source": row["candidate_source"],
                "component_name": component_name,
                "accepted_only_count": 0,
                "candidate_only_count": 0,
                "total_delta_count": 0,
            },
        )
        if row["delta_type"] == "accepted-only":
            summary["accepted_only_count"] += 1
        elif row["delta_type"] == "candidate-only":
            summary["candidate_only_count"] += 1
        summary["total_delta_count"] += 1
    return tuple(
        summaries[key]
        for key in sorted(
            summaries,
            key=lambda item: (item[0], item[2]),
        )
    )


def bilevel_candidate_source_filter_summary_rows(
    candidates: Iterable[BilevelCandidateAssignment],
    *,
    variable_names: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    """Summarize candidate records filtered by target master variables."""

    candidate_records = tuple(candidates)
    target_variables = tuple(dict.fromkeys(variable_names))
    compatible_candidates = compatible_bilevel_candidate_assignments(
        candidate_records,
        variable_names=target_variables,
    )
    compatible_set = set(compatible_candidates)
    incompatible_candidates = tuple(
        candidate
        for candidate in candidate_records
        if candidate not in compatible_set
    )
    return (
        {
            "source_record_count": len(candidate_records),
            "compatible_candidate_count": len(compatible_candidates),
            "incompatible_candidate_count": len(incompatible_candidates),
            "target_variable_count": len(target_variables),
            "candidate_sources": _candidate_source_labels(candidate_records),
            "compatible_candidate_sources": _candidate_source_labels(
                compatible_candidates,
            ),
            "incompatible_candidate_sources": _candidate_source_labels(
                incompatible_candidates,
            ),
        },
    )


def bilevel_candidate_source_filter_detail_rows(
    candidates: Iterable[BilevelCandidateAssignment],
    *,
    variable_names: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    """Return one source-filter detail row per candidate record."""

    target_variables = set(variable_names)
    if not target_variables:
        raise ValueError("at least one target variable name is required")
    return tuple(
        _bilevel_candidate_source_filter_detail_row(
            candidate_index,
            candidate,
            target_variables=target_variables,
        )
        for candidate_index, candidate in enumerate(candidates, start=1)
    )


def bilevel_candidate_source_filter_variable_rows(
    candidates: Iterable[BilevelCandidateAssignment],
    *,
    variable_names: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    """Return variable-level diagnostics for incompatible candidate sources."""

    target_variables = set(variable_names)
    if not target_variables:
        raise ValueError("at least one target variable name is required")
    rows: list[dict[str, Any]] = []
    for candidate_index, candidate in enumerate(candidates, start=1):
        rows.extend(
            _bilevel_candidate_source_filter_variable_rows(
                candidate_index,
                candidate,
                target_variables=target_variables,
            ),
        )
    return tuple(rows)


def bilevel_skipped_candidate_delta_summary_rows(
    run: BilevelDecompositionRun,
    *,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Join skipped-candidate failures with component-level selection deltas."""

    rows: list[dict[str, Any]] = []
    for skip_index, skipped_candidate in enumerate(run.skipped_candidates, start=1):
        rows.extend(
            _bilevel_skipped_candidate_delta_summary_rows(
                skip_index=skip_index,
                skipped_candidate=skipped_candidate,
                accepted_assignment=accepted_assignment,
            ),
        )
    return tuple(rows)


def bilevel_candidate_audit_bundle_rows(
    candidates: Iterable[BilevelCandidateAssignment],
    *,
    run: BilevelDecompositionRun,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Return a single audit table for candidate pool and skipped diagnostics."""

    candidate_records = tuple(candidates)
    rows: list[dict[str, Any]] = [
        _bilevel_candidate_audit_accepted_incumbent_row(
            run,
            accepted_assignment=accepted_assignment,
        ),
    ]
    rows.extend(
        _bilevel_candidate_audit_pool_row(
            candidate_index,
            candidate,
            accepted_assignment=accepted_assignment,
        )
        for candidate_index, candidate in enumerate(candidate_records, start=1)
    )
    rows.extend(
        _bilevel_candidate_audit_delta_summary_row(row)
        for row in bilevel_candidate_selection_delta_summary_rows(
            candidate_records,
            accepted_assignment=accepted_assignment,
        )
    )
    rows.extend(
        _bilevel_candidate_audit_skipped_row(row)
        for row in bilevel_skipped_candidate_rows(run)
    )
    rows.extend(
        _bilevel_candidate_audit_skipped_delta_summary_row(row)
        for row in bilevel_skipped_candidate_delta_summary_rows(
            run,
            accepted_assignment=accepted_assignment,
        )
    )
    return tuple(rows)


def format_bilevel_decomposition_run_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format bilevel decomposition trajectory rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_DECOMPOSITION_RUN_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported bilevel-run output format {output_format!r}")


def format_bilevel_candidate_pool_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate-pool audit rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_POOL_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported candidate-pool output format {output_format!r}")


def format_bilevel_candidate_pool_comparison_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate-pool comparison rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_POOL_COMPARISON_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported candidate-pool comparison output format {output_format!r}"
    )


def format_bilevel_candidate_selection_delta_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate-selection delta rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_SELECTION_DELTA_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported candidate-selection delta output format {output_format!r}"
    )


def format_bilevel_candidate_selection_delta_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate-selection delta summary rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_SELECTION_DELTA_SUMMARY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported candidate-selection summary output format {output_format!r}"
    )


def format_bilevel_candidate_source_filter_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate source-filter summary rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_SOURCE_FILTER_SUMMARY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported candidate source-filter summary output format "
        f"{output_format!r}"
    )


def format_bilevel_candidate_source_filter_detail_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate source-filter detail rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_SOURCE_FILTER_DETAIL_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported candidate source-filter detail output format "
        f"{output_format!r}"
    )


def format_bilevel_candidate_source_filter_variable_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate source-filter variable rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_SOURCE_FILTER_VARIABLE_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported candidate source-filter variable output format "
        f"{output_format!r}"
    )


def format_bilevel_candidate_audit_bundle_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format candidate audit-bundle rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_CANDIDATE_AUDIT_BUNDLE_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported candidate audit-bundle output format {output_format!r}"
    )


def format_bilevel_skipped_candidate_delta_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format skipped-candidate delta summary rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_SKIPPED_CANDIDATE_DELTA_SUMMARY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported skipped-candidate delta summary output format "
        f"{output_format!r}"
    )


def format_bilevel_skipped_candidate_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format skipped-candidate audit rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            BILEVEL_SKIPPED_CANDIDATE_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported skipped-candidate output format {output_format!r}")


def style_decomposition_trajectory_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    run: BilevelDecompositionRun,
) -> tuple[dict[str, Any], ...]:
    """Return decomposition trajectory rows with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_decomposition_run_rows(run)
    )


def format_style_decomposition_trajectory_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE decomposition trajectory rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_DECOMPOSITION_TRAJECTORY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE decomposition trajectory output format {output_format!r}"
    )


def style_decomposition_skipped_candidate_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    run: BilevelDecompositionRun,
) -> tuple[dict[str, Any], ...]:
    """Return skipped-candidate audit rows with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_skipped_candidate_rows(run)
    )


def style_candidate_pool_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
) -> tuple[dict[str, Any], ...]:
    """Return candidate-pool rows with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_pool_rows(candidates)
    )


def style_candidate_pool_comparison_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Return candidate-pool comparison rows with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_pool_comparison_rows(
            candidates,
            accepted_assignment=accepted_assignment,
        )
    )


def style_candidate_selection_delta_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Return candidate-selection delta rows with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_selection_delta_rows(
            candidates,
            accepted_assignment=accepted_assignment,
        )
    )


def style_candidate_selection_delta_summary_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Return grouped candidate-selection deltas with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_selection_delta_summary_rows(
            candidates,
            accepted_assignment=accepted_assignment,
        )
    )


def style_candidate_source_filter_summary_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
    variable_names: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    """Return candidate source-filter summary rows with STYLE metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_source_filter_summary_rows(
            candidates,
            variable_names=variable_names,
        )
    )


def style_candidate_source_filter_detail_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
    variable_names: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    """Return candidate source-filter detail rows with STYLE metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_source_filter_detail_rows(
            candidates,
            variable_names=variable_names,
        )
    )


def style_candidate_source_filter_variable_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
    variable_names: Iterable[str],
) -> tuple[dict[str, Any], ...]:
    """Return candidate source-filter variable rows with STYLE metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_source_filter_variable_rows(
            candidates,
            variable_names=variable_names,
        )
    )


def style_skipped_candidate_delta_summary_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    run: BilevelDecompositionRun,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Return skipped-candidate delta summaries with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_skipped_candidate_delta_summary_rows(
            run,
            accepted_assignment=accepted_assignment,
        )
    )


def style_candidate_audit_bundle_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    candidates: Iterable[BilevelCandidateAssignment],
    run: BilevelDecompositionRun,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    """Return candidate audit-bundle rows with STYLE scenario metadata."""

    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            **row,
        }
        for row in bilevel_candidate_audit_bundle_rows(
            candidates,
            run=run,
            accepted_assignment=accepted_assignment,
        )
    )


def format_style_candidate_audit_bundle_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate audit-bundle rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_CANDIDATE_AUDIT_BUNDLE_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE candidate audit-bundle output format {output_format!r}"
    )


def format_style_skipped_candidate_delta_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE skipped-candidate delta summary rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_SKIPPED_CANDIDATE_DELTA_SUMMARY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE skipped-candidate delta summary output format "
        f"{output_format!r}"
    )


def format_style_candidate_source_filter_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate source-filter summary rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_CANDIDATE_SOURCE_FILTER_SUMMARY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE candidate source-filter summary output format "
        f"{output_format!r}"
    )


def format_style_candidate_source_filter_detail_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate source-filter detail rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_CANDIDATE_SOURCE_FILTER_DETAIL_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE candidate source-filter detail output format "
        f"{output_format!r}"
    )


def format_style_candidate_source_filter_variable_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate source-filter variable rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_CANDIDATE_SOURCE_FILTER_VARIABLE_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE candidate source-filter variable output format "
        f"{output_format!r}"
    )


def format_style_candidate_selection_delta_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate-selection delta summary rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_CANDIDATE_SELECTION_DELTA_SUMMARY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE candidate-selection summary output format "
        f"{output_format!r}"
    )


def format_style_candidate_selection_delta_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate-selection delta rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_CANDIDATE_SELECTION_DELTA_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE candidate-selection delta output format "
        f"{output_format!r}"
    )


def format_style_candidate_pool_comparison_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate-pool comparison rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_CANDIDATE_POOL_COMPARISON_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE candidate-pool comparison output format {output_format!r}"
    )


def format_style_candidate_pool_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE candidate-pool rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(materialized_rows, STYLE_CANDIDATE_POOL_ROW_FIELDS)
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported STYLE candidate-pool output format {output_format!r}")


def format_style_decomposition_skipped_candidate_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE skipped-candidate audit rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_DECOMPOSITION_SKIPPED_CANDIDATE_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE skipped-candidate output format {output_format!r}"
    )


def style_decomposition_objective_comparison_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    run: BilevelDecompositionRun,
    benchmark: Contribution2BestConfiguration,
    absolute_tolerance: float | None = None,
) -> tuple[dict[str, Any], ...]:
    """Compare decomposition objective values with Table 2-9 total costs."""

    tolerance = (
        scenario.absolute_tolerance
        if absolute_tolerance is None
        else absolute_tolerance
    )
    if tolerance < 0.0:
        raise ValueError("absolute_tolerance must be non-negative")
    return tuple(
        _style_decomposition_objective_comparison_row(
            catalog=catalog,
            scenario=scenario,
            iteration_index=row["iteration_index"],
            objective_value=row["objective_value"],
            benchmark_total_cost=benchmark.total_cost,
            absolute_tolerance=tolerance,
        )
        for row in bilevel_decomposition_run_rows(run)
    )


def format_style_decomposition_objective_comparison_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE decomposition objective comparison rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_DECOMPOSITION_OBJECTIVE_COMPARISON_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        "unsupported STYLE decomposition objective comparison output format "
        f"{output_format!r}"
    )


def style_fuel_consumption_family_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    model: Any,
    benchmark: Contribution2BestConfiguration,
) -> tuple[dict[str, Any], ...]:
    """Return fuel-family rows compared with a Table 2-9 fuel benchmark."""

    family_rows = static_style_fuel_consumption_by_family(model)
    table_fuel_consumption = next(
        row.fuel_consumption
        for row in family_rows
        if row.equipment_family == "table_total"
    )
    residual = table_fuel_consumption - benchmark.fuel_consumption
    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            "equipment_family": row.equipment_family,
            "included_in_table_fuel_consumption": (
                row.included_in_table_fuel_consumption
            ),
            "fuel_consumption": row.fuel_consumption,
            "benchmark_fuel_consumption": benchmark.fuel_consumption,
            "table_fuel_consumption": table_fuel_consumption,
            "fuel_consumption_residual": residual,
        }
        for row in family_rows
    )


def format_style_fuel_consumption_family_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE fuel-family residual rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_FUEL_CONSUMPTION_FAMILY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE fuel-family output format {output_format!r}"
    )


def style_fuel_consumption_equipment_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    model: Any,
    benchmark: Contribution2BestConfiguration,
) -> tuple[dict[str, Any], ...]:
    """Return equipment-level fuel-consumption residual trace rows."""

    family_rows = static_style_fuel_consumption_by_family(model)
    family_fuel_consumption = {
        row.equipment_family: row.fuel_consumption for row in family_rows
    }
    table_fuel_consumption = family_fuel_consumption["table_total"]
    residual = table_fuel_consumption - benchmark.fuel_consumption
    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            "equipment_family": row.equipment_family,
            "equipment_name": row.equipment_name,
            "fuel_variable": row.fuel_variable,
            "fuel_multiplier": row.fuel_multiplier,
            "included_in_table_fuel_consumption": (
                row.included_in_table_fuel_consumption
            ),
            "fuel_consumption": row.fuel_consumption,
            "family_fuel_consumption": family_fuel_consumption[row.equipment_family],
            "share_of_family": _safe_divide(
                row.fuel_consumption,
                family_fuel_consumption[row.equipment_family],
            ),
            "benchmark_fuel_consumption": benchmark.fuel_consumption,
            "table_fuel_consumption": table_fuel_consumption,
            "fuel_consumption_residual": residual,
        }
        for row in static_style_fuel_consumption_by_equipment(model)
    )


def format_style_fuel_consumption_equipment_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE equipment-level fuel residual rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_FUEL_CONSUMPTION_EQUIPMENT_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE fuel-equipment output format {output_format!r}"
    )


def style_fuel_consumption_capacity_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    model: Any,
    benchmark: Contribution2BestConfiguration,
) -> tuple[dict[str, Any], ...]:
    """Return equipment fuel-consumption rows with capacity context."""

    equipment_rows = style_fuel_consumption_equipment_rows(
        catalog=catalog,
        scenario=scenario,
        model=model,
        benchmark=benchmark,
    )
    capacity_context = {
        (row.equipment_family, row.equipment_name): row
        for row in static_style_fuel_capacity_context_by_equipment(model)
    }
    rows: list[dict[str, Any]] = []
    for row in equipment_rows:
        context = capacity_context.get((row["equipment_family"], row["equipment_name"]))
        if context is None:
            continue
        rows.append(_style_fuel_consumption_capacity_row(row, context))
    return tuple(rows)


def format_style_fuel_consumption_capacity_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE fuel-capacity context rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_FUEL_CONSUMPTION_CAPACITY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE fuel-capacity output format {output_format!r}"
    )


def style_fuel_consumption_diagnosis_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Classify scenario-level physical-profile fuel residual drivers."""

    grouped_rows: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["catalog"], row["case_study"], row["scenario"])
        grouped_rows.setdefault(key, []).append(row)

    diagnosis_rows = [
        _style_fuel_consumption_diagnosis_row(group_rows)
        for group_rows in grouped_rows.values()
    ]
    return tuple(
        {
            **row,
            "residual_rank": rank,
        }
        for rank, row in enumerate(
            sorted(
                diagnosis_rows,
                key=lambda row: (
                    -row["absolute_fuel_consumption_residual"],
                    row["scenario"],
                ),
            ),
            start=1,
        )
    )


def format_style_fuel_consumption_diagnosis_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE fuel residual diagnosis rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_FUEL_CONSUMPTION_DIAGNOSIS_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE fuel-diagnosis output format {output_format!r}"
    )


def style_fuel_calibration_target_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Return fuel-consumption targets needed to close residuals."""

    grouped_rows: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["catalog"], row["case_study"], row["scenario"])
        grouped_rows.setdefault(key, []).append(row)

    target_rows = [
        _style_fuel_calibration_target_row(group_rows)
        for group_rows in grouped_rows.values()
    ]
    return tuple(
        {
            **row,
            "residual_rank": rank,
        }
        for rank, row in enumerate(
            sorted(
                target_rows,
                key=lambda row: (
                    -abs(row["fuel_consumption_residual"]),
                    row["scenario"],
                ),
            ),
            start=1,
        )
    )


def format_style_fuel_calibration_target_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE fuel calibration target rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_FUEL_CALIBRATION_TARGET_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE fuel-target output format {output_format!r}"
    )


def style_fuel_consumption_factor_map_from_calibration_target_rows(
    rows: Iterable[dict[str, Any]],
) -> dict[str, dict[tuple[str, str], float]]:
    """Return scenario fuel-accounting factors from target rows."""

    factor_map: dict[str, dict[tuple[str, str], float]] = {}
    for row in rows:
        factor = row["fuel_consumption_adjustment_factor"]
        if factor is None or row["calibration_action"] == "within_tolerance":
            continue
        if row["calibration_action"] == "no_capped_capacity_target":
            continue
        factor_map.setdefault(row["scenario"], {})[
            (row["target_equipment_family"], row["target_equipment_name"])
        ] = factor
    return factor_map


def style_operating_cost_component_rows(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    model: Any,
    benchmark: Contribution2BestConfiguration,
) -> tuple[dict[str, Any], ...]:
    """Return operating-cost component comparisons against a benchmark row."""

    benchmark_components = _benchmark_operating_cost_components(benchmark)
    return tuple(
        {
            "catalog": catalog,
            "case_study": scenario.case_study,
            "scenario": scenario.scenario,
            "operating_cost_component": row.component,
            "actual_operating_cost": row.operating_cost,
            "benchmark_operating_cost": benchmark_components[row.component],
            "operating_cost_residual": (
                row.operating_cost - benchmark_components[row.component]
            ),
        }
        for row in static_style_operating_cost_components(model)
    )


def format_style_operating_cost_component_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE operating-cost component rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_OPERATING_COST_COMPONENT_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE operating-components output format {output_format!r}"
    )


def style_operating_cost_target_rows(
    rows: Iterable[dict[str, Any]],
    *,
    absolute_tolerance: float = 1e-9,
) -> tuple[dict[str, Any], ...]:
    """Return component adjustments that close total operating-cost residuals."""

    grouped_rows: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["catalog"], row["case_study"], row["scenario"])
        grouped_rows.setdefault(key, []).append(row)

    target_rows: list[dict[str, Any]] = []
    for key, scenario_rows in grouped_rows.items():
        total_row = _operating_cost_total_row(scenario_rows)
        if total_row is None:
            continue
        residual = total_row["operating_cost_residual"]
        if abs(residual) <= absolute_tolerance:
            continue
        target_component = _largest_operating_cost_component_residual(scenario_rows)
        if target_component is None:
            continue

        current_component_cost = target_component["actual_operating_cost"]
        adjustment = -residual
        required_component_cost = current_component_cost + adjustment
        target_rows.append(
            {
                "catalog": key[0],
                "case_study": key[1],
                "scenario": key[2],
                "residual_rank": 0,
                "target_operating_cost_component": target_component[
                    "operating_cost_component"
                ],
                "current_component_operating_cost": current_component_cost,
                "required_component_operating_cost": required_component_cost,
                "operating_cost_adjustment": adjustment,
                "operating_cost_adjustment_factor": _safe_divide(
                    required_component_cost,
                    current_component_cost,
                ),
                "benchmark_operating_cost": total_row["benchmark_operating_cost"],
                "actual_operating_cost": total_row["actual_operating_cost"],
                "target_operating_cost": total_row["benchmark_operating_cost"],
                "operating_cost_residual": residual,
            },
        )

    sorted_rows = sorted(
        target_rows,
        key=lambda row: (
            -abs(row["operating_cost_residual"]),
            row["catalog"],
            row["case_study"],
            row["scenario"],
        ),
    )
    return tuple(
        {
            **row,
            "residual_rank": index,
        }
        for index, row in enumerate(sorted_rows, start=1)
    )


def format_style_operating_cost_target_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE operating-cost target rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_OPERATING_COST_TARGET_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE operating-targets output format {output_format!r}"
    )


def style_operating_cost_adjustment_map_from_target_rows(
    rows: Iterable[dict[str, Any]],
) -> dict[str, dict[str, float]]:
    """Return scenario operating-cost adjustment maps from target rows."""

    adjustment_map: dict[str, dict[str, float]] = {}
    for row in rows:
        adjustment = row["operating_cost_adjustment"]
        if adjustment is None or abs(adjustment) <= 1e-9:
            continue
        adjustment_map.setdefault(row["scenario"], {})[
            row["target_operating_cost_component"]
        ] = adjustment
    return adjustment_map


def style_fuel_consumption_residual_ranking_rows(
    rows: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Rank scenarios by absolute fuel-consumption residual."""

    grouped_rows: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["catalog"], row["case_study"], row["scenario"])
        grouped_rows.setdefault(key, []).append(row)

    ranking_rows = [
        _style_fuel_consumption_residual_ranking_row(group_rows)
        for group_rows in grouped_rows.values()
    ]
    return tuple(
        {
            **row,
            "residual_rank": rank,
        }
        for rank, row in enumerate(
            sorted(
                ranking_rows,
                key=lambda row: (
                    -row["absolute_fuel_consumption_residual"],
                    row["scenario"],
                ),
            ),
            start=1,
        )
    )


def format_style_fuel_consumption_residual_ranking_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format STYLE fuel-residual ranking rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            STYLE_FUEL_CONSUMPTION_RESIDUAL_RANKING_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported STYLE fuel-residual ranking output format {output_format!r}"
    )


def steam_property_comparison_rows(
    comparisons: Iterable[Contribution2SteamPropertyComparison] = (
        CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS
    ),
) -> tuple[dict[str, Any], ...]:
    """Return Contribution 2 steam-property comparison rows."""

    return tuple(_steam_property_comparison_row(comparison) for comparison in comparisons)


def model_derived_steam_property_comparison_rows(
    comparisons: Iterable[Contribution2SteamPropertyComparison] = (
        CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS
    ),
    *,
    properties: SteamPropertyProvider | None = None,
) -> tuple[dict[str, Any], ...]:
    """Recompute IAPWS-side steam-property comparison rows from conditions."""

    provider = CoolPropSteamPropertyProvider() if properties is None else properties
    rows: list[dict[str, Any]] = []
    iapws_power_by_configuration: dict[str, float] = {}
    for comparison in comparisons:
        if comparison.turbine == "total":
            iapws_power = iapws_power_by_configuration.get(
                comparison.configuration,
                comparison.iapws_power_generation,
            )
            rows.append(
                _steam_property_comparison_row_from_values(
                    comparison,
                    real_isentropic_enthalpy_change=None,
                    iapws_power_generation=iapws_power,
                ),
            )
            continue
        real_enthalpy_change = provider.isentropic_enthalpy_change(
            inlet_pressure=_required_property_value(
                comparison.inlet_pressure,
                "inlet_pressure",
            ),
            outlet_pressure=_required_property_value(
                comparison.outlet_pressure,
                "outlet_pressure",
            ),
            inlet_temperature=_required_property_value(
                comparison.inlet_temperature,
                "inlet_temperature",
            ),
        )
        turbine_flow = _model_turbine_flow(comparison)
        iapws_power = turbine_flow * real_enthalpy_change
        iapws_power_by_configuration[comparison.configuration] = (
            iapws_power_by_configuration.get(comparison.configuration, 0.0)
            + iapws_power
        )
        rows.append(
            _steam_property_comparison_row_from_values(
                comparison,
                real_isentropic_enthalpy_change=real_enthalpy_change,
                iapws_power_generation=iapws_power,
            ),
        )
    return tuple(rows)


def contribution2_model_statistic_rows(
    statistics: Iterable[Contribution2ModelStatistic] = (
        CONTRIBUTION2_MODEL_STATISTICS
    ),
) -> tuple[dict[str, Any], ...]:
    """Return Contribution 2 model-statistics rows."""

    return tuple(
        {
            "test_number": statistic.test_number,
            "reference": statistic.reference,
            "steam_mains": statistic.steam_mains,
            "power_demand": statistic.power_demand,
            "integrates_hot_oil_and_fsr": statistic.integrates_hot_oil_and_fsr,
            "variable_count": statistic.variable_count,
            "binary_count": statistic.binary_count,
            "equation_count": statistic.equation_count,
        }
        for statistic in statistics
    )


def contribution2_computational_result_rows(
    results: Iterable[Contribution2ComputationalResult] = (
        CONTRIBUTION2_COMPUTATIONAL_RESULTS
    ),
) -> tuple[dict[str, Any], ...]:
    """Return Contribution 2 computational-result rows."""

    return tuple(
        {
            "test_number": result.test_number,
            "scenario": result.scenario,
            "method": result.method,
            "best_solution_found": result.best_solution_found,
            "best_possible": result.best_possible,
            "optimality_gap": _optional_difference(
                result.best_solution_found,
                result.best_possible,
            ),
            "computational_time_seconds": result.computational_time_seconds,
            "hit_time_limit": result.hit_time_limit,
        }
        for result in results
    )


def contribution2_computational_best_method_rows(
    results: Iterable[Contribution2ComputationalResult] = (
        CONTRIBUTION2_COMPUTATIONAL_RESULTS
    ),
) -> tuple[dict[str, Any], ...]:
    """Return the best reported method for each Contribution 2 test scenario."""

    grouped_results = _computational_results_by_test_scenario(results)
    return tuple(
        _computational_best_method_row(
            min(group, key=lambda result: result.best_solution_found)
        )
        for _, group in grouped_results
    )


def contribution2_computational_method_summary_rows(
    results: Iterable[Contribution2ComputationalResult] = (
        CONTRIBUTION2_COMPUTATIONAL_RESULTS
    ),
) -> tuple[dict[str, Any], ...]:
    """Return method-level Contribution 2 computational-result summaries."""

    result_tuple = tuple(results)
    best_method_keys = {
        (
            row["test_number"],
            row["scenario"],
            row["best_method"],
        )
        for row in contribution2_computational_best_method_rows(result_tuple)
    }
    methods = tuple(dict.fromkeys(result.method for result in result_tuple))
    return tuple(
        _computational_method_summary_row(
            method,
            tuple(result for result in result_tuple if result.method == method),
            best_method_keys,
        )
        for method in methods
    )


def contribution2_bilevel_benchmark_trajectory_rows(
    results: Iterable[Contribution2ComputationalResult] = (
        CONTRIBUTION2_COMPUTATIONAL_RESULTS
    ),
    *,
    method: str = "bilevel",
) -> tuple[dict[str, Any], ...]:
    """Map captured Contribution 2 bilevel rows onto trajectory-style rows."""

    return tuple(
        _contribution2_bilevel_benchmark_trajectory_row(result)
        for result in results
        if result.method == method
    )


def contribution2_bilevel_trajectory_comparison_rows(
    *,
    test_number: int,
    scenario: int,
    actual_rows: Iterable[dict[str, Any]],
    benchmark_rows: Iterable[dict[str, Any]] | None = None,
    fields: Sequence[str] = CONTRIBUTION2_BILEVEL_TRAJECTORY_COMPARISON_FIELDS,
    absolute_tolerance: float = 1e-6,
) -> tuple[dict[str, Any], ...]:
    """Compare generated bilevel trajectory rows with Contribution 2 fixtures."""

    if absolute_tolerance < 0.0:
        raise ValueError("absolute_tolerance must be non-negative")
    selected_benchmark_rows = _contribution2_bilevel_benchmark_rows_by_iteration(
        test_number=test_number,
        scenario=scenario,
        benchmark_rows=(
            contribution2_bilevel_benchmark_trajectory_rows()
            if benchmark_rows is None
            else benchmark_rows
        ),
    )
    rows: list[dict[str, Any]] = []
    for actual_row in actual_rows:
        iteration_index = actual_row["iteration_index"]
        try:
            benchmark_row = selected_benchmark_rows[iteration_index]
        except KeyError:
            raise KeyError(
                "No Contribution 2 bilevel benchmark trajectory row for "
                f"test {test_number}, scenario {scenario}, iteration "
                f"{iteration_index}"
            ) from None
        for field in fields:
            rows.append(
                _contribution2_bilevel_trajectory_comparison_row(
                    test_number=test_number,
                    scenario=scenario,
                    iteration_index=iteration_index,
                    field=field,
                    actual=actual_row.get(field),
                    benchmark=benchmark_row.get(field),
                    absolute_tolerance=absolute_tolerance,
                ),
            )
    return tuple(rows)


def format_steam_property_comparison_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format steam-property comparison rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(materialized_rows, STEAM_PROPERTY_ROW_FIELDS)
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported steam-property output format {output_format!r}")


def format_contribution2_model_statistic_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format Contribution 2 model-statistics rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(materialized_rows, MODEL_STATISTIC_ROW_FIELDS)
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported model-statistics output format {output_format!r}")


def format_contribution2_computational_result_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format Contribution 2 computational-result rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(materialized_rows, COMPUTATIONAL_RESULT_ROW_FIELDS)
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported computational-results output format {output_format!r}"
    )


def format_contribution2_computational_best_method_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format Contribution 2 best-method summary rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            COMPUTATIONAL_BEST_METHOD_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported best-method output format {output_format!r}")


def format_contribution2_computational_method_summary_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format Contribution 2 method summary rows as CSV or JSON text."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            COMPUTATIONAL_METHOD_SUMMARY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(f"unsupported method-summary output format {output_format!r}")


def format_contribution2_bilevel_benchmark_trajectory_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format Contribution 2 bilevel benchmark trajectory rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            CONTRIBUTION2_BILEVEL_BENCHMARK_TRAJECTORY_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported bilevel benchmark trajectory output format {output_format!r}"
    )


def format_contribution2_bilevel_trajectory_comparison_rows(
    rows: Iterable[dict[str, Any]],
    *,
    output_format: str,
) -> str:
    """Format Contribution 2 bilevel trajectory comparison rows."""

    materialized_rows = tuple(rows)
    if output_format == "csv":
        return _format_rows_csv(
            materialized_rows,
            CONTRIBUTION2_BILEVEL_TRAJECTORY_COMPARISON_ROW_FIELDS,
        )
    if output_format == "json":
        return json.dumps(materialized_rows, indent=2)
    raise ValueError(
        f"unsupported bilevel trajectory comparison output format {output_format!r}"
    )


def _computational_results_by_test_scenario(
    results: Iterable[Contribution2ComputationalResult],
) -> tuple[tuple[tuple[int, int], tuple[Contribution2ComputationalResult, ...]], ...]:
    result_tuple = tuple(results)
    keys = tuple(
        dict.fromkeys((result.test_number, result.scenario) for result in result_tuple)
    )
    return tuple(
        (
            key,
            tuple(
                result
                for result in result_tuple
                if (result.test_number, result.scenario) == key
            ),
        )
        for key in keys
    )


def _computational_best_method_row(
    result: Contribution2ComputationalResult,
) -> dict[str, Any]:
    return {
        "test_number": result.test_number,
        "scenario": result.scenario,
        "best_method": result.method,
        "best_solution_found": result.best_solution_found,
        "best_possible": result.best_possible,
        "optimality_gap": _optional_difference(
            result.best_solution_found,
            result.best_possible,
        ),
        "computational_time_seconds": result.computational_time_seconds,
        "hit_time_limit": result.hit_time_limit,
    }


def _computational_method_summary_row(
    method: str,
    results: tuple[Contribution2ComputationalResult, ...],
    best_method_keys: set[tuple[int, int, str]],
) -> dict[str, Any]:
    if not results:
        raise ValueError("method summary requires at least one result")
    return {
        "method": method,
        "result_count": len(results),
        "best_solution_count": sum(
            (result.test_number, result.scenario, result.method) in best_method_keys
            for result in results
        ),
        "time_limit_count": sum(result.hit_time_limit for result in results),
        "mean_computational_time_seconds": sum(
            result.computational_time_seconds for result in results
        )
        / len(results),
    }


def _bilevel_decomposition_iteration_row(
    iteration: BilevelDecompositionIteration,
    *,
    stop_reason: str,
    skipped_candidate_count: int,
) -> dict[str, Any]:
    return {
        "iteration_index": iteration.iteration_index,
        "candidate_source": iteration.candidate_source_label or "",
        "objective_value": iteration.incumbent.objective_value,
        "best_bound": iteration.incumbent.best_bound,
        "optimality_gap": iteration.incumbent.optimality_gap,
        "elapsed_seconds": iteration.incumbent.elapsed_seconds,
        "hit_time_limit": iteration.incumbent.hit_time_limit,
        "selected_binary_count": len(iteration.assignment.selected_variables),
        "unselected_binary_count": len(iteration.assignment.unselected_variables),
        "subproblem_status": iteration.subproblem.status,
        "stop_reason": stop_reason,
        "skipped_candidate_count": skipped_candidate_count,
    }


def _bilevel_skipped_candidate_row(
    skip_index: int,
    skipped_candidate: Any,
) -> dict[str, Any]:
    assignment = skipped_candidate.assignment
    return {
        "skip_index": skip_index,
        "candidate_label": skipped_candidate.candidate_label,
        "candidate_source": skipped_candidate.source_label or "",
        "selected_binary_count": len(assignment.selected_variables),
        "unselected_binary_count": len(assignment.unselected_variables),
        "selected_variables": ";".join(assignment.selected_variables),
        "reason": skipped_candidate.reason,
    }


def _bilevel_candidate_pool_row(
    candidate_index: int,
    candidate: BilevelCandidateAssignment,
) -> dict[str, Any]:
    assignment = candidate.assignment
    return {
        "candidate_index": candidate_index,
        "candidate_source": candidate.source_label or "",
        "selected_binary_count": len(assignment.selected_variables),
        "unselected_binary_count": len(assignment.unselected_variables),
        "selected_variables": ";".join(assignment.selected_variables),
    }


def _bilevel_candidate_pool_comparison_row(
    candidate_index: int,
    candidate: BilevelCandidateAssignment,
    *,
    accepted_assignment: Any,
) -> dict[str, Any]:
    assignment = candidate.assignment
    hamming_distance = assignment.hamming_distance(accepted_assignment)
    return {
        "candidate_index": candidate_index,
        "candidate_source": candidate.source_label or "",
        "hamming_distance_to_accepted": hamming_distance,
        "matches_accepted": hamming_distance == 0,
        "selected_binary_count": len(assignment.selected_variables),
        "unselected_binary_count": len(assignment.unselected_variables),
    }


def _bilevel_candidate_selection_delta_rows(
    candidate_index: int,
    candidate: BilevelCandidateAssignment,
    *,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    accepted_values = accepted_assignment.as_dict()
    candidate_values = candidate.assignment.as_dict()
    if accepted_values.keys() != candidate_values.keys():
        raise ValueError("candidate and accepted assignments must contain same variables")
    return tuple(
        _bilevel_candidate_selection_delta_row(
            candidate_index=candidate_index,
            candidate=candidate,
            variable_name=variable_name,
            accepted_value=accepted_values[variable_name],
            candidate_value=candidate_values[variable_name],
        )
        for variable_name in sorted(accepted_values)
        if accepted_values[variable_name] != candidate_values[variable_name]
    )


def _bilevel_candidate_selection_delta_row(
    *,
    candidate_index: int,
    candidate: BilevelCandidateAssignment,
    variable_name: str,
    accepted_value: int,
    candidate_value: int,
) -> dict[str, Any]:
    return {
        "candidate_index": candidate_index,
        "candidate_source": candidate.source_label or "",
        "variable_name": variable_name,
        "accepted_value": accepted_value,
        "candidate_value": candidate_value,
        "delta_type": _binary_selection_delta_type(
            accepted_value=accepted_value,
            candidate_value=candidate_value,
        ),
    }


def _bilevel_skipped_candidate_delta_summary_rows(
    *,
    skip_index: int,
    skipped_candidate: Any,
    accepted_assignment: Any,
) -> tuple[dict[str, Any], ...]:
    candidate = BilevelCandidateAssignment(
        assignment=skipped_candidate.assignment,
        source_label=skipped_candidate.source_label,
    )
    return tuple(
        {
            "skip_index": skip_index,
            "candidate_label": skipped_candidate.candidate_label,
            "candidate_source": row["candidate_source"],
            "component_name": row["component_name"],
            "accepted_only_count": row["accepted_only_count"],
            "candidate_only_count": row["candidate_only_count"],
            "total_delta_count": row["total_delta_count"],
            "reason": skipped_candidate.reason,
        }
        for row in bilevel_candidate_selection_delta_summary_rows(
            (candidate,),
            accepted_assignment=accepted_assignment,
        )
    )


def _bilevel_candidate_audit_base_row(audit_section: str) -> dict[str, Any]:
    row = dict.fromkeys(BILEVEL_CANDIDATE_AUDIT_BUNDLE_ROW_FIELDS, "")
    row["audit_section"] = audit_section
    return row


def _bilevel_candidate_audit_accepted_incumbent_row(
    run: BilevelDecompositionRun,
    *,
    accepted_assignment: Any,
) -> dict[str, Any]:
    incumbent = run.best_incumbent()
    row = _bilevel_candidate_audit_base_row("accepted-incumbent")
    row.update(
        {
            "candidate_label": incumbent.label,
            "objective_value": incumbent.objective_value,
            "best_bound": incumbent.best_bound,
            "optimality_gap": incumbent.optimality_gap,
            "selected_binary_count": len(accepted_assignment.selected_variables),
            "unselected_binary_count": len(accepted_assignment.unselected_variables),
            "hamming_distance_to_accepted": 0,
            "matches_accepted": True,
            "selected_variables": ";".join(accepted_assignment.selected_variables),
            "reason": run.stop_reason,
        },
    )
    return row


def _bilevel_candidate_audit_pool_row(
    candidate_index: int,
    candidate: BilevelCandidateAssignment,
    *,
    accepted_assignment: Any,
) -> dict[str, Any]:
    pool_row = _bilevel_candidate_pool_row(candidate_index, candidate)
    comparison_row = _bilevel_candidate_pool_comparison_row(
        candidate_index,
        candidate,
        accepted_assignment=accepted_assignment,
    )
    row = _bilevel_candidate_audit_base_row("candidate-pool")
    row.update(
        {
            "candidate_index": candidate_index,
            "candidate_source": pool_row["candidate_source"],
            "selected_binary_count": pool_row["selected_binary_count"],
            "unselected_binary_count": pool_row["unselected_binary_count"],
            "hamming_distance_to_accepted": comparison_row[
                "hamming_distance_to_accepted"
            ],
            "matches_accepted": comparison_row["matches_accepted"],
            "selected_variables": pool_row["selected_variables"],
        },
    )
    return row


def _bilevel_candidate_source_filter_detail_row(
    candidate_index: int,
    candidate: BilevelCandidateAssignment,
    *,
    target_variables: set[str],
) -> dict[str, Any]:
    candidate_variables = set(candidate.assignment.as_dict())
    source_catalog, candidate_source = _split_qualified_candidate_source(
        candidate.source_label or "",
    )
    return {
        "candidate_index": candidate_index,
        "source_catalog": source_catalog,
        "candidate_source": candidate_source,
        "target_variable_count": len(target_variables),
        "candidate_variable_count": len(candidate_variables),
        "selected_binary_count": len(candidate.assignment.selected_variables),
        "unselected_binary_count": len(candidate.assignment.unselected_variables),
        "compatible_with_target": candidate_variables == target_variables,
        "missing_target_variable_count": len(target_variables - candidate_variables),
        "extra_candidate_variable_count": len(candidate_variables - target_variables),
    }


def _bilevel_candidate_source_filter_variable_rows(
    candidate_index: int,
    candidate: BilevelCandidateAssignment,
    *,
    target_variables: set[str],
) -> tuple[dict[str, Any], ...]:
    candidate_variables = set(candidate.assignment.as_dict())
    source_catalog, candidate_source = _split_qualified_candidate_source(
        candidate.source_label or "",
    )
    rows = [
        _bilevel_candidate_source_filter_variable_row(
            candidate_index=candidate_index,
            source_catalog=source_catalog,
            candidate_source=candidate_source,
            difference_type="missing-target",
            variable_name=variable_name,
        )
        for variable_name in sorted(target_variables - candidate_variables)
    ]
    rows.extend(
        _bilevel_candidate_source_filter_variable_row(
            candidate_index=candidate_index,
            source_catalog=source_catalog,
            candidate_source=candidate_source,
            difference_type="extra-candidate",
            variable_name=variable_name,
        )
        for variable_name in sorted(candidate_variables - target_variables)
    )
    return tuple(rows)


def _bilevel_candidate_source_filter_variable_row(
    *,
    candidate_index: int,
    source_catalog: str,
    candidate_source: str,
    difference_type: str,
    variable_name: str,
) -> dict[str, Any]:
    return {
        "candidate_index": candidate_index,
        "source_catalog": source_catalog,
        "candidate_source": candidate_source,
        "difference_type": difference_type,
        "variable_name": variable_name,
    }


def _bilevel_candidate_audit_delta_summary_row(
    summary_row: dict[str, Any],
) -> dict[str, Any]:
    row = _bilevel_candidate_audit_base_row("candidate-delta-summary")
    row.update(
        {
            "candidate_index": summary_row["candidate_index"],
            "candidate_source": summary_row["candidate_source"],
            "component_name": summary_row["component_name"],
            "accepted_only_count": summary_row["accepted_only_count"],
            "candidate_only_count": summary_row["candidate_only_count"],
            "total_delta_count": summary_row["total_delta_count"],
        },
    )
    return row


def _bilevel_candidate_audit_skipped_row(skipped_row: dict[str, Any]) -> dict[str, Any]:
    row = _bilevel_candidate_audit_base_row("skipped-candidate")
    row.update(
        {
            "skip_index": skipped_row["skip_index"],
            "candidate_label": skipped_row["candidate_label"],
            "candidate_source": skipped_row["candidate_source"],
            "selected_binary_count": skipped_row["selected_binary_count"],
            "unselected_binary_count": skipped_row["unselected_binary_count"],
            "selected_variables": skipped_row["selected_variables"],
            "reason": skipped_row["reason"],
        },
    )
    return row


def _bilevel_candidate_audit_skipped_delta_summary_row(
    summary_row: dict[str, Any],
) -> dict[str, Any]:
    row = _bilevel_candidate_audit_base_row("skipped-candidate-delta-summary")
    row.update(
        {
            "skip_index": summary_row["skip_index"],
            "candidate_label": summary_row["candidate_label"],
            "candidate_source": summary_row["candidate_source"],
            "component_name": summary_row["component_name"],
            "accepted_only_count": summary_row["accepted_only_count"],
            "candidate_only_count": summary_row["candidate_only_count"],
            "total_delta_count": summary_row["total_delta_count"],
            "reason": summary_row["reason"],
        },
    )
    return row


def _candidate_source_labels(
    candidates: Iterable[BilevelCandidateAssignment],
) -> str:
    return ";".join(
        candidate.source_label
        for candidate in candidates
        if candidate.source_label is not None
    )


def _split_qualified_candidate_source(source_label: str) -> tuple[str, str]:
    source_catalog, separator, source = source_label.partition(":")
    if separator and source_catalog in {"calibrated", "uncalibrated"}:
        return source_catalog, source
    return "", source_label


def _binary_selection_delta_type(*, accepted_value: int, candidate_value: int) -> str:
    if accepted_value == 0 and candidate_value == 1:
        return "candidate-only"
    if accepted_value == 1 and candidate_value == 0:
        return "accepted-only"
    raise ValueError("selection delta requires different binary values")


def _binary_selection_component_name(variable_name: str) -> str:
    return variable_name.split("[", maxsplit=1)[0]


def _contribution2_bilevel_benchmark_trajectory_row(
    result: Contribution2ComputationalResult,
) -> dict[str, Any]:
    return {
        "test_number": result.test_number,
        "scenario": result.scenario,
        "iteration_index": 1,
        "objective_value": result.best_solution_found,
        "best_bound": result.best_possible,
        "optimality_gap": _optional_difference(
            result.best_solution_found,
            result.best_possible,
        ),
        "elapsed_seconds": result.computational_time_seconds,
        "hit_time_limit": result.hit_time_limit,
        "selected_binary_count": None,
        "unselected_binary_count": None,
        "subproblem_status": "reported",
        "stop_reason": "reported",
    }


def _contribution2_bilevel_benchmark_rows_by_iteration(
    *,
    test_number: int,
    scenario: int,
    benchmark_rows: Iterable[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    return {
        row["iteration_index"]: row
        for row in benchmark_rows
        if row["test_number"] == test_number and row["scenario"] == scenario
    }


def _contribution2_bilevel_trajectory_comparison_row(
    *,
    test_number: int,
    scenario: int,
    iteration_index: int,
    field: str,
    actual: Any,
    benchmark: Any,
    absolute_tolerance: float,
) -> dict[str, Any]:
    absolute_deviation = _optional_absolute_difference(actual, benchmark)
    within_tolerance = (
        actual == benchmark
        if absolute_deviation is None
        else absolute_deviation <= absolute_tolerance
    )
    return {
        "test_number": test_number,
        "scenario": scenario,
        "iteration_index": iteration_index,
        "field": field,
        "actual": actual,
        "benchmark": benchmark,
        "absolute_deviation": absolute_deviation,
        "within_tolerance": within_tolerance,
    }


def _style_decomposition_objective_comparison_row(
    *,
    catalog: str,
    scenario: StaticStyleScenario,
    iteration_index: int,
    objective_value: float,
    benchmark_total_cost: float,
    absolute_tolerance: float,
) -> dict[str, Any]:
    absolute_deviation = abs(objective_value - benchmark_total_cost)
    return {
        "catalog": catalog,
        "case_study": scenario.case_study,
        "scenario": scenario.scenario,
        "iteration_index": iteration_index,
        "objective_value": objective_value,
        "benchmark_total_cost": benchmark_total_cost,
        "absolute_deviation": absolute_deviation,
        "within_tolerance": absolute_deviation <= absolute_tolerance,
    }


def _style_fuel_consumption_residual_ranking_row(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    table_row = next(row for row in rows if row["equipment_family"] == "table_total")
    included_family_rows = tuple(
        row
        for row in rows
        if row["included_in_table_fuel_consumption"]
        and row["equipment_family"] != "table_total"
    )
    largest_family = max(
        included_family_rows,
        key=lambda row: (row["fuel_consumption"], row["equipment_family"]),
    )
    table_fuel_consumption = table_row["table_fuel_consumption"]
    benchmark_fuel_consumption = table_row["benchmark_fuel_consumption"]
    residual = table_row["fuel_consumption_residual"]
    return {
        "catalog": table_row["catalog"],
        "case_study": table_row["case_study"],
        "scenario": table_row["scenario"],
        "residual_rank": 0,
        "largest_fuel_family": largest_family["equipment_family"],
        "largest_family_fuel_consumption": largest_family["fuel_consumption"],
        "largest_family_share_of_table": _safe_divide(
            largest_family["fuel_consumption"],
            table_fuel_consumption,
        ),
        "benchmark_fuel_consumption": benchmark_fuel_consumption,
        "table_fuel_consumption": table_fuel_consumption,
        "fuel_consumption_residual": residual,
        "absolute_fuel_consumption_residual": abs(residual),
        "residual_percent_of_benchmark": _safe_percent(
            residual,
            benchmark_fuel_consumption,
        ),
    }


def _style_fuel_consumption_capacity_row(
    row: dict[str, Any],
    context: Any,
) -> dict[str, Any]:
    return {
        "catalog": row["catalog"],
        "case_study": row["case_study"],
        "scenario": row["scenario"],
        "equipment_family": row["equipment_family"],
        "equipment_name": row["equipment_name"],
        "fuel_variable": row["fuel_variable"],
        "fuel_consumption": row["fuel_consumption"],
        "selection_variable": context.selection_variable,
        "selected": context.selected,
        "capacity_basis": context.capacity_basis,
        "actual_capacity_basis_value": context.actual_capacity_basis_value,
        "capacity_value": context.capacity_value,
        "capacity_utilization": context.capacity_utilization,
        "benchmark_fuel_consumption": row["benchmark_fuel_consumption"],
        "table_fuel_consumption": row["table_fuel_consumption"],
        "fuel_consumption_residual": row["fuel_consumption_residual"],
    }


def _style_fuel_consumption_diagnosis_row(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    scenario_row = rows[0]
    included_rows = tuple(row for row in rows if row["equipment_family"] != "hot_oil")
    largest_included = (
        max(
            included_rows,
            key=lambda row: (row["fuel_consumption"], row["equipment_family"]),
        )
        if included_rows
        else None
    )
    hot_oil_heat_load = sum(
        (
            row["actual_capacity_basis_value"] or 0.0
            for row in rows
            if row["equipment_family"] == "hot_oil"
        ),
        0.0,
    )
    auxiliary_vhp_fuel_consumption = sum(
        (
            row["fuel_consumption"]
            for row in rows
            if row["equipment_family"] == "vhp_source"
        ),
        0.0,
    )
    residual = scenario_row["fuel_consumption_residual"]
    largest_capacity_utilization = (
        None if largest_included is None else largest_included["capacity_utilization"]
    )
    return {
        "catalog": scenario_row["catalog"],
        "case_study": scenario_row["case_study"],
        "scenario": scenario_row["scenario"],
        "residual_rank": 0,
        "residual_driver": _fuel_consumption_residual_driver(
            residual=residual,
            largest_included_capacity_utilization=largest_capacity_utilization,
            hot_oil_heat_load=hot_oil_heat_load,
            auxiliary_vhp_fuel_consumption=auxiliary_vhp_fuel_consumption,
        ),
        "largest_included_equipment_family": (
            None if largest_included is None else largest_included["equipment_family"]
        ),
        "largest_included_equipment_name": (
            None if largest_included is None else largest_included["equipment_name"]
        ),
        "largest_included_fuel_consumption": (
            None if largest_included is None else largest_included["fuel_consumption"]
        ),
        "largest_included_capacity_utilization": largest_capacity_utilization,
        "hot_oil_heat_load": hot_oil_heat_load,
        "auxiliary_vhp_fuel_consumption": auxiliary_vhp_fuel_consumption,
        "benchmark_fuel_consumption": scenario_row["benchmark_fuel_consumption"],
        "table_fuel_consumption": scenario_row["table_fuel_consumption"],
        "fuel_consumption_residual": residual,
        "absolute_fuel_consumption_residual": abs(residual),
    }


def _fuel_consumption_residual_driver(
    *,
    residual: float,
    largest_included_capacity_utilization: float | None,
    hot_oil_heat_load: float,
    auxiliary_vhp_fuel_consumption: float,
) -> str:
    if abs(residual) <= 1e-9:
        return "within_tolerance"
    if (
        largest_included_capacity_utilization is not None
        and largest_included_capacity_utilization >= 0.999
    ):
        return "capped_fuel_capacity"
    if hot_oil_heat_load > 0.0:
        return "hot_oil_heat_load_context"
    if auxiliary_vhp_fuel_consumption > 0.0:
        return "auxiliary_vhp_fuel_context"
    return "unclassified"


def _style_fuel_calibration_target_row(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    scenario_row = rows[0]
    target_row = _largest_included_fuel_row(rows)
    residual = scenario_row["fuel_consumption_residual"]
    current_fuel = None if target_row is None else target_row["fuel_consumption"]
    required_fuel = None if current_fuel is None else current_fuel - residual
    adjustment = (
        None
        if required_fuel is None or current_fuel is None
        else required_fuel - current_fuel
    )
    adjustment_factor = (
        None
        if required_fuel is None or current_fuel is None
        else _safe_divide(required_fuel, current_fuel)
    )
    return {
        "catalog": scenario_row["catalog"],
        "case_study": scenario_row["case_study"],
        "scenario": scenario_row["scenario"],
        "residual_rank": 0,
        "calibration_action": _fuel_calibration_action(
            residual=residual,
            capacity_utilization=None
            if target_row is None
            else target_row["capacity_utilization"],
        ),
        "target_equipment_family": (
            None if target_row is None else target_row["equipment_family"]
        ),
        "target_equipment_name": (
            None if target_row is None else target_row["equipment_name"]
        ),
        "capacity_basis": None if target_row is None else target_row["capacity_basis"],
        "capacity_utilization": (
            None if target_row is None else target_row["capacity_utilization"]
        ),
        "current_equipment_fuel_consumption": current_fuel,
        "required_equipment_fuel_consumption": required_fuel,
        "fuel_consumption_adjustment": adjustment,
        "fuel_consumption_adjustment_factor": adjustment_factor,
        "benchmark_fuel_consumption": scenario_row["benchmark_fuel_consumption"],
        "table_fuel_consumption": scenario_row["table_fuel_consumption"],
        "target_table_fuel_consumption": scenario_row["benchmark_fuel_consumption"],
        "fuel_consumption_residual": residual,
    }


def _largest_included_fuel_row(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    included_rows = tuple(row for row in rows if row["equipment_family"] != "hot_oil")
    if not included_rows:
        return None
    return max(
        included_rows,
        key=lambda row: (row["fuel_consumption"], row["equipment_family"]),
    )


def _fuel_calibration_action(
    *,
    residual: float,
    capacity_utilization: float | None,
) -> str:
    if abs(residual) <= 1e-9:
        return "within_tolerance"
    if capacity_utilization is not None and capacity_utilization >= 0.999:
        if residual > 0.0:
            return "reduce_largest_capped_equipment_fuel"
            return "increase_largest_capped_equipment_fuel"
    return "no_capped_capacity_target"


def _operating_cost_total_row(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    for row in rows:
        if row["operating_cost_component"] == "total":
            return row
    return None


def _largest_operating_cost_component_residual(
    rows: Sequence[dict[str, Any]],
) -> dict[str, Any] | None:
    component_rows = tuple(
        row for row in rows if row["operating_cost_component"] != "total"
    )
    if not component_rows:
        return None
    return max(
        component_rows,
        key=lambda row: (
            abs(row["operating_cost_residual"]),
            row["operating_cost_component"],
        ),
    )


def _benchmark_operating_cost_components(
    benchmark: Contribution2BestConfiguration,
) -> dict[str, float]:
    fuel = benchmark.fuel_cost
    hot_oil = benchmark.hot_oil_operating_cost or 0.0
    electricity = benchmark.power_revenue or 0.0
    auxiliary = benchmark.operating_cost - fuel - hot_oil - electricity
    return {
        "fuel": fuel,
        "hot_oil": hot_oil,
        "electricity": electricity,
        "auxiliary_or_unallocated": auxiliary,
        "total": benchmark.operating_cost,
    }


def _steam_property_comparison_row(
    comparison: Contribution2SteamPropertyComparison,
) -> dict[str, Any]:
    return _steam_property_comparison_row_from_values(
        comparison,
        real_isentropic_enthalpy_change=comparison.real_isentropic_enthalpy_change,
        iapws_power_generation=comparison.iapws_power_generation,
    )


def _steam_property_comparison_row_from_values(
    comparison: Contribution2SteamPropertyComparison,
    *,
    real_isentropic_enthalpy_change: float | None,
    iapws_power_generation: float,
) -> dict[str, Any]:
    return {
        "configuration": comparison.configuration,
        "turbine": comparison.turbine,
        "inlet_temperature": comparison.inlet_temperature,
        "inlet_pressure": comparison.inlet_pressure,
        "outlet_pressure": comparison.outlet_pressure,
        "real_isentropic_enthalpy_change": real_isentropic_enthalpy_change,
        "model_isentropic_enthalpy_change": (
            comparison.model_isentropic_enthalpy_change
        ),
        "enthalpy_change_deviation": _optional_difference(
            comparison.model_isentropic_enthalpy_change,
            real_isentropic_enthalpy_change,
        ),
        "iapws_power_generation": iapws_power_generation,
        "model_power_generation": comparison.model_power_generation,
        "power_generation_deviation": (
            comparison.model_power_generation - iapws_power_generation
        ),
    }


def _model_turbine_flow(comparison: Contribution2SteamPropertyComparison) -> float:
    model_enthalpy_change = _required_property_value(
        comparison.model_isentropic_enthalpy_change,
        "model_isentropic_enthalpy_change",
    )
    return comparison.model_power_generation / model_enthalpy_change


def _required_property_value(value: float | None, name: str) -> float:
    if value is None:
        raise ValueError(f"{name} is required for turbine steam-property rows")
    return value


def _optional_difference(
    actual: float | None,
    benchmark: float | None,
) -> float | None:
    if actual is None or benchmark is None:
        return None
    return actual - benchmark


def _safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0.0:
        return None
    return numerator / denominator


def _safe_percent(numerator: float, denominator: float) -> float | None:
    ratio = _safe_divide(numerator, denominator)
    if ratio is None:
        return None
    return 100.0 * ratio


def _optional_absolute_difference(actual: Any, benchmark: Any) -> float | None:
    if actual is None or benchmark is None:
        return None
    if isinstance(actual, bool) or isinstance(benchmark, bool):
        return None
    if isinstance(actual, int | float) and isinstance(benchmark, int | float):
        return abs(float(actual) - float(benchmark))
    return None


def _format_comparison_rows_csv(rows: Sequence[dict[str, Any]]) -> str:
    return _format_rows_csv(rows, COMPARISON_ROW_FIELDS)


def _format_rows_csv(
    rows: Sequence[dict[str, Any]],
    fieldnames: Sequence[str],
) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()
