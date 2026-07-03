"""Regression targets extracted from Jimenez-Romero source result tables."""

from __future__ import annotations

from dataclasses import dataclass

from OpenPinch.classes.stream import Stream
from OpenPinch.classes.stream_collection import StreamCollection
from OpenPinch.classes.zone import Zone


@dataclass(frozen=True)
class StyleBenchmarkResult:
    """One reported STYLE result used as a regression target."""

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
class StyleSteamSystemTarget:
    """Steam-system target row reported for STYLE case study 1."""

    case_study: str
    scenario: str
    utility_steam_temperature: float
    boiler_flowrate: float
    letdown_flowrate: float
    power_generation: float
    power_generation_per_boiler_flow: float


@dataclass(frozen=True)
class StyleHotOilDesignResult:
    """Hot-oil design economics reported for STYLE case study 1."""

    case_study: str
    scenario: str
    mp_pressure: float
    lp_pressure: float
    boiler_flowrate: float
    power_generation: float
    boiler_fuel_cost: float
    hot_oil_fuel_cost: float
    power_cost: float
    cooling_cost: float
    treated_water_cost: float
    total_operating_cost: float
    boiler_capital_cost: float
    hot_oil_capital_cost: float
    steam_turbine_capital_cost: float
    deaerator_capital_cost: float
    total_capital_cost: float
    total_annualized_cost: float


@dataclass(frozen=True)
class StyleSiteConfig:
    """Site-wide operating constants extracted from a STYLE case-study table."""

    case_study: str
    power_demand: float
    max_power_export: float
    operating_hours: float
    interest_rate_percent: float
    plant_life_years: float
    capital_installation_factor: float
    cooling_water_temperature_rise: float
    boiler_feedwater_temperature: float
    vhp_pressure: float

    def __post_init__(self) -> None:
        _require_text(self.case_study, "case_study")
        _require_non_negative(self.power_demand, "power_demand")
        _require_non_negative(self.max_power_export, "max_power_export")
        _require_positive(self.operating_hours, "operating_hours")
        _require_non_negative(self.interest_rate_percent, "interest_rate_percent")
        _require_positive(self.plant_life_years, "plant_life_years")
        _require_non_negative(
            self.capital_installation_factor,
            "capital_installation_factor",
        )
        _require_non_negative(
            self.cooling_water_temperature_rise,
            "cooling_water_temperature_rise",
        )
        _require_non_negative(
            self.boiler_feedwater_temperature,
            "boiler_feedwater_temperature",
        )
        _require_positive(self.vhp_pressure, "vhp_pressure")


@dataclass(frozen=True)
class StyleResource:
    """Resource price row extracted from a STYLE case-study table."""

    case_study: str
    name: str
    lower_heating_value: float | None
    unit_cost: float
    cost_unit: str

    def __post_init__(self) -> None:
        _require_text(self.case_study, "case_study")
        _require_text(self.name, "resource name")
        if self.lower_heating_value is not None:
            _require_positive(self.lower_heating_value, "lower_heating_value")
        _require_non_negative(self.unit_cost, "unit_cost")
        _require_text(self.cost_unit, "cost_unit")


@dataclass(frozen=True)
class StyleEquipmentCostCoefficient:
    """Linear equipment capital-cost coefficient row from a STYLE case study."""

    case_study: str
    equipment_type: str
    subtype: str
    size_variable: str
    size_unit: str
    variable_cost: float
    fixed_cost: float
    range_lower: float | None
    range_upper: float | None
    reference: str

    def __post_init__(self) -> None:
        _require_text(self.case_study, "case_study")
        _require_text(self.equipment_type, "equipment_type")
        _require_text(self.subtype, "subtype")
        _require_text(self.size_variable, "size_variable")
        _require_text(self.size_unit, "size_unit")
        _require_non_negative(self.variable_cost, "variable_cost")
        _require_non_negative(self.fixed_cost, "fixed_cost")
        if self.range_lower is not None:
            _require_non_negative(self.range_lower, "range_lower")
        if self.range_upper is not None:
            _require_positive(self.range_upper, "range_upper")
        if (
            self.range_lower is not None
            and self.range_upper is not None
            and self.range_lower > self.range_upper
        ):
            raise ValueError("range_lower must not exceed range_upper")
        _require_text(self.reference, "reference")


@dataclass(frozen=True)
class StyleGasTurbineFullLoadCoefficient:
    """Gas-turbine full-load coefficients from Supplementary Information P1.B."""

    turbine_type: str
    full_load_a: float
    full_load_b: float
    air_flow_c: float
    air_flow_d: float

    def __post_init__(self) -> None:
        _require_text(self.turbine_type, "turbine_type")
        _require_positive(self.full_load_a, "full_load_a")
        _require_positive(self.full_load_b, "full_load_b")
        _require_positive(self.air_flow_c, "air_flow_c")
        _require_positive(self.air_flow_d, "air_flow_d")


@dataclass(frozen=True)
class StyleGasTurbineAmbientCorrection:
    """Gas-turbine ambient correction factors from Supplementary Information P1.B."""

    temperature_power_e: float
    temperature_power_f: float
    temperature_efficiency_g: float
    temperature_efficiency_h: float

    def __post_init__(self) -> None:
        _require_positive(self.temperature_power_e, "temperature_power_e")
        _require_positive(self.temperature_power_f, "temperature_power_f")
        _require_positive(
            self.temperature_efficiency_g,
            "temperature_efficiency_g",
        )
        _require_positive(
            self.temperature_efficiency_h,
            "temperature_efficiency_h",
        )


