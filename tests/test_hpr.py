from __future__ import annotations

import pyomo.environ as pyo
import pytest

from OpenUtility.utility_system import (
    EquipmentCost,
    HprCandidate,
    HprPerformanceMap,
    HprPerformancePoint,
    OperatingPeriod,
    SteamLevelCandidate,
    ThermalNode,
    UtilitySystemModelData,
    build_utility_system_model,
    hpr_performance_map_from_mapping,
    solve_utility_system_model_with_pyomo,
)


def test_hpr_performance_map_validates_required_boundary_metadata() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        _heat_pump_map(schema_version="")

    with pytest.raises(ValueError, match="units are missing"):
        _heat_pump_map(units={"q_source": "kW"})

    with pytest.raises(ValueError, match="provenance"):
        _heat_pump_map(provenance={})


def test_hpr_performance_map_decodes_plain_mapping_data() -> None:
    performance_map = hpr_performance_map_from_mapping(
        {
            "schema_version": "1.0",
            "map_id": "hp-map",
            "mode": "heat_pump",
            "units": _units(),
            "reference_capacity": 150.0,
            "reference_capacity_basis": "q_sink",
            "interpolation_topology": "ordered_part_load_curve",
            "thermodynamic_backend": "coolprop",
            "model_id": "openhpr-export",
            "provenance": {"source": "export", "nested": {"case": 1}},
            "cop_convention": "heating",
            "points": [
                {
                    "name": "full",
                    "curve_id": "curve",
                    "source_temperature": 40.0,
                    "sink_temperature": 80.0,
                    "load_fraction": 1.0,
                    "q_source": 100.0,
                    "q_sink": 150.0,
                    "electric_power": 50.0,
                    "cop": 3.0,
                }
            ],
        }
    )

    assert performance_map.map_id == "hp-map"
    assert performance_map.thermodynamic_backend == "coolprop"
    assert performance_map.provenance["nested"] == {"case": 1}
    assert performance_map.points[0].q_sink == pytest.approx(150.0)


def test_hpr_performance_map_decoder_rejects_unknown_keys() -> None:
    payload = _heat_pump_map_payload()
    payload["unexpected"] = True

    with pytest.raises(ValueError, match="unknown keys"):
        hpr_performance_map_from_mapping(payload)


def test_hpr_performance_map_rejects_unknown_schema_version() -> None:
    with pytest.raises(ValueError, match="schema_version"):
        _heat_pump_map(schema_version="1.1")


def test_hpr_performance_map_rejects_incompatible_units_and_cop_convention() -> None:
    with pytest.raises(ValueError, match="source_temperature"):
        _heat_pump_map(units={**_units(), "source_temperature": "K"})

    with pytest.raises(ValueError, match="cop_convention"):
        _heat_pump_map(cop_convention="cooling")


def test_hpr_performance_map_validates_finite_temperatures() -> None:
    with pytest.raises(ValueError, match="source_temperature"):
        HprPerformancePoint(
            name="bad",
            curve_id="curve",
            source_temperature=float("nan"),
            sink_temperature=80.0,
            load_fraction=1.0,
            q_source=100.0,
            q_sink=150.0,
            electric_power=50.0,
        )


def test_hpr_performance_map_validates_energy_balance() -> None:
    with pytest.raises(ValueError, match="q_sink = q_source \\+ electric_power"):
        _heat_pump_map(
            points=(
                HprPerformancePoint(
                    name="bad",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=1.0,
                    q_source=100.0,
                    q_sink=120.0,
                    electric_power=50.0,
                ),
            ),
        )


def test_hpr_performance_map_validates_cop_value_consistency() -> None:
    with pytest.raises(ValueError, match="heating COP"):
        _heat_pump_map(
            points=(
                HprPerformancePoint(
                    name="bad",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=1.0,
                    q_source=100.0,
                    q_sink=150.0,
                    electric_power=50.0,
                    cop=4.0,
                ),
            ),
        )


