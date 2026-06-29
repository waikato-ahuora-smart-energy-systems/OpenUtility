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
    "get_contribution2_computational_result",
    "get_contribution2_model_statistic",
    "get_contribution2_steam_property_comparison",
)
