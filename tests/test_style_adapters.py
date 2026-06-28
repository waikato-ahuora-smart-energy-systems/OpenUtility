from __future__ import annotations

import pytest

from OpenUtility.style import (
    style_model_data_from_heat_profile,
    style_model_data_from_heat_profile_for_steam_mains,
)
from OpenUtility.thermal import HeatIntervalProfile, TemperatureInterval


def test_style_model_data_from_heat_profile_preserves_interval_heat_loads() -> None:
    intervals = (
        TemperatureInterval(195.0, 185.0),
        TemperatureInterval(185.0, 95.0),
        TemperatureInterval(95.0, 85.0),
    )
    profile = HeatIntervalProfile(
        intervals=intervals,
        source_heat={
            (195.0, 185.0): 100.0,
            (185.0, 95.0): 900.0,
            (95.0, 85.0): 0.0,
        },
        sink_heat={
            (195.0, 185.0): 0.0,
            (185.0, 95.0): 450.0,
            (95.0, 85.0): 50.0,
        },
    )

    data = style_model_data_from_heat_profile(
        profile,
        steam_main="MP",
        power_demand=25.0,
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
    )

    assert data.steam_mains == ("MP",)
    assert [level.name for level in data.steam_levels] == [
        "MP_185",
        "MP_95",
        "MP_85",
    ]
    assert [level.source_heat_available for level in data.steam_levels] == [
        pytest.approx(100.0),
        pytest.approx(900.0),
        pytest.approx(0.0),
    ]
    assert [level.sink_heat_demand for level in data.steam_levels] == [
        pytest.approx(0.0),
        pytest.approx(450.0),
        pytest.approx(50.0),
    ]


def test_style_model_data_from_heat_profile_sets_tight_cumulative_bounds() -> None:
    intervals = (
        TemperatureInterval(195.0, 185.0),
        TemperatureInterval(185.0, 95.0),
        TemperatureInterval(95.0, 85.0),
    )
    profile = HeatIntervalProfile(
        intervals=intervals,
        source_heat={
            (195.0, 185.0): 100.0,
            (185.0, 95.0): 900.0,
            (95.0, 85.0): 0.0,
        },
        sink_heat={
            (195.0, 185.0): 0.0,
            (185.0, 95.0): 450.0,
            (95.0, 85.0): 50.0,
        },
    )

    data = style_model_data_from_heat_profile(
        profile,
        steam_main="MP",
        power_demand=25.0,
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
    )

    assert [level.source_heat_upper_bound for level in data.steam_levels] == [
        pytest.approx(100.0),
        pytest.approx(1000.0),
        pytest.approx(1000.0),
    ]
    assert [level.sink_heat_upper_bound for level in data.steam_levels] == [
        pytest.approx(500.0),
        pytest.approx(500.0),
        pytest.approx(50.0),
    ]


def test_style_model_data_from_heat_profile_for_steam_mains_repeats_interval_candidates_per_main() -> None:
    profile = HeatIntervalProfile(
        intervals=(
            TemperatureInterval(195.0, 185.0),
            TemperatureInterval(185.0, 95.0),
        ),
        source_heat={
            (195.0, 185.0): 100.0,
            (185.0, 95.0): 900.0,
        },
        sink_heat={
            (195.0, 185.0): 0.0,
            (185.0, 95.0): 450.0,
        },
    )

    data = style_model_data_from_heat_profile_for_steam_mains(
        profile,
        steam_mains=("HP", "MP"),
        power_demand=25.0,
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
    )

    assert data.steam_mains == ("HP", "MP")
    assert [level.name for level in data.steam_levels] == [
        "HP_185",
        "HP_95",
        "MP_185",
        "MP_95",
    ]
    assert [level.steam_main for level in data.steam_levels] == [
        "HP",
        "HP",
        "MP",
        "MP",
    ]
    assert [level.source_heat_available for level in data.steam_levels] == (
        pytest.approx([100.0, 900.0, 100.0, 900.0])
    )
    assert [level.sink_heat_demand for level in data.steam_levels] == (
        pytest.approx([0.0, 450.0, 0.0, 450.0])
    )
    assert [level.source_heat_upper_bound for level in data.steam_levels] == (
        pytest.approx([100.0, 1000.0, 100.0, 1000.0])
    )
    assert [level.sink_heat_upper_bound for level in data.steam_levels] == (
        pytest.approx([450.0, 450.0, 450.0, 450.0])
    )


def test_style_model_data_from_heat_profile_for_steam_mains_can_assign_heat_loads_to_one_main() -> None:
    profile = HeatIntervalProfile(
        intervals=(
            TemperatureInterval(195.0, 185.0),
            TemperatureInterval(185.0, 95.0),
        ),
        source_heat={
            (195.0, 185.0): 100.0,
            (185.0, 95.0): 900.0,
        },
        sink_heat={
            (195.0, 185.0): 0.0,
            (185.0, 95.0): 450.0,
        },
    )

    data = style_model_data_from_heat_profile_for_steam_mains(
        profile,
        steam_mains=("HP", "MP"),
        power_demand=25.0,
        generation_enthalpy_delta=2.0,
        use_enthalpy_delta=1.0,
        heat_load_steam_main="MP",
    )

    assert [level.source_heat_available for level in data.steam_levels] == (
        pytest.approx([0.0, 0.0, 100.0, 900.0])
    )
    assert [level.sink_heat_demand for level in data.steam_levels] == (
        pytest.approx([0.0, 0.0, 0.0, 450.0])
    )
    assert [level.source_heat_upper_bound for level in data.steam_levels] == (
        pytest.approx([0.0, 0.0, 100.0, 1000.0])
    )
    assert [level.sink_heat_upper_bound for level in data.steam_levels] == (
        pytest.approx([0.0, 0.0, 450.0, 450.0])
    )


def test_style_model_data_from_heat_profile_for_steam_mains_rejects_unknown_heat_load_main() -> None:
    profile = HeatIntervalProfile(
        intervals=(TemperatureInterval(195.0, 185.0),),
        source_heat={(195.0, 185.0): 100.0},
        sink_heat={(195.0, 185.0): 0.0},
    )

    with pytest.raises(ValueError, match="heat-load steam main"):
        style_model_data_from_heat_profile_for_steam_mains(
            profile,
            steam_mains=("HP", "MP"),
            power_demand=25.0,
            generation_enthalpy_delta=2.0,
            use_enthalpy_delta=1.0,
            heat_load_steam_main="LP",
        )
