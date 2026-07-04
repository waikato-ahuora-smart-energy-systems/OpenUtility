"""Notebook-oriented workflows for STYLE case-study replication."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    get_contribution2_case_study2_best_configuration,
)
from OpenUtility.style import (
    StaticStyleScenarioCatalog,
    best_configuration_comparison_rows,
    best_configuration_summary_row,
    compare_static_style_result_to_best_configuration,
    pyomo_static_style_solver,
    run_static_style_scenario,
    style_fuel_calibration_target_rows,
    style_fuel_consumption_capacity_rows,
    style_fuel_consumption_factor_map_from_calibration_target_rows,
    style_operating_cost_adjustment_map_from_target_rows,
    style_operating_cost_component_rows,
    style_operating_cost_target_rows,
)
from case_study.jimenez_romero_utility_system_optimization.style_model_builders import (
    style_case_study_2_contribution2_best_configuration_catalog,
    style_case_study_2_contribution2_physical_profile_catalog,
)


TABLE_2_9_CATALOGS = ("reported-equipment", "physical-profile")


@dataclass(frozen=True)
class Contribution2Table29NotebookRun:
    """Solved STYLE Table 2-9 case-study data prepared for notebooks."""

    catalog: str
    comparison_rows: tuple[dict[str, Any], ...]
    summary_rows: tuple[dict[str, Any], ...]

    def comparison_table(self, *, digits: int | None = 2) -> pd.DataFrame:
        """Return one row per reported model-versus-benchmark field."""

        return _rows_to_frame(self.comparison_rows, digits=digits)

    def summary_table(self, *, digits: int | None = 6) -> pd.DataFrame:
        """Return one row per solved scenario."""

        return _rows_to_frame(self.summary_rows, digits=digits)

    def field_table(self, field: str, *, digits: int | None = 2) -> pd.DataFrame:
        """Return comparison rows for one reported output field."""

        table = self.comparison_table(digits=digits)
        return table.loc[table["field"] == field].reset_index(drop=True)

    def plot_field_comparison(self, field: str, *, ax: Any | None = None) -> Any:
        """Plot model and benchmark values for one reported output field."""

        axis = _resolve_axis(ax)
        table = self.field_table(field, digits=None)
        x_positions = range(len(table))
        width = 0.38
        axis.bar(
            [position - width / 2 for position in x_positions],
            table["actual"],
            width=width,
            label="OpenUtility",
        )
        axis.bar(
            [position + width / 2 for position in x_positions],
            table["benchmark"],
            width=width,
            label="Benchmark",
        )
        axis.set_title(field)
        axis.set_ylabel(field)
        axis.set_xticks(tuple(x_positions), table["scenario"], rotation=30, ha="right")
        axis.legend()
        return axis

    def plot_summary_deviations(self, *, ax: Any | None = None) -> Any:
        """Plot the maximum absolute deviation for each solved scenario."""

        axis = _resolve_axis(ax)
        table = self.summary_table(digits=None)
        axis.bar(table["scenario"], table["max_absolute_deviation"])
        axis.set_title("Maximum absolute deviation by scenario")
        axis.set_ylabel("absolute deviation")
        axis.tick_params(axis="x", rotation=30)
        return axis


def run_contribution2_table_2_9_case_study(
    *,
    catalog: str = "physical-profile",
    calibrated: bool = True,
    apply_fuel_targets: bool = True,
    apply_operating_targets: bool = True,
    solver_time_limit: float = 20.0,
) -> Contribution2Table29NotebookRun:
    """Solve a STYLE Table 2-9 case-study catalog for notebook exploration."""

    scenario_catalog = _table_2_9_catalog(
        catalog,
        calibrated=calibrated,
        apply_fuel_targets=apply_fuel_targets,
        apply_operating_targets=apply_operating_targets,
        solver_time_limit=solver_time_limit,
    )
    comparison_rows, summary_rows = _comparison_and_summary_rows(
        catalog=catalog,
        scenario_catalog=scenario_catalog,
        solver_time_limit=solver_time_limit,
    )
    return Contribution2Table29NotebookRun(
        catalog=catalog,
        comparison_rows=comparison_rows,
        summary_rows=summary_rows,
    )


def _table_2_9_catalog(
    catalog: str,
    *,
    calibrated: bool,
    apply_fuel_targets: bool,
    apply_operating_targets: bool,
    solver_time_limit: float,
) -> StaticStyleScenarioCatalog:
    if catalog == "reported-equipment":
        if apply_fuel_targets or apply_operating_targets:
            raise ValueError("target bridges are only available for physical-profile")
        return style_case_study_2_contribution2_best_configuration_catalog(
            match_reported_economics=calibrated,
        )
    if catalog == "physical-profile":
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
    raise ValueError(f"unsupported STYLE Table 2-9 catalog {catalog!r}")


def _physical_profile_fuel_target_factors(
    *,
    calibrated: bool,
    solver_time_limit: float,
) -> dict[str, dict[tuple[str, str], float]]:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=calibrated,
    )
    rows = _fuel_capacity_rows(catalog, solver_time_limit=solver_time_limit)
    target_rows = style_fuel_calibration_target_rows(rows)
    return style_fuel_consumption_factor_map_from_calibration_target_rows(target_rows)


def _physical_profile_operating_cost_target_adjustments(
    *,
    calibrated: bool,
    solver_time_limit: float,
    fuel_factors_by_scenario: Mapping[str, Mapping[tuple[str, str], float]] | None,
) -> dict[str, dict[str, float]]:
    catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=calibrated,
        fuel_consumption_factors_by_scenario=fuel_factors_by_scenario,
    )
    rows = _operating_cost_component_rows(catalog, solver_time_limit=solver_time_limit)
    target_rows = style_operating_cost_target_rows(rows)
    return style_operating_cost_adjustment_map_from_target_rows(target_rows)


def _fuel_capacity_rows(
    catalog: StaticStyleScenarioCatalog,
    *,
    solver_time_limit: float,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    for scenario in catalog:
        run = run_static_style_scenario(scenario, solve=solve)
        rows.extend(
            style_fuel_consumption_capacity_rows(
                catalog="physical-profile",
                scenario=scenario,
                model=run.model,
                benchmark=get_contribution2_case_study2_best_configuration(
                    scenario.scenario,
                ),
            ),
        )
    return tuple(rows)


def _operating_cost_component_rows(
    catalog: StaticStyleScenarioCatalog,
    *,
    solver_time_limit: float,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    for scenario in catalog:
        run = run_static_style_scenario(scenario, solve=solve)
        rows.extend(
            style_operating_cost_component_rows(
                catalog="physical-profile",
                scenario=scenario,
                model=run.model,
                benchmark=get_contribution2_case_study2_best_configuration(
                    scenario.scenario,
                ),
            ),
        )
    return tuple(rows)


def _comparison_and_summary_rows(
    *,
    catalog: str,
    scenario_catalog: StaticStyleScenarioCatalog,
    solver_time_limit: float,
) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    comparison_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    solve = _pyomo_highs_solver(solver_time_limit=solver_time_limit)
    for scenario in scenario_catalog:
        run = run_static_style_scenario(scenario, solve=solve)
        comparison = compare_static_style_result_to_best_configuration(
            run.result,
            get_contribution2_case_study2_best_configuration(scenario.scenario),
            absolute_tolerance=scenario.absolute_tolerance,
        )
        comparison_rows.extend(
            best_configuration_comparison_rows(
                catalog=catalog,
                comparison=comparison,
            ),
        )
        summary_rows.append(
            best_configuration_summary_row(
                catalog=catalog,
                comparison=comparison,
            ),
        )
    return tuple(comparison_rows), tuple(summary_rows)


def _pyomo_highs_solver(*, solver_time_limit: float):
    return pyomo_static_style_solver(
        "appsi_highs",
        options={"time_limit": solver_time_limit},
    )


def _rows_to_frame(
    rows: tuple[dict[str, Any], ...], *, digits: int | None
) -> pd.DataFrame:
    table = pd.DataFrame(rows)
    if digits is None or table.empty:
        return table
    numeric_columns = table.select_dtypes(include=("number",)).columns
    table.loc[:, numeric_columns] = table.loc[:, numeric_columns].round(digits)
    return table


def _resolve_axis(ax: Any | None) -> Any:
    if ax is not None:
        return ax
    from matplotlib import pyplot as plt

    _, axis = plt.subplots()
    return axis
