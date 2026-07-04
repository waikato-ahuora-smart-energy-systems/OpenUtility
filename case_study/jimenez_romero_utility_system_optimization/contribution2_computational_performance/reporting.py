"""Contribution 2 computational-performance reporting helpers."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Sequence
from io import StringIO
from typing import Any, Protocol

from OpenUtility.style.properties import (
    CoolPropSteamPropertyProvider,
    SteamPropertyProvider,
)


class _ComputationalResultRecord(Protocol):
    @property
    def test_number(self) -> int: ...

    @property
    def scenario(self) -> int: ...

    @property
    def method(self) -> str: ...

    @property
    def best_solution_found(self) -> float: ...

    @property
    def best_possible(self) -> float | None: ...

    @property
    def computational_time_seconds(self) -> float: ...

    @property
    def hit_time_limit(self) -> bool: ...


class _ModelStatisticRecord(Protocol):
    @property
    def test_number(self) -> int: ...

    @property
    def reference(self) -> str: ...

    @property
    def steam_mains(self) -> int: ...

    @property
    def power_demand(self) -> float: ...

    @property
    def integrates_hot_oil_and_fsr(self) -> bool: ...

    @property
    def variable_count(self) -> int: ...

    @property
    def binary_count(self) -> int: ...

    @property
    def equation_count(self) -> int: ...


class _SteamPropertyComparisonRecord(Protocol):
    @property
    def configuration(self) -> str: ...

    @property
    def turbine(self) -> str: ...

    @property
    def inlet_temperature(self) -> float | None: ...

    @property
    def inlet_pressure(self) -> float | None: ...

    @property
    def outlet_pressure(self) -> float | None: ...

    @property
    def real_isentropic_enthalpy_change(self) -> float | None: ...

    @property
    def iapws_power_generation(self) -> float: ...

    @property
    def model_isentropic_enthalpy_change(self) -> float | None: ...

    @property
    def model_power_generation(self) -> float: ...


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


def steam_property_comparison_rows(
    comparisons: Iterable[_SteamPropertyComparisonRecord],
) -> tuple[dict[str, Any], ...]:
    """Return Contribution 2 steam-property comparison rows."""

    return tuple(
        _steam_property_comparison_row(comparison) for comparison in comparisons
    )


def model_derived_steam_property_comparison_rows(
    comparisons: Iterable[_SteamPropertyComparisonRecord],
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
    statistics: Iterable[_ModelStatisticRecord],
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
    results: Iterable[_ComputationalResultRecord],
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
    results: Iterable[_ComputationalResultRecord],
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
    results: Iterable[_ComputationalResultRecord],
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
    results: Iterable[_ComputationalResultRecord],
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
    benchmark_rows: Iterable[dict[str, Any]],
    fields: Sequence[str] = CONTRIBUTION2_BILEVEL_TRAJECTORY_COMPARISON_FIELDS,
    absolute_tolerance: float = 1e-6,
) -> tuple[dict[str, Any], ...]:
    """Compare generated bilevel trajectory rows with Contribution 2 fixtures."""

    if absolute_tolerance < 0.0:
        raise ValueError("absolute_tolerance must be non-negative")
    selected_benchmark_rows = _contribution2_bilevel_benchmark_rows_by_iteration(
        test_number=test_number,
        scenario=scenario,
        benchmark_rows=benchmark_rows,
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
    results: Iterable[_ComputationalResultRecord],
) -> tuple[tuple[tuple[int, int], tuple[_ComputationalResultRecord, ...]], ...]:
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
    result: _ComputationalResultRecord,
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
    results: tuple[_ComputationalResultRecord, ...],
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


def _contribution2_bilevel_benchmark_trajectory_row(
    result: _ComputationalResultRecord,
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


def _steam_property_comparison_row(
    comparison: _SteamPropertyComparisonRecord,
) -> dict[str, Any]:
    return _steam_property_comparison_row_from_values(
        comparison,
        real_isentropic_enthalpy_change=comparison.real_isentropic_enthalpy_change,
        iapws_power_generation=comparison.iapws_power_generation,
    )


def _steam_property_comparison_row_from_values(
    comparison: _SteamPropertyComparisonRecord,
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


def _model_turbine_flow(
    comparison: _SteamPropertyComparisonRecord,
) -> float:
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


def _optional_absolute_difference(actual: Any, benchmark: Any) -> float | None:
    if actual is None or benchmark is None:
        return None
    if isinstance(actual, bool) or isinstance(benchmark, bool):
        return None
    if isinstance(actual, int | float) and isinstance(benchmark, int | float):
        return abs(float(actual) - float(benchmark))
    return None


def _format_rows_csv(rows: Sequence[dict[str, Any]], fields: Sequence[str]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field) for field in fields})
    return output.getvalue().strip()


__all__ = (
    "CONTRIBUTION2_BILEVEL_BENCHMARK_TRAJECTORY_ROW_FIELDS",
    "CONTRIBUTION2_BILEVEL_TRAJECTORY_COMPARISON_FIELDS",
    "CONTRIBUTION2_BILEVEL_TRAJECTORY_COMPARISON_ROW_FIELDS",
    "contribution2_bilevel_benchmark_trajectory_rows",
    "contribution2_bilevel_trajectory_comparison_rows",
    "contribution2_computational_best_method_rows",
    "contribution2_computational_method_summary_rows",
    "contribution2_computational_result_rows",
    "contribution2_model_statistic_rows",
    "format_contribution2_bilevel_benchmark_trajectory_rows",
    "format_contribution2_bilevel_trajectory_comparison_rows",
    "format_contribution2_computational_best_method_rows",
    "format_contribution2_computational_method_summary_rows",
    "format_contribution2_computational_result_rows",
    "format_contribution2_model_statistic_rows",
    "format_steam_property_comparison_rows",
    "model_derived_steam_property_comparison_rows",
    "steam_property_comparison_rows",
)