def test_hpr_performance_map_validates_ordered_curve_contract() -> None:
    with pytest.raises(ValueError, match="source/sink temperature pair"):
        _heat_pump_map(
            points=(
                HprPerformancePoint(
                    name="low",
                    curve_id="curve",
                    source_temperature=35.0,
                    sink_temperature=80.0,
                    load_fraction=0.5,
                    q_source=50.0,
                    q_sink=75.0,
                    electric_power=25.0,
                ),
                HprPerformancePoint(
                    name="high",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=1.0,
                    q_source=100.0,
                    q_sink=150.0,
                    electric_power=50.0,
                ),
            ),
        )

    with pytest.raises(ValueError, match="coordinates"):
        _heat_pump_map(
            points=(
                HprPerformancePoint(
                    name="duplicate-a",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=0.5,
                    q_source=50.0,
                    q_sink=75.0,
                    electric_power=25.0,
                ),
                HprPerformancePoint(
                    name="duplicate-b",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=0.5,
                    q_source=50.0,
                    q_sink=75.0,
                    electric_power=25.0,
                ),
            ),
        )

    with pytest.raises(ValueError, match="strictly increasing"):
        _heat_pump_map(
            points=(
                HprPerformancePoint(
                    name="high",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=1.0,
                    q_source=100.0,
                    q_sink=150.0,
                    electric_power=50.0,
                ),
                HprPerformancePoint(
                    name="low",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=0.5,
                    q_source=50.0,
                    q_sink=75.0,
                    electric_power=25.0,
                ),
            ),
        )


def test_hpr_performance_map_validates_useful_capacity_basis() -> None:
    with pytest.raises(ValueError, match="reference_capacity_basis"):
        _heat_pump_map(reference_capacity_basis="q_source")

    with pytest.raises(ValueError, match="load_fraction \\* reference_capacity"):
        _heat_pump_map(
            points=(
                HprPerformancePoint(
                    name="bad",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=0.5,
                    q_source=60.0,
                    q_sink=90.0,
                    electric_power=30.0,
                ),
            ),
        )


def test_hpr_candidate_validates_node_and_map_references() -> None:
    with pytest.raises(ValueError, match="unknown map"):
        _minimal_data(
            hpr_maps=(),
            hpr_candidates=(
                HprCandidate(
                    name="hp",
                    mode="heat_pump",
                    map_id="missing",
                    source_node="waste",
                    sink_node="heat",
                ),
            ),
        )

    with pytest.raises(ValueError, match="unknown thermal node"):
        _minimal_data(
            hpr_candidates=(
                HprCandidate(
                    name="hp",
                    mode="heat_pump",
                    map_id="hp-map",
                    source_node="missing",
                    sink_node="heat",
                ),
            ),
        )


def test_heat_pump_hpr_is_selected_when_economic() -> None:
    data = _minimal_data()
    model = build_utility_system_model(data)

    status = solve_utility_system_model_with_pyomo(model, "appsi_highs")

    assert status.status == "ok"
    assert status.termination_condition == "optimal"
    assert pyo.value(model.hpr_selected["hp"]) == pytest.approx(1.0)
    assert pyo.value(model.hpr_q_source["hp", "day"]) == pytest.approx(100.0)
    assert pyo.value(model.hpr_q_sink["hp", "day"]) == pytest.approx(150.0)
    assert pyo.value(model.hpr_power["hp", "day"]) == pytest.approx(50.0)
    assert pyo.value(model.node_external_heating["day", "heat"]) == pytest.approx(0.0)


def test_heat_pump_hpr_is_not_selected_when_uneconomic() -> None:
    data = _minimal_data(
        thermal_nodes=(
            ThermalNode("waste", 40.0, "source"),
            ThermalNode("heat", 80.0, "sink", heating_unit_cost=1.0),
        ),
        periods=(
            OperatingPeriod(
                name="day",
                hours=1.0,
                electricity_import_unit_cost=10.0,
                source_heat_available={"waste": 100.0},
                heating_demand={"heat": 150.0},
            ),
        ),
        equipment_costs=(
            EquipmentCost(
                name="hp-cost",
                equipment_type="hpr",
                equipment_name="hp",
                annualization_factor=1.0,
                installation_factor=1.0,
                variable_capital_cost=0.0,
                fixed_capital_cost=1.0,
            ),
        ),
    )
    model = build_utility_system_model(data)

    status = solve_utility_system_model_with_pyomo(model, "appsi_highs")

    assert status.status == "ok"
    assert status.termination_condition == "optimal"
    assert pyo.value(model.hpr_selected["hp"]) == pytest.approx(0.0)
    assert pyo.value(model.node_external_heating["day", "heat"]) == pytest.approx(150.0)


