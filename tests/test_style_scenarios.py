from __future__ import annotations

import pytest

from OpenUtility.utility_system import (
    UtilitySystemScenario,
    UtilitySystemScenarioCatalog,
    SteamLevelCandidate,
    UtilitySystemModelData,
)
from minimal_utility_system import minimal_utility_benchmark


def test_static_style_scenario_catalog_returns_registered_scenarios() -> None:
    scenario = UtilitySystemScenario(
        case_study="example-site",
        scenario="gas-turbine-with-steam-turbine",
        data=_minimal_data(),
        benchmark=minimal_utility_benchmark(),
    )
    catalog = UtilitySystemScenarioCatalog((scenario,))

    assert catalog.keys() == (("example-site", "gas-turbine-with-steam-turbine"),)
    assert catalog.get("example-site", "gas-turbine-with-steam-turbine") == scenario


def test_static_style_scenario_catalog_rejects_duplicate_keys() -> None:
    scenario = UtilitySystemScenario(
        case_study="example-site",
        scenario="gas-turbine-with-steam-turbine",
        data=_minimal_data(),
    )

    with pytest.raises(ValueError, match="duplicate static utility-system scenario"):
        UtilitySystemScenarioCatalog((scenario, scenario))


def test_static_style_scenario_catalog_reports_missing_key() -> None:
    catalog = UtilitySystemScenarioCatalog(())

    with pytest.raises(KeyError, match="No static utility-system scenario"):
        catalog.get("example-site", "missing")


def _minimal_data() -> UtilitySystemModelData:
    return UtilitySystemModelData(
        steam_mains=("MP",),
        steam_levels=(
            SteamLevelCandidate(
                name="MP_3",
                steam_main="MP",
                temperature=134.0,
                source_heat_available=0.0,
                sink_heat_demand=0.0,
                generation_enthalpy_delta=1.0,
                use_enthalpy_delta=1.0,
            ),
        ),
        power_demand=0.0,
    )
