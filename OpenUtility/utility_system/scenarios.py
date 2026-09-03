"""Static utility-system scenario catalog helpers."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .runner import UtilitySystemScenario


@dataclass(frozen=True)
class UtilitySystemScenarioCatalog:
    """Immutable lookup catalog for static utility-system scenario definitions."""

    scenarios: tuple[UtilitySystemScenario, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenarios", tuple(self.scenarios))
        seen_keys: set[tuple[str, str]] = set()
        for scenario in self.scenarios:
            key = _scenario_key(scenario)
            if key in seen_keys:
                raise ValueError(
                    "duplicate static utility-system scenario "
                    f"{scenario.case_study!r}, {scenario.scenario!r}"
                )
            seen_keys.add(key)

    def __iter__(self) -> Iterator[UtilitySystemScenario]:
        """Iterate through registered scenarios in catalog order."""

        return iter(self.scenarios)

    def keys(self) -> tuple[tuple[str, str], ...]:
        """Return registered `(case_study, scenario)` keys in catalog order."""

        return tuple(_scenario_key(scenario) for scenario in self.scenarios)

    def get(self, case_study: str, scenario: str) -> UtilitySystemScenario:
        """Return a registered scenario by case identifier and scenario name."""

        for candidate in self.scenarios:
            if candidate.case_study == case_study and candidate.scenario == scenario:
                return candidate
        raise KeyError(
            f"No static utility-system scenario for {case_study!r}, {scenario!r}."
        )


def _scenario_key(scenario: UtilitySystemScenario) -> tuple[str, str]:
    return (scenario.case_study, scenario.scenario)