@dataclass(frozen=True)
class StyleGasTurbinePartLoadCoefficient:
    """Gas-turbine part-load coefficients from Supplementary Information P1.B."""

    fuel: str
    part_load_a: float
    part_load_b: float

    def __post_init__(self) -> None:
        _require_text(self.fuel, "fuel")
        _require_positive(self.part_load_a, "part_load_a")


def _require_text(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} must not be blank")


def _require_positive(value: float, label: str) -> None:
    if value <= 0.0:
        raise ValueError(f"{label} must be positive")


def _require_non_negative(value: float, label: str) -> None:
    if value < 0.0:
        raise ValueError(f"{label} must be non-negative")


@dataclass(frozen=True)
class Contribution2ModelStatistic:
    """Model statistic row for one Contribution 2 test example."""

    test_number: int
    reference: str
    steam_mains: int
    power_demand: float
    integrates_hot_oil_and_fsr: bool
    variable_count: int
    binary_count: int
    equation_count: int


@dataclass(frozen=True)
class Contribution2ComputationalResult:
    """Computational result for one Contribution 2 test scenario and method."""

    test_number: int
    scenario: int
    method: str
    best_solution_found: float
    best_possible: float | None
    computational_time_seconds: float
    hit_time_limit: bool = False


@dataclass(frozen=True)
class Contribution2SteamPropertyComparison:
    """Steam-property comparison row for Contribution 2 test 6 scenario 2."""

    configuration: str
    turbine: str
    inlet_temperature: float | None
    inlet_pressure: float | None
    outlet_pressure: float | None
    real_isentropic_enthalpy_change: float | None
    model_isentropic_enthalpy_change: float | None
    iapws_power_generation: float
    model_power_generation: float


@dataclass(frozen=True)
class Contribution2BestConfiguration:
    """Best configuration row for Contribution 2 case study 2."""

    scenario: str
    integrates_hot_oil_and_fsr: bool
    microgrid: bool
    vhp_pressure: float
    vhp_temperature: float
    steam_mains: tuple[str, ...]
    pressures: tuple[float, ...]
    temperatures: tuple[float, ...]
    process_steam_use: tuple[float, ...]
    flash_steam: tuple[float | None, ...]
    process_steam_generation: tuple[float | None, ...]
    utility_steam_generation: float
    boiler_flowrate: float | None
    hrsg_flowrate: float
    hot_oil_system_load: float | None
    fuel_consumption: float
    power_generation: float
    steam_turbine_power: float
    gas_turbine_power: float
    operating_cost: float
    fuel_cost: float
    hot_oil_operating_cost: float | None
    power_revenue: float | None
    maintenance_cost: float
    capital_cost: float
    total_cost: float


def _contribution2_scenario_results(
    test_number: int,
    scenario: int,
    baron_found: float,
    baron_possible: float,
    baron_time: float,
    smilp_found: float,
    smilp_time: float,
    bilevel_found: float,
    bilevel_possible: float,
    bilevel_time: float,
    *,
    baron_hit_time_limit: bool = False,
) -> tuple[Contribution2ComputationalResult, ...]:
    return (
        Contribution2ComputationalResult(
            test_number=test_number,
            scenario=scenario,
            method="baron",
            best_solution_found=baron_found,
            best_possible=baron_possible,
            computational_time_seconds=baron_time,
            hit_time_limit=baron_hit_time_limit,
        ),
        Contribution2ComputationalResult(
            test_number=test_number,
            scenario=scenario,
            method="s-milp",
            best_solution_found=smilp_found,
            best_possible=None,
            computational_time_seconds=smilp_time,
        ),
        Contribution2ComputationalResult(
            test_number=test_number,
            scenario=scenario,
            method="bilevel",
            best_solution_found=bilevel_found,
            best_possible=bilevel_possible,
            computational_time_seconds=bilevel_time,
        ),
    )


STYLE_CASE_STUDY_1_STEAM_TARGETS: tuple[StyleSteamSystemTarget, ...] = (
    StyleSteamSystemTarget(
        case_study="case-study-1",
        scenario="varbanov-2005",
        utility_steam_temperature=503.0,
        boiler_flowrate=93.324,
        letdown_flowrate=16.645,
        power_generation=4.762,
        power_generation_per_boiler_flow=0.051,
    ),
    StyleSteamSystemTarget(
        case_study="case-study-1",
        scenario="authors",
        utility_steam_temperature=471.0,
        boiler_flowrate=107.140,
        letdown_flowrate=0.036,
        power_generation=8.364,
        power_generation_per_boiler_flow=0.078,
    ),
)


STYLE_CASE_STUDY_1_HOT_OIL_RESULTS: tuple[StyleHotOilDesignResult, ...] = (
    StyleHotOilDesignResult(
        case_study="case-study-1",
        scenario="hot-oil-and-additional-steam-main",
        mp_pressure=15.2,
        lp_pressure=2.7,
        boiler_flowrate=87.22,
        power_generation=9.35,
        boiler_fuel_cost=3.01,
        hot_oil_fuel_cost=0.65,
        power_cost=2.86,
        cooling_cost=0.11,
        treated_water_cost=0.02,
        total_operating_cost=6.64,
        boiler_capital_cost=3.99,
        hot_oil_capital_cost=0.33,
        steam_turbine_capital_cost=0.43,
        deaerator_capital_cost=0.06,
        total_capital_cost=4.83,
        total_annualized_cost=11.47,
    ),
    StyleHotOilDesignResult(
        case_study="case-study-1",
        scenario="hot-oil",
        mp_pressure=18.8,
        lp_pressure=2.7,
        boiler_flowrate=75.90,
        power_generation=7.38,
        boiler_fuel_cost=2.59,
        hot_oil_fuel_cost=1.22,
        power_cost=3.18,
        cooling_cost=0.11,
        treated_water_cost=0.02,
        total_operating_cost=7.12,
        boiler_capital_cost=3.58,
        hot_oil_capital_cost=0.56,
        steam_turbine_capital_cost=0.35,
        deaerator_capital_cost=0.06,
        total_capital_cost=4.55,
        total_annualized_cost=11.67,
    ),
)


