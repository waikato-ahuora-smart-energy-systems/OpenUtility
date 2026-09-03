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
            "interpolation_topology": "ordered_part_load_curve",
            "thermodynamic_backend": "coolprop",
            "model_id": "openhpr-export",
            "provenance": {"source": "export"},
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
    )

    assert performance_map.map_id == "hp-map"
    assert performance_map.thermodynamic_backend == "coolprop"
    assert performance_map.points[0].q_sink == pytest.approx(150.0)


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
        interpolation_topology="ordered_part_load_curve",
        thermodynamic_backend="synthetic",
        model_id="linear-cop",
        provenance=provenance,
        points=points,
    )


def _refrigeration_map() -> HprPerformanceMap:
    return HprPerformanceMap(
        schema_version="1.0",
        map_id="ref-map",
        mode="refrigeration",
        units=_units(),
        reference_capacity=100.0,
        interpolation_topology="ordered_part_load_curve",
        thermodynamic_backend="synthetic",
        model_id="linear-cop",
        provenance={"source": "synthetic-test"},
        points=(
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
    )


def _units() -> dict[str, str]:
    return {
        "source_temperature": "degC",
        "sink_temperature": "degC",
        "q_source": "kW",
        "q_sink": "kW",
        "electric_power": "kW",
    }
