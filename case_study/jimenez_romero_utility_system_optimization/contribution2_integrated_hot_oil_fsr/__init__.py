"""Contribution 2 integrated hot-oil and flash-steam-recovery case-study data."""

from __future__ import annotations

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS,
    STYLE_CASE_STUDY_2_EQUIPMENT_COSTS,
    STYLE_CASE_STUDY_2_RESOURCES,
    STYLE_CASE_STUDY_2_RESULTS,
    STYLE_CASE_STUDY_2_SITE_CONFIG,
    STYLE_CASE_STUDY_2_STREAMS,
    STYLE_GAS_TURBINE_AMBIENT_CORRECTION,
    STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS,
    STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS,
    Contribution2BestConfiguration,
    StyleGasTurbineAmbientCorrection,
    StyleGasTurbineFullLoadCoefficient,
    StyleGasTurbinePartLoadCoefficient,
    StyleEquipmentCostCoefficient,
    StyleResource,
    StyleBenchmarkResult,
    StyleSiteConfig,
    StyleProcessStream,
    get_contribution2_case_study2_best_configuration,
    get_style_result,
)

CONTRIBUTION2_INTEGRATED_HOT_OIL_FSR_BEST_CONFIGURATIONS = (
    CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS
)
STYLE_CASE_STUDY_2_TOTAL_SITE_PROCESS_STREAMS = STYLE_CASE_STUDY_2_STREAMS
STYLE_CASE_STUDY_2_TOTAL_SITE_UTILITY_BENCHMARKS = STYLE_CASE_STUDY_2_RESULTS

__all__ = (
    "CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS",
    "CONTRIBUTION2_INTEGRATED_HOT_OIL_FSR_BEST_CONFIGURATIONS",
    "STYLE_CASE_STUDY_2_EQUIPMENT_COSTS",
    "STYLE_CASE_STUDY_2_RESOURCES",
    "STYLE_CASE_STUDY_2_RESULTS",
    "STYLE_CASE_STUDY_2_SITE_CONFIG",
    "STYLE_CASE_STUDY_2_STREAMS",
    "STYLE_CASE_STUDY_2_TOTAL_SITE_PROCESS_STREAMS",
    "STYLE_CASE_STUDY_2_TOTAL_SITE_UTILITY_BENCHMARKS",
    "STYLE_GAS_TURBINE_AMBIENT_CORRECTION",
    "STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS",
    "STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS",
    "Contribution2BestConfiguration",
    "StyleGasTurbineAmbientCorrection",
    "StyleGasTurbineFullLoadCoefficient",
    "StyleGasTurbinePartLoadCoefficient",
    "StyleEquipmentCostCoefficient",
    "StyleResource",
    "StyleBenchmarkResult",
    "StyleSiteConfig",
    "StyleProcessStream",
    "get_contribution2_case_study2_best_configuration",
    "get_style_result",
)