CONTRIBUTION2_MODEL_STATISTICS: tuple[Contribution2ModelStatistic, ...] = (
    Contribution2ModelStatistic(
        test_number=1,
        reference="Varbanov et al. (2005)",
        steam_mains=2,
        power_demand=25.0,
        integrates_hot_oil_and_fsr=False,
        variable_count=1327,
        binary_count=113,
        equation_count=1331,
    ),
    Contribution2ModelStatistic(
        test_number=2,
        reference="Varbanov et al. (2005)",
        steam_mains=2,
        power_demand=25.0,
        integrates_hot_oil_and_fsr=True,
        variable_count=1544,
        binary_count=141,
        equation_count=1485,
    ),
    Contribution2ModelStatistic(
        test_number=3,
        reference="Varbanov et al. (2005)",
        steam_mains=3,
        power_demand=25.0,
        integrates_hot_oil_and_fsr=False,
        variable_count=1805,
        binary_count=132,
        equation_count=1588,
    ),
    Contribution2ModelStatistic(
        test_number=4,
        reference="Varbanov et al. (2005)",
        steam_mains=3,
        power_demand=25.0,
        integrates_hot_oil_and_fsr=True,
        variable_count=2106,
        binary_count=168,
        equation_count=1789,
    ),
    Contribution2ModelStatistic(
        test_number=5,
        reference="Sun et al. (2015)",
        steam_mains=3,
        power_demand=40.0,
        integrates_hot_oil_and_fsr=False,
        variable_count=8165,
        binary_count=512,
        equation_count=5816,
    ),
    Contribution2ModelStatistic(
        test_number=6,
        reference="Sun et al. (2015)",
        steam_mains=3,
        power_demand=40.0,
        integrates_hot_oil_and_fsr=True,
        variable_count=9550,
        binary_count=709,
        equation_count=6879,
    ),
    Contribution2ModelStatistic(
        test_number=7,
        reference="Sun et al. (2015)",
        steam_mains=4,
        power_demand=40.0,
        integrates_hot_oil_and_fsr=False,
        variable_count=10404,
        binary_count=542,
        equation_count=6340,
    ),
    Contribution2ModelStatistic(
        test_number=8,
        reference="Sun et al. (2015)",
        steam_mains=4,
        power_demand=40.0,
        integrates_hot_oil_and_fsr=True,
        variable_count=11123,
        binary_count=757,
        equation_count=7522,
    ),
    Contribution2ModelStatistic(
        test_number=9,
        reference="Oluleye (2015)",
        steam_mains=3,
        power_demand=15.0,
        integrates_hot_oil_and_fsr=False,
        variable_count=16048,
        binary_count=957,
        equation_count=10713,
    ),
    Contribution2ModelStatistic(
        test_number=10,
        reference="Oluleye (2015)",
        steam_mains=3,
        power_demand=15.0,
        integrates_hot_oil_and_fsr=True,
        variable_count=18457,
        binary_count=1354,
        equation_count=12147,
    ),
    Contribution2ModelStatistic(
        test_number=11,
        reference="Oluleye (2015)",
        steam_mains=4,
        power_demand=15.0,
        integrates_hot_oil_and_fsr=False,
        variable_count=20080,
        binary_count=1107,
        equation_count=11282,
    ),
    Contribution2ModelStatistic(
        test_number=12,
        reference="Oluleye (2015)",
        steam_mains=4,
        power_demand=15.0,
        integrates_hot_oil_and_fsr=True,
        variable_count=21817,
        binary_count=1442,
        equation_count=13561,
    ),
)