def test_temperature_incompatible_hpr_points_are_rejected() -> None:
    data = _minimal_data(
        periods=(
            OperatingPeriod(
                name="day",
                hours=1.0,
                source_heat_available={"waste": 100.0},
                heating_demand={"heat": 150.0},
                node_temperatures={"heat": 90.0},
            ),
        ),
    )

    with pytest.raises(ValueError, match="temperature-compatible"):
        build_utility_system_model(data)


def test_temperature_matching_uses_temperature_tolerance_not_energy_tolerance() -> None:
    data = _minimal_data(
        periods=(
            OperatingPeriod(
                name="day",
                hours=1.0,
                electricity_import_unit_cost=1.0,
                source_heat_available={"waste": 100.0},
                heating_demand={"heat": 150.0},
                node_temperatures={"heat": 80.25},
            ),
        ),
        hpr_maps=(_heat_pump_map(temperature_match_tolerance=0.5),),
    )

    model = build_utility_system_model(data)
    status = solve_utility_system_model_with_pyomo(model, "appsi_highs")

    assert status.termination_condition == "optimal"
    assert pyo.value(model.hpr_q_sink["hp", "day"]) == pytest.approx(150.0)


def test_refrigeration_hpr_serves_cooling_and_rejects_condenser_heat() -> None:
    data = _minimal_data(
        thermal_nodes=(
            ThermalNode("cold", -5.0, "cooling", cooling_unit_cost=10.0),
            ThermalNode("reject", 35.0, "rejection", rejection_unit_cost=0.1),
        ),
        periods=(
            OperatingPeriod(
                name="day",
                hours=1.0,
                electricity_import_unit_cost=1.0,
                cooling_demand={"cold": 100.0},
                rejection_capacity={"reject": 200.0},
            ),
        ),
        hpr_maps=(_refrigeration_map(),),
        hpr_candidates=(
            HprCandidate(
                name="chiller",
                mode="refrigeration",
                map_id="ref-map",
                source_node="cold",
                rejection_node="reject",
                fixed_capacity=100.0,
            ),
        ),
    )
    model = build_utility_system_model(data)

    status = solve_utility_system_model_with_pyomo(model, "appsi_highs")

    assert status.status == "ok"
    assert status.termination_condition == "optimal"
    assert pyo.value(model.hpr_selected["chiller"]) == pytest.approx(1.0)
    assert pyo.value(model.hpr_q_source["chiller", "day"]) == pytest.approx(100.0)
    assert pyo.value(model.hpr_rejected_heat["chiller", "day"]) == pytest.approx(125.0)
    assert pyo.value(model.node_external_cooling["day", "cold"]) == pytest.approx(0.0)


def test_hpr_equipment_cost_uses_fixed_capacity() -> None:
    data = _minimal_data(
        equipment_costs=(
            EquipmentCost(
                name="hp-cost",
                equipment_type="hpr",
                equipment_name="hp",
                annualization_factor=0.2,
                installation_factor=1.0,
                variable_capital_cost=2.0,
                fixed_capital_cost=10.0,
                variable_maintenance_cost=1.0,
            ),
        ),
    )
    model = build_utility_system_model(data)
    model.hpr_selected["hp"].fix(1.0)

    assert pyo.value(model.equipment_annualized_capital_cost["hp-cost"]) == (
        pytest.approx(62.0)
    )
    assert pyo.value(model.equipment_maintenance_cost["hp-cost"]) == pytest.approx(
        150.0
    )


def test_hpr_fixed_capacity_scales_absolute_map_points() -> None:
    data = _minimal_data(
        periods=(
            OperatingPeriod(
                name="day",
                hours=1.0,
                electricity_import_unit_cost=1.0,
                source_heat_available={"waste": 200.0},
                heating_demand={"heat": 300.0},
            ),
        ),
        hpr_candidates=(
            HprCandidate(
                name="hp",
                mode="heat_pump",
                map_id="hp-map",
                source_node="waste",
                sink_node="heat",
                fixed_capacity=300.0,
            ),
        ),
    )
    model = build_utility_system_model(data)

    status = solve_utility_system_model_with_pyomo(model, "appsi_highs")

    assert status.termination_condition == "optimal"
    assert pyo.value(model.hpr_capacity_scale["hp"]) == pytest.approx(2.0)
    assert pyo.value(model.hpr_q_source["hp", "day"]) == pytest.approx(200.0)
    assert pyo.value(model.hpr_q_sink["hp", "day"]) == pytest.approx(300.0)
    assert pyo.value(model.hpr_power["hp", "day"]) == pytest.approx(100.0)


