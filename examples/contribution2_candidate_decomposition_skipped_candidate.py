from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from OpenUtility.style import (
    compatible_bilevel_candidate_assignments,
    format_style_decomposition_trajectory_rows,
    run_static_style_binary_selection_candidate_decomposition,
    scipy_milp_static_style_solver,
    style_binary_selection_candidate_records_from_scenarios,
    style_case_study_2_contribution2_physical_profile_catalog,
    style_decomposition_trajectory_rows,
    style_master_binary_variables,
    build_static_style_model,
)


def trajectory_rows() -> tuple[dict[str, object], ...]:
    calibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog()
    uncalibrated_catalog = style_case_study_2_contribution2_physical_profile_catalog(
        calibrated=False,
    )
    calibrated_scenarios = tuple(calibrated_catalog)
    uncalibrated_scenarios = tuple(uncalibrated_catalog)
    target = calibrated_catalog.get(
        "contribution-2-case-study-2-physical-profile",
        "hot-oil-fsr-microgrid",
    )
    target_model = build_static_style_model(target.data)
    candidates = compatible_bilevel_candidate_assignments(
        style_binary_selection_candidate_records_from_scenarios(
            calibrated_scenarios + uncalibrated_scenarios,
            solve=scipy_milp_static_style_solver(),
            source_label_factory=_source_label_factory(calibrated_scenarios),
        ),
        variable_names=style_master_binary_variables(target_model),
    )
    run = run_static_style_binary_selection_candidate_decomposition(
        target,
        candidates=candidates,
        solve_subproblem=scipy_milp_static_style_solver(),
        max_iterations=2,
    )
    return style_decomposition_trajectory_rows(
        catalog="physical-profile-candidates",
        scenario=target,
        run=run,
    )


def _source_label_factory(calibrated_scenarios: tuple[object, ...]):
    calibrated_scenario_ids = {id(scenario) for scenario in calibrated_scenarios}

    def source_label(scenario: object) -> str:
        source_catalog = (
            "calibrated" if id(scenario) in calibrated_scenario_ids else "uncalibrated"
        )
        return f"{source_catalog}:{scenario.case_study}:{scenario.scenario}"

    return source_label


def trajectory_csv() -> str:
    return format_style_decomposition_trajectory_rows(
        trajectory_rows(),
        output_format="csv",
    )


def main() -> int:
    print(trajectory_csv(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