CONTRIBUTION2_COMPUTATIONAL_RESULTS: tuple[Contribution2ComputationalResult, ...] = (
    *_contribution2_scenario_results(
        1, 1, 30.487, 30.456, 319.1, 30.090, 31.2, 30.487, 30.456, 190.2
    ),
    *_contribution2_scenario_results(
        1, 2, 27.638, 27.610, 224.8, 28.651, 33.1, 27.641, 27.610, 106.7
    ),
    *_contribution2_scenario_results(
        2, 1, 24.989, 24.974, 612.3, 25.479, 32.4, 24.989, 24.963, 307.1
    ),
    *_contribution2_scenario_results(
        2, 2, 24.901, 24.876, 497.4, 24.832, 30.2, 24.901, 24.874, 382.2
    ),
    *_contribution2_scenario_results(
        3, 1, 27.182, 27.082, 5631.2, 28.025, 23.4, 27.182, 27.081, 515.0
    ),
    *_contribution2_scenario_results(
        3, 2, 25.514, 26.489, 6482.1, 26.717, 26.5, 25.511, 25.489, 789.1
    ),
    *_contribution2_scenario_results(
        4, 1, 24.164, 24.140, 5144.2, 25.201, 38.1, 24.164, 24.138, 877.3
    ),
    *_contribution2_scenario_results(
        4, 2, 22.919, 22.896, 8930.7, 23.927, 33.5, 22.919, 22.897, 959.1
    ),
    *_contribution2_scenario_results(
        5,
        1,
        66.993,
        34.506,
        20000.0,
        66.380,
        77.8,
        66.738,
        63.047,
        1716.3,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        5,
        2,
        65.593,
        37.118,
        20000.0,
        64.460,
        102.7,
        64.863,
        60.211,
        1643.2,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        6,
        1,
        55.395,
        31.540,
        20000.0,
        56.010,
        104.5,
        55.167,
        54.271,
        2120.2,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        6,
        2,
        54.859,
        30.848,
        20000.0,
        54.718,
        85.3,
        53.891,
        52.659,
        2613.3,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        7,
        1,
        66.002,
        32.914,
        20000.0,
        65.481,
        81.4,
        65.136,
        62.742,
        2124.1,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        7,
        2,
        64.657,
        31.156,
        20000.0,
        63.980,
        94.3,
        64.221,
        62.192,
        2350.5,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        8,
        1,
        57.418,
        30.695,
        20000.0,
        56.178,
        98.1,
        55.289,
        54.223,
        2410.3,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        8,
        2,
        56.283,
        29.286,
        20000.0,
        54.901,
        101.3,
        53.844,
        52.857,
        2603.2,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        9,
        1,
        12.301,
        9.281,
        20000.0,
        12.386,
        61.5,
        12.160,
        10.020,
        1442.1,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        9,
        2,
        11.667,
        8.431,
        20000.0,
        12.351,
        58.7,
        11.650,
        9.924,
        1541.2,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        10,
        1,
        11.981,
        9.059,
        20000.0,
        12.303,
        142.2,
        11.891,
        10.247,
        1829.8,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        10,
        2,
        12.315,
        8.281,
        20000.0,
        12.112,
        420.3,
        11.405,
        9.987,
        1951.7,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        11,
        1,
        11.890,
        8.592,
        20000.0,
        12.103,
        58.1,
        11.788,
        10.068,
        2130.9,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        11,
        2,
        11.715,
        8.658,
        20000.0,
        11.781,
        62.1,
        11.475,
        10.504,
        2411.3,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        12,
        1,
        11.981,
        8.276,
        20000.0,
        12.012,
        145.2,
        11.842,
        9.440,
        2511.3,
        baron_hit_time_limit=True,
    ),
    *_contribution2_scenario_results(
        12,
        2,
        11.738,
        7.414,
        20000.0,
        11.624,
        306.9,
        11.252,
        9.235,
        2621.2,
        baron_hit_time_limit=True,
    ),
)


CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS: tuple[
    Contribution2SteamPropertyComparison,
    ...,
] = (
    Contribution2SteamPropertyComparison(
        configuration="best-obtained-configuration",
        turbine="VHP-ST 1",
        inlet_temperature=570.0,
        inlet_pressure=100.0,
        outlet_pressure=20.0,
        real_isentropic_enthalpy_change=0.1385,
        model_isentropic_enthalpy_change=0.1367,
        iapws_power_generation=10.29,
        model_power_generation=10.15,
    ),
    Contribution2SteamPropertyComparison(
        configuration="best-obtained-configuration",
        turbine="BP-ST 1",
        inlet_temperature=295.5,
        inlet_pressure=20.0,
        outlet_pressure=2.7,
        real_isentropic_enthalpy_change=0.1126,
        model_isentropic_enthalpy_change=0.1152,
        iapws_power_generation=1.22,
        model_power_generation=1.26,
    ),
    Contribution2SteamPropertyComparison(
        configuration="best-obtained-configuration",
        turbine="total",
        inlet_temperature=None,
        inlet_pressure=None,
        outlet_pressure=None,
        real_isentropic_enthalpy_change=None,
        model_isentropic_enthalpy_change=None,
        iapws_power_generation=11.51,
        model_power_generation=11.41,
    ),
    Contribution2SteamPropertyComparison(
        configuration="fixed-steam-main-pressures",
        turbine="VHP-ST 1",
        inlet_temperature=570.0,
        inlet_pressure=100.0,
        outlet_pressure=20.0,
        real_isentropic_enthalpy_change=0.1385,
        model_isentropic_enthalpy_change=0.1367,
        iapws_power_generation=9.45,
        model_power_generation=9.32,
    ),
    Contribution2SteamPropertyComparison(
        configuration="fixed-steam-main-pressures",
        turbine="BP-ST 1",
        inlet_temperature=267.0,
        inlet_pressure=14.0,
        outlet_pressure=2.7,
        real_isentropic_enthalpy_change=0.0915,
        model_isentropic_enthalpy_change=0.0936,
        iapws_power_generation=1.16,
        model_power_generation=1.19,
    ),
    Contribution2SteamPropertyComparison(
        configuration="fixed-steam-main-pressures",
        turbine="total",
        inlet_temperature=None,
        inlet_pressure=None,
        outlet_pressure=None,
        real_isentropic_enthalpy_change=None,
        model_isentropic_enthalpy_change=None,
        iapws_power_generation=10.61,
        model_power_generation=10.51,
    ),
)


CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS: tuple[
    Contribution2BestConfiguration,
    ...,
] = (
    Contribution2BestConfiguration(
        scenario="utility-system-stand-alone",
        integrates_hot_oil_and_fsr=False,
        microgrid=False,
        vhp_pressure=100.0,
        vhp_temperature=570.0,
        steam_mains=("HP", "MP", "LP"),
        pressures=(37.8, 12.3, 2.7),
        temperatures=(442.6, 288.2, 150.0),
        process_steam_use=(104.3, 155.6, 103.9),
        flash_steam=(None, None, None),
        process_steam_generation=(None, 42.3, 153.8),
        utility_steam_generation=217.78,
        boiler_flowrate=128.76,
        hrsg_flowrate=89.02,
        hot_oil_system_load=None,
        fuel_consumption=239.97,
        power_generation=41.67,
        steam_turbine_power=20.89,
        gas_turbine_power=20.78,
        operating_cost=52.83,
        fuel_cost=50.60,
        hot_oil_operating_cost=None,
        power_revenue=None,
        maintenance_cost=3.53,
        capital_cost=10.38,
        total_cost=66.74,
    ),
    Contribution2BestConfiguration(
        scenario="utility-system-microgrid",
        integrates_hot_oil_and_fsr=False,
        microgrid=True,
        vhp_pressure=100.0,
        vhp_temperature=570.0,
        steam_mains=("HP", "MP", "LP"),
        pressures=(37.8, 12.3, 2.7),
        temperatures=(441.3, 285.1, 150.0),
        process_steam_use=(104.2, 155.6, 103.9),
        flash_steam=(None, None, None),
        process_steam_generation=(None, 42.4, 153.7),
        utility_steam_generation=217.78,
        boiler_flowrate=115.45,
        hrsg_flowrate=102.33,
        hot_oil_system_load=None,
        fuel_consumption=245.04,
        power_generation=46.67,
        steam_turbine_power=20.88,
        gas_turbine_power=25.79,
        operating_cost=50.49,
        fuel_cost=51.78,
        hot_oil_operating_cost=None,
        power_revenue=-3.50,
        maintenance_cost=3.59,
        capital_cost=10.78,
        total_cost=64.86,
    ),
    Contribution2BestConfiguration(
        scenario="hot-oil-fsr-stand-alone",
        integrates_hot_oil_and_fsr=True,
        microgrid=False,
        vhp_pressure=100.0,
        vhp_temperature=570.0,
        steam_mains=("MP", "LP"),
        pressures=(14.0, 2.7),
        temperatures=(273.1, 150.0),
        process_steam_use=(165.77, 83.28),
        flash_steam=(None, 21.04),
        process_steam_generation=(76.4, 118.5),
        utility_steam_generation=137.09,
        boiler_flowrate=None,
        hrsg_flowrate=89.438,
        hot_oil_system_load=58.16,
        fuel_consumption=121.96,
        power_generation=41.67,
        steam_turbine_power=11.02,
        gas_turbine_power=30.65,
        operating_cost=43.71,
        fuel_cost=25.96,
        hot_oil_operating_cost=13.81,
        power_revenue=None,
        maintenance_cost=2.46,
        capital_cost=8.99,
        total_cost=55.17,
    ),
    Contribution2BestConfiguration(
        scenario="hot-oil-fsr-microgrid",
        integrates_hot_oil_and_fsr=True,
        microgrid=True,
        vhp_pressure=100.0,
        vhp_temperature=570.0,
        steam_mains=("MP", "LP"),
        pressures=(20.0, 2.7),
        temperatures=(295.5, 150.0),
        process_steam_use=(181.21, 74.87),
        flash_steam=(None, 29.62),
        process_steam_generation=(100.4, 93.0),
        utility_steam_generation=136.67,
        boiler_flowrate=None,
        hrsg_flowrate=136.67,
        hot_oil_system_load=51.86,
        fuel_consumption=175.03,
        power_generation=46.67,
        steam_turbine_power=11.41,
        gas_turbine_power=35.26,
        operating_cost=41.66,
        fuel_cost=29.10,
        hot_oil_operating_cost=13.81,
        power_revenue=-3.50,
        maintenance_cost=2.63,
        capital_cost=9.60,
        total_cost=53.89,
    ),
)


STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS: tuple[
    StyleGasTurbineFullLoadCoefficient,
    ...,
] = (
    StyleGasTurbineFullLoadCoefficient(
        turbine_type="industrial",
        full_load_a=2.5948,
        full_load_b=30093.0,
        air_flow_c=0.0028,
        air_flow_d=18.444,
    ),
    StyleGasTurbineFullLoadCoefficient(
        turbine_type="aeroderivative",
        full_load_a=2.1816,
        full_load_b=10002.0,
        air_flow_c=0.0029,
        air_flow_d=5.538,
    ),
)


STYLE_GAS_TURBINE_AMBIENT_CORRECTION = StyleGasTurbineAmbientCorrection(
    temperature_power_e=1.02,
    temperature_power_f=1.33e-3,
    temperature_efficiency_g=1.1,
    temperature_efficiency_h=6.66e-3,
)


STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS: tuple[
    StyleGasTurbinePartLoadCoefficient,
    ...,
] = (
    StyleGasTurbinePartLoadCoefficient(
        fuel="natural-gas",
        part_load_a=0.152,
        part_load_b=-0.00142,
    ),
    StyleGasTurbinePartLoadCoefficient(
        fuel="distillate-oil",
        part_load_a=0.144,
        part_load_b=-0.00153,
    ),
)


STYLE_CASE_STUDY_2_SITE_CONFIG = StyleSiteConfig(
    case_study="case-study-2",
    power_demand=40.0,
    max_power_export=10.0,
    operating_hours=8600.0,
    interest_rate_percent=8.0,
    plant_life_years=25.0,
    capital_installation_factor=4.0,
    cooling_water_temperature_rise=10.0,
    boiler_feedwater_temperature=120.0,
    vhp_pressure=100.0,
)


def _case_study_2_resource(
    name: str,
    lower_heating_value: float | None,
    unit_cost: float,
    cost_unit: str = "eur_per_mwh",
) -> StyleResource:
    return StyleResource(
        case_study="case-study-2",
        name=name,
        lower_heating_value=lower_heating_value,
        unit_cost=unit_cost,
        cost_unit=cost_unit,
    )