def test_hpr_minimum_load_and_variable_cost_use_refrigeration_useful_duty() -> None:
    data = _minimal_data(
        thermal_nodes=(
            ThermalNode("cold", -5.0, "cooling", cooling_unit_cost=10.0),
            ThermalNode("reject", 35.0, "rejection", rejection_unit_cost=0.1),
        ),
        periods=(
            OperatingPeriod(
                name="day",
                hours=2.0,
                electricity_import_unit_cost=1.0,
                cooling_demand={"cold": 50.0},
                rejection_capacity={"reject": 200.0},
            ),
        ),
        hpr_maps=(_refrigeration_map(),),
        hpr_candidates=(
            HprCandidate(
                name="chiller",
                mode="refrigeration",
                map_id="ref-map",
                source_node="cold",
                rejection_node="reject",
                fixed_capacity=100.0,
                minimum_load_fraction=0.5,
                variable_operating_cost_per_q_useful=2.0,
            ),
        ),
    )
    model = build_utility_system_model(data)

    status = solve_utility_system_model_with_pyomo(model, "appsi_highs")

    assert status.termination_condition == "optimal"
    assert pyo.value(model.hpr_q_useful["chiller", "day"]) == pytest.approx(50.0)
    assert pyo.value(model.hpr_variable_operating_cost) == pytest.approx(200.0)


def test_ordered_part_load_curve_allows_only_adjacent_point_mixing() -> None:
    data = _minimal_data(
        periods=(
            OperatingPeriod(
                name="day",
                hours=1.0,
                electricity_import_unit_cost=1.0,
                source_heat_available={"waste": 75.0},
                heating_demand={"heat": 112.5},
            ),
        ),
        hpr_maps=(_three_point_heat_pump_map(),),
    )
    model = build_utility_system_model(data)

    model.hpr_selected["hp"].fix(1.0)
    model.hpr_on["hp", "day"].fix(1.0)
    model.hpr_lambda["hp", "day", "low"].fix(0.5)
    model.hpr_lambda["hp", "day", "high"].fix(0.5)

    status = solve_utility_system_model_with_pyomo(model, "appsi_highs")

    assert status.termination_condition == "infeasible"


def test_hpr_electricity_is_currently_an_isolated_period_overlay() -> None:
    data = _minimal_data()
    model = build_utility_system_model(data)

    assert hasattr(model, "electricity_balance")
    assert hasattr(model, "hpr_period_electricity_balance")
    assert hasattr(model, "hpr_grid_power_import")


def _minimal_data(
    *,
    thermal_nodes: tuple[ThermalNode, ...] | None = None,
    periods: tuple[OperatingPeriod, ...] | None = None,
    hpr_maps: tuple[HprPerformanceMap, ...] | None = None,
    hpr_candidates: tuple[HprCandidate, ...] | None = None,
    equipment_costs: tuple[EquipmentCost, ...] = (),
) -> UtilitySystemModelData:
    if thermal_nodes is None:
        thermal_nodes = (
            ThermalNode("waste", 40.0, "source", cooling_unit_cost=1.0),
            ThermalNode("heat", 80.0, "sink", heating_unit_cost=10.0),
        )
    if periods is None:
        periods = (
            OperatingPeriod(
                name="day",
                hours=1.0,
                electricity_import_unit_cost=1.0,
                source_heat_available={"waste": 100.0},
                heating_demand={"heat": 150.0},
            ),
        )
    if hpr_maps is None:
        hpr_maps = (_heat_pump_map(),)
    if hpr_candidates is None:
        hpr_candidates = (
            HprCandidate(
                name="hp",
                mode="heat_pump",
                map_id="hp-map",
                source_node="waste",
                sink_node="heat",
                fixed_capacity=150.0,
            ),
        )
    return UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_100",
                steam_main="MP",
                temperature=100.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
        ),
        power_demand=0.0,
        thermal_nodes=thermal_nodes,
        periods=periods,
        hpr_performance_maps=hpr_maps,
        hpr_candidates=hpr_candidates,
        equipment_costs=equipment_costs,
    )


