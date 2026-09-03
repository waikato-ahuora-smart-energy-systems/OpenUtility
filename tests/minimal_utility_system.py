from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MinimalUtilityBenchmark:
    case_study: str
    scenario: str
    utility_steam_flow: float
    fuel_consumption: float
    power_generation: float
    operating_cost: float
    maintenance_cost: float | None
    capital_cost: float
    total_annualized_cost: float


@dataclass(frozen=True)
class MinimalBestConfigurationBenchmark:
    utility_steam_generation: float
    fuel_consumption: float
    power_generation: float
    steam_turbine_power: float
    gas_turbine_power: float
    operating_cost: float
    maintenance_cost: float
    capital_cost: float
    total_cost: float
    fuel_cost: float
    hot_oil_operating_cost: float | None = None
    power_revenue: float | None = None


def minimal_utility_benchmark() -> MinimalUtilityBenchmark:
    return MinimalUtilityBenchmark(
        case_study="example-site",
        scenario="gas-turbine-with-steam-turbine",
        utility_steam_flow=239.86,
        fuel_consumption=249.03,
        power_generation=46.67,
        operating_cost=51.04,
        maintenance_cost=1.75,
        capital_cost=11.98,
        total_annualized_cost=64.77,
    )


def minimal_best_configuration_benchmark(
    scenario: str = "gas-turbine-microgrid",
) -> MinimalBestConfigurationBenchmark:
    if scenario == "heat-recovery-microgrid":
        return MinimalBestConfigurationBenchmark(
            utility_steam_generation=136.67,
            fuel_consumption=175.03,
            power_generation=46.67,
            steam_turbine_power=11.41,
            gas_turbine_power=35.26,
            operating_cost=41.66,
            maintenance_cost=2.63,
            capital_cost=9.60,
            total_cost=53.89,
            fuel_cost=29.10,
            hot_oil_operating_cost=13.81,
        )
    return MinimalBestConfigurationBenchmark(
        utility_steam_generation=217.78,
        fuel_consumption=245.04,
        power_generation=46.67,
        steam_turbine_power=20.88,
        gas_turbine_power=25.79,
        operating_cost=50.49,
        maintenance_cost=3.59,
        capital_cost=10.78,
        total_cost=64.86,
        fuel_cost=51.78,
    )