STYLE_CASE_STUDY_2_RESOURCES: tuple[StyleResource, ...] = (
    _case_study_2_resource("natural-gas", 13.08, 24.30),
    _case_study_2_resource("distillate-oil", 11.28, 39.65),
    _case_study_2_resource("fuel-gas", 13.03, 23.87),
    _case_study_2_resource("fuel-oil", 10.83, 39.40),
    _case_study_2_resource("hot-oil", None, 30.40),
    _case_study_2_resource("electricity-import", None, 88.65),
    _case_study_2_resource("electricity-export", None, 79.79),
    _case_study_2_resource("cooling-water", None, 1.230),
    _case_study_2_resource("treated-water", None, 0.301, "eur_per_tonne"),
)


def _case_study_2_equipment_cost(
    equipment_type: str,
    subtype: str,
    size_variable: str,
    size_unit: str,
    variable_cost: float,
    fixed_cost: float,
    range_lower: float | None,
    range_upper: float | None,
    reference: str,
) -> StyleEquipmentCostCoefficient:
    return StyleEquipmentCostCoefficient(
        case_study="case-study-2",
        equipment_type=equipment_type,
        subtype=subtype,
        size_variable=size_variable,
        size_unit=size_unit,
        variable_cost=variable_cost,
        fixed_cost=fixed_cost,
        range_lower=range_lower,
        range_upper=range_upper,
        reference=reference,
    )


STYLE_CASE_STUDY_2_EQUIPMENT_COSTS: tuple[
    StyleEquipmentCostCoefficient,
    ...
] = (
    _case_study_2_equipment_cost(
        "boiler",
        "packaged",
        "boiler_steam_flow",
        "t_per_h",
        46432.32,
        318715.66,
        50.0,
        350.0,
        "Smith (2016)",
    ),
    _case_study_2_equipment_cost(
        "boiler",
        "field-erected",
        "boiler_steam_flow",
        "t_per_h",
        57059.40,
        843282.30,
        20.0,
        154.2,
        "Smith (2016)",
    ),
    _case_study_2_equipment_cost(
        "boiler",
        "field-erected",
        "boiler_steam_flow",
        "t_per_h",
        40411.71,
        3948425.00,
        154.2,
        800.0,
        "Smith (2016)",
    ),
    _case_study_2_equipment_cost(
        "steam-turbine",
        "all",
        "steam_turbine_power",
        "mw",
        345101.63,
        44057.43,
        1.0,
        200.0,
        "Fleiter et al. (2016)",
    ),
    _case_study_2_equipment_cost(
        "gas-turbine",
        "aeroderivative",
        "gas_turbine_power",
        "mw",
        417061.85,
        764213.50,
        2.0,
        13.1,
        "Pauschert (2009)",
    ),
    _case_study_2_equipment_cost(
        "gas-turbine",
        "aeroderivative",
        "gas_turbine_power",
        "mw",
        299924.77,
        2497065.00,
        13.1,
        51.0,
        "Pauschert (2009)",
    ),
    _case_study_2_equipment_cost(
        "gas-turbine",
        "industrial",
        "gas_turbine_power",
        "mw",
        282115.02,
        1463097.00,
        6.0,
        34.1,
        "Pauschert (2009)",
    ),
    _case_study_2_equipment_cost(
        "gas-turbine",
        "industrial",
        "gas_turbine_power",
        "mw",
        204104.04,
        4439144.00,
        34.1,
        125.0,
        "Pauschert (2009)",
    ),
    _case_study_2_equipment_cost(
        "hrsg",
        "all",
        "hrsg_exhaust_flow",
        "t_per_h",
        2894.08,
        266.54,
        None,
        85.0,
        "Luo et al. (2014)",
    ),
    _case_study_2_equipment_cost(
        "hrsg",
        "all",
        "hrsg_exhaust_flow",
        "t_per_h",
        22895.56,
        135.33,
        85.0,
        None,
        "Luo et al. (2014)",
    ),
    _case_study_2_equipment_cost(
        "hot-oil-furnace",
        "all",
        "hot_oil_heat_load",
        "mw",
        44447.73,
        403443.62,
        5.0,
        60.0,
        "Towler and Sinnott (2013)",
    ),
)


def _case_study_2_stream(
    process: str,
    name: str,
    stream_type: str,
    supply_temperature: float,
    target_temperature: float,
    heat_load: float,
    minimum_temperature_difference: float,
) -> tuple[str, Stream]:
    _require_text(process, "process")
    _require_text(name, "stream name")
    normalized_type = stream_type.strip().lower()
    if normalized_type not in {"hot", "cold"}:
        raise ValueError("stream_type must be 'hot' or 'cold'")
    _require_positive(heat_load, "heat_load")
    _require_non_negative(
        minimum_temperature_difference,
        "minimum_temperature_difference",
    )
    stream = Stream(
        name=name,
        t_supply=supply_temperature,
        t_target=target_temperature,
        dt_cont=0.5 * minimum_temperature_difference,
        heat_flow=heat_load,
        is_process_stream=True,
    )
    if stream.type.lower() != normalized_type:
        raise ValueError(f"stream {name!r} temperatures do not match {stream_type!r}")
    return process, stream


def _add_stream_to_zone(zone: Zone, stream: Stream) -> None:
    if stream.type == "Hot":
        zone.hot_streams.add(stream)
        return
    if stream.type == "Cold":
        zone.cold_streams.add(stream)
        return
    raise ValueError(f"unsupported process stream type {stream.type!r}")