def _heat_pump_map(
    *,
    schema_version: str = "1.0",
    units: dict[str, str] | None = None,
    provenance: dict[str, str] | None = None,
    reference_capacity_basis: str = "q_sink",
    cop_convention: str = "heating",
    energy_balance_tolerance: float = 1e-6,
    temperature_match_tolerance: float = 1e-6,
    points: tuple[HprPerformancePoint, ...] | None = None,
) -> HprPerformanceMap:
    if units is None:
        units = _units()
    if provenance is None:
        provenance = {"source": "synthetic-test"}
    if points is None:
        points = (
            HprPerformancePoint(
                name="low",
                curve_id="curve",
                source_temperature=40.0,
                sink_temperature=80.0,
                load_fraction=0.5,
                q_source=50.0,
                q_sink=75.0,
                electric_power=25.0,
            ),
            HprPerformancePoint(
                name="high",
                curve_id="curve",
                source_temperature=40.0,
                sink_temperature=80.0,
                load_fraction=1.0,
                q_source=100.0,
                q_sink=150.0,
                electric_power=50.0,
            ),
        )
    return HprPerformanceMap(
        schema_version=schema_version,
        map_id="hp-map",
        mode="heat_pump",
        units=units,
        reference_capacity=150.0,
        reference_capacity_basis=reference_capacity_basis,
        interpolation_topology="ordered_part_load_curve",
        thermodynamic_backend="synthetic",
        model_id="linear-cop",
        provenance=provenance,
        points=points,
        cop_convention=cop_convention,
        energy_balance_tolerance=energy_balance_tolerance,
        temperature_match_tolerance=temperature_match_tolerance,
    )


def _three_point_heat_pump_map() -> HprPerformanceMap:
    return _heat_pump_map(
        points=(
            HprPerformancePoint(
                name="low",
                curve_id="curve",
                source_temperature=40.0,
                sink_temperature=80.0,
                load_fraction=0.25,
                q_source=25.0,
                q_sink=37.5,
                electric_power=12.5,
            ),
            HprPerformancePoint(
                name="mid",
                curve_id="curve",
                source_temperature=40.0,
                sink_temperature=80.0,
                load_fraction=0.5,
                q_source=50.0,
                q_sink=75.0,
                electric_power=25.0,
            ),
            HprPerformancePoint(
                name="high",
                curve_id="curve",
                source_temperature=40.0,
                sink_temperature=80.0,
                load_fraction=1.0,
                q_source=100.0,
                q_sink=150.0,
                electric_power=50.0,
            ),
        ),
    )


def _refrigeration_map() -> HprPerformanceMap:
    return HprPerformanceMap(
        schema_version="1.0",
        map_id="ref-map",
        mode="refrigeration",
        units=_units(),
        reference_capacity=100.0,
        reference_capacity_basis="q_source",
        interpolation_topology="ordered_part_load_curve",
        thermodynamic_backend="synthetic",
        model_id="linear-cop",
        provenance={"source": "synthetic-test"},
        points=(
            HprPerformancePoint(
                name="half",
                curve_id="curve",
                source_temperature=-5.0,
                sink_temperature=35.0,
                load_fraction=0.5,
                q_source=50.0,
                q_sink=62.5,
                electric_power=12.5,
            ),
            HprPerformancePoint(
                name="full",
                curve_id="curve",
                source_temperature=-5.0,
                sink_temperature=35.0,
                load_fraction=1.0,
                q_source=100.0,
                q_sink=125.0,
                electric_power=25.0,
            ),
        ),
        cop_convention="cooling",
    )


def _units() -> dict[str, str]:
    return {
        "source_temperature": "degC",
        "sink_temperature": "degC",
        "q_source": "kW",
        "q_sink": "kW",
        "electric_power": "kW",
    }


def _heat_pump_map_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "map_id": "hp-map",
        "mode": "heat_pump",
        "units": _units(),
        "reference_capacity": 150.0,
        "reference_capacity_basis": "q_sink",
        "interpolation_topology": "ordered_part_load_curve",
        "thermodynamic_backend": "coolprop",
        "model_id": "openhpr-export",
        "provenance": {"source": "export"},
        "cop_convention": "heating",
        "points": [
            {
                "name": "full",
                "curve_id": "curve",
                "source_temperature": 40.0,
                "sink_temperature": 80.0,
                "load_fraction": 1.0,
                "q_source": 100.0,
                "q_sink": 150.0,
                "electric_power": 50.0,
            }
        ],
    }
