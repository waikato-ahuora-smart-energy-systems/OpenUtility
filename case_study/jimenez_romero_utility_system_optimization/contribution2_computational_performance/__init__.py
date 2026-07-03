"""Contribution 2 computational-performance and steam-property benchmark data."""

from __future__ import annotations

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    CONTRIBUTION2_COMPUTATIONAL_RESULTS,
    CONTRIBUTION2_MODEL_STATISTICS,
    CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS,
    Contribution2ComputationalResult,
    Contribution2ModelStatistic,
    Contribution2SteamPropertyComparison,
    get_contribution2_computational_result,
    get_contribution2_model_statistic,
    get_contribution2_steam_property_comparison,
)
from .bilevel import (
    contribution2_reported_bilevel_decomposition_run,
    contribution2_synthetic_bilevel_decomposition_run,
)
from .reporting import (
    contribution2_bilevel_benchmark_trajectory_rows,
    contribution2_bilevel_trajectory_comparison_rows,
    contribution2_computational_best_method_rows,
    contribution2_computational_method_summary_rows,
    contribution2_computational_result_rows,
    contribution2_model_statistic_rows,
    format_contribution2_bilevel_benchmark_trajectory_rows,
    format_contribution2_bilevel_trajectory_comparison_rows,
    format_contribution2_computational_best_method_rows,
    format_contribution2_computational_method_summary_rows,
    format_contribution2_computational_result_rows,
    format_contribution2_model_statistic_rows,
    format_steam_property_comparison_rows,
    model_derived_steam_property_comparison_rows,
    steam_property_comparison_rows,
)

CONTRIBUTION2_SOLVER_PERFORMANCE_RESULTS = CONTRIBUTION2_COMPUTATIONAL_RESULTS
CONTRIBUTION2_MODEL_SIZE_STATISTICS = CONTRIBUTION2_MODEL_STATISTICS
CONTRIBUTION2_STEAM_TURBINE_PROPERTY_COMPARISONS = (
    CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS
)

__all__ = (
    "CONTRIBUTION2_COMPUTATIONAL_RESULTS",
    "CONTRIBUTION2_MODEL_SIZE_STATISTICS",
    "CONTRIBUTION2_MODEL_STATISTICS",
    "CONTRIBUTION2_SOLVER_PERFORMANCE_RESULTS",
    "CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS",
    "CONTRIBUTION2_STEAM_TURBINE_PROPERTY_COMPARISONS",
    "Contribution2ComputationalResult",
    "Contribution2ModelStatistic",
    "Contribution2SteamPropertyComparison",
    "contribution2_bilevel_benchmark_trajectory_rows",
    "contribution2_bilevel_trajectory_comparison_rows",
    "contribution2_computational_best_method_rows",
    "contribution2_computational_method_summary_rows",
    "contribution2_computational_result_rows",
    "contribution2_model_statistic_rows",
    "contribution2_reported_bilevel_decomposition_run",
    "contribution2_synthetic_bilevel_decomposition_run",
    "format_contribution2_bilevel_benchmark_trajectory_rows",
    "format_contribution2_bilevel_trajectory_comparison_rows",
    "format_contribution2_computational_best_method_rows",
    "format_contribution2_computational_method_summary_rows",
    "format_contribution2_computational_result_rows",
    "format_contribution2_model_statistic_rows",
    "format_steam_property_comparison_rows",
    "get_contribution2_computational_result",
    "get_contribution2_model_statistic",
    "get_contribution2_steam_property_comparison",
    "model_derived_steam_property_comparison_rows",
    "steam_property_comparison_rows",
)