def _case_study_2_total_site_zone(
    stream_rows: tuple[tuple[str, Stream], ...],
) -> Zone:
    site = Zone(name="case-study-2")
    subzones: dict[str, Zone] = {}
    for process, stream in stream_rows:
        subzone = subzones.get(process)
        if subzone is None:
            subzone = Zone(name=process, parent_zone=site)
            subzones[process] = subzone
        _add_stream_to_zone(subzone, stream)
    for subzone in subzones.values():
        site.add_zone(subzone)
    site.import_hot_and_cold_streams_from_sub_zones()
    return site


_STYLE_CASE_STUDY_2_STREAM_ROWS: tuple[tuple[str, Stream], ...] = (
    _case_study_2_stream("A", "A-1", "hot", 300.0, 280.0, 30.000, 15.0),
    _case_study_2_stream("A", "A-2", "hot", 148.0, 135.0, 10.000, 15.0),
    _case_study_2_stream("A", "A-3", "hot", 135.0, 110.0, 20.000, 15.0),
    _case_study_2_stream("A", "A-4", "hot", 110.0, 100.0, 10.000, 15.0),
    _case_study_2_stream("B", "B-1", "hot", 270.0, 260.0, 10.000, 5.0),
    _case_study_2_stream("B", "B-2", "hot", 260.0, 241.0, 10.000, 5.0),
    _case_study_2_stream("B", "B-3", "hot", 241.0, 240.0, 20.000, 5.0),
    _case_study_2_stream("B", "B-4", "hot", 240.0, 220.0, 10.000, 5.0),
    _case_study_2_stream("B", "B-5", "hot", 220.0, 200.0, 5.000, 5.0),
    _case_study_2_stream("B", "B-6", "hot", 200.0, 150.0, 5.000, 5.0),
    _case_study_2_stream("B", "B-7", "hot", 150.0, 135.0, 10.000, 5.0),
    _case_study_2_stream("B", "B-8", "hot", 135.0, 90.0, 10.000, 5.0),
    _case_study_2_stream("C", "C-1", "cold", 169.0, 174.0, 10.000, 15.0),
    _case_study_2_stream("C", "C-2", "cold", 168.0, 169.0, 10.000, 15.0),
    _case_study_2_stream("C", "C-3", "cold", 159.0, 168.0, 10.000, 15.0),
    _case_study_2_stream("C", "C-4", "hot", 179.0, 160.0, 5.000, 15.0),
    _case_study_2_stream("C", "C-5", "hot", 160.0, 150.0, 15.000, 15.0),
    _case_study_2_stream("C", "C-6", "hot", 150.0, 135.0, 5.000, 15.0),
    _case_study_2_stream("C", "C-7", "hot", 135.0, 90.0, 5.000, 15.0),
    _case_study_2_stream("C", "C-8", "hot", 90.0, 85.0, 8.000, 15.0),
    _case_study_2_stream("C", "C-9", "hot", 85.0, 84.0, 12.000, 15.0),
    _case_study_2_stream("D", "D-1", "cold", 209.0, 210.0, 20.000, 5.0),
    _case_study_2_stream("D", "D-2", "cold", 149.0, 150.0, 20.000, 5.0),
    _case_study_2_stream("D", "D-3", "cold", 104.0, 105.0, 30.000, 5.0),
    _case_study_2_stream("D", "D-4", "hot", 119.0, 118.0, 20.000, 5.0),
    _case_study_2_stream("D", "D-5", "hot", 101.0, 100.0, 30.000, 5.0),
    _case_study_2_stream("D", "D-6", "hot", 95.0, 94.0, 20.000, 5.0),
    _case_study_2_stream("E", "E-1", "cold", 235.0, 237.0, 5.714, 10.0),
    _case_study_2_stream("E", "E-2", "cold", 230.0, 235.0, 16.104, 10.0),
    _case_study_2_stream("E", "E-3", "cold", 180.0, 230.0, 18.182, 10.0),
    _case_study_2_stream("E", "E-4", "cold", 160.0, 180.0, 30.000, 10.0),
    _case_study_2_stream("E", "E-5", "cold", 110.0, 160.0, 20.000, 10.0),
    _case_study_2_stream("E", "E-6", "cold", 95.0, 110.0, 5.000, 10.0),
    _case_study_2_stream("E", "E-7", "cold", 90.0, 95.0, 25.000, 10.0),
    _case_study_2_stream("E", "E-8", "hot", 110.0, 90.0, 40.000, 10.0),
    _case_study_2_stream("E", "E-9", "hot", 90.0, 80.0, 20.000, 10.0),
)

STYLE_CASE_STUDY_2_STREAMS = StreamCollection(
    [stream for _, stream in _STYLE_CASE_STUDY_2_STREAM_ROWS],
)
STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE = _case_study_2_total_site_zone(
    _STYLE_CASE_STUDY_2_STREAM_ROWS,
)


STYLE_CASE_STUDY_2_RESULTS: tuple[StyleBenchmarkResult, ...] = (
    StyleBenchmarkResult(
        case_study="case-study-2",
        scenario="conventional",
        utility_steam_flow=299.56,
        fuel_consumption=295.86,
        power_generation=46.67,
        operating_cost=61.14,
        maintenance_cost=1.71,
        capital_cost=13.01,
        total_annualized_cost=75.86,
    ),
    StyleBenchmarkResult(
        case_study="case-study-2",
        scenario="proposed-without-hot-oil",
        utility_steam_flow=239.86,
        fuel_consumption=249.03,
        power_generation=46.67,
        operating_cost=51.04,
        maintenance_cost=1.75,
        capital_cost=11.98,
        total_annualized_cost=64.77,
    ),
    StyleBenchmarkResult(
        case_study="case-study-2",
        scenario="fsr",
        utility_steam_flow=190.96,
        fuel_consumption=210.02,
        power_generation=46.67,
        operating_cost=43.03,
        maintenance_cost=2.00,
        capital_cost=11.07,
        total_annualized_cost=56.10,
    ),
    StyleBenchmarkResult(
        case_study="case-study-2",
        scenario="hot-oil",
        utility_steam_flow=118.84,
        fuel_consumption=218.75,
        power_generation=46.67,
        operating_cost=45.24,
        maintenance_cost=2.71,
        capital_cost=10.90,
        total_annualized_cost=58.85,
    ),
    StyleBenchmarkResult(
        case_study="case-study-2",
        scenario="hot-oil-and-fsr",
        utility_steam_flow=97.46,
        fuel_consumption=201.13,
        power_generation=46.67,
        operating_cost=41.64,
        maintenance_cost=2.79,
        capital_cost=10.29,
        total_annualized_cost=54.72,
    ),
)


def get_style_steam_target(
    case_study: str,
    scenario: str,
) -> StyleSteamSystemTarget:
    """Return a named STYLE steam-system target benchmark."""

    for result in STYLE_CASE_STUDY_1_STEAM_TARGETS:
        if result.case_study == case_study and result.scenario == scenario:
            return result
    raise KeyError(f"No STYLE steam target for {case_study!r}, {scenario!r}.")


def get_style_hot_oil_result(
    case_study: str,
    scenario: str,
) -> StyleHotOilDesignResult:
    """Return a named STYLE hot-oil design benchmark."""

    for result in STYLE_CASE_STUDY_1_HOT_OIL_RESULTS:
        if result.case_study == case_study and result.scenario == scenario:
            return result
    raise KeyError(f"No STYLE hot-oil benchmark for {case_study!r}, {scenario!r}.")


def get_contribution2_model_statistic(
    test_number: int,
) -> Contribution2ModelStatistic:
    """Return model statistics for one Contribution 2 test example."""

    for result in CONTRIBUTION2_MODEL_STATISTICS:
        if result.test_number == test_number:
            return result
    raise KeyError(f"No Contribution 2 model statistic for test {test_number!r}.")


def get_contribution2_computational_result(
    test_number: int,
    scenario: int,
    method: str,
) -> Contribution2ComputationalResult:
    """Return one Contribution 2 computational result."""

    normalized_method = method.lower()
    for result in CONTRIBUTION2_COMPUTATIONAL_RESULTS:
        if (
            result.test_number == test_number
            and result.scenario == scenario
            and result.method == normalized_method
        ):
            return result
    raise KeyError(
        "No Contribution 2 computational result for "
        f"test {test_number!r}, scenario {scenario!r}, method {method!r}."
    )


def get_contribution2_steam_property_comparison(
    configuration: str,
    turbine: str,
) -> Contribution2SteamPropertyComparison:
    """Return one Contribution 2 steam-property comparison row."""

    for result in CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS:
        if result.configuration == configuration and result.turbine == turbine:
            return result
    raise KeyError(
        "No Contribution 2 steam-property comparison for "
        f"configuration {configuration!r}, turbine {turbine!r}."
    )


def get_contribution2_case_study2_best_configuration(
    scenario: str,
) -> Contribution2BestConfiguration:
    """Return one Contribution 2 case study 2 best-configuration row."""

    for result in CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS:
        if result.scenario == scenario:
            return result
    raise KeyError(f"No Contribution 2 case study 2 configuration {scenario!r}.")


def get_style_result(case_study: str, scenario: str) -> StyleBenchmarkResult:
    """Return a named STYLE benchmark result."""

    for result in STYLE_CASE_STUDY_2_RESULTS:
        if result.case_study == case_study and result.scenario == scenario:
            return result
    raise KeyError(f"No STYLE benchmark for {case_study!r}, {scenario!r}.")


__all__ = (
    "Contribution2BestConfiguration",
    "Contribution2ComputationalResult",
    "Contribution2ModelStatistic",
    "Contribution2SteamPropertyComparison",
    "CONTRIBUTION2_CASE_STUDY_2_BEST_CONFIGURATIONS",
    "CONTRIBUTION2_COMPUTATIONAL_RESULTS",
    "CONTRIBUTION2_MODEL_STATISTICS",
    "CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS",
    "STYLE_CASE_STUDY_1_HOT_OIL_RESULTS",
    "STYLE_CASE_STUDY_1_STEAM_TARGETS",
    "STYLE_CASE_STUDY_2_EQUIPMENT_COSTS",
    "STYLE_CASE_STUDY_2_RESOURCES",
    "STYLE_CASE_STUDY_2_RESULTS",
    "STYLE_CASE_STUDY_2_SITE_CONFIG",
    "STYLE_CASE_STUDY_2_STREAMS",
    "STYLE_CASE_STUDY_2_TOTAL_SITE_ZONE",
    "STYLE_GAS_TURBINE_AMBIENT_CORRECTION",
    "STYLE_GAS_TURBINE_FULL_LOAD_COEFFICIENTS",
    "STYLE_GAS_TURBINE_PART_LOAD_COEFFICIENTS",
    "StyleBenchmarkResult",
    "StyleEquipmentCostCoefficient",
    "StyleGasTurbineAmbientCorrection",
    "StyleGasTurbineFullLoadCoefficient",
    "StyleGasTurbinePartLoadCoefficient",
    "StyleHotOilDesignResult",
    "StyleResource",
    "StyleSiteConfig",
    "StyleSteamSystemTarget",
    "get_contribution2_case_study2_best_configuration",
    "get_contribution2_computational_result",
    "get_contribution2_model_statistic",
    "get_contribution2_steam_property_comparison",
    "get_style_hot_oil_result",
    "get_style_result",
    "get_style_steam_target",
)
