from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from case_study.jimenez_romero_utility_system_optimization.style_model_builders import (
    style_case_study_2_contribution2_physical_profile_catalog,
)
from OpenUtility.style import (
    bilevel_decomposition_run_rows,
    format_bilevel_decomposition_run_rows,
    pyomo_static_style_solver,
    run_static_style_fixed_assignment_decomposition,
)


def trajectory_rows() -> tuple[dict[str, object], ...]:
    scenario = next(iter(style_case_study_2_contribution2_physical_profile_catalog()))
    run = run_static_style_fixed_assignment_decomposition(
        scenario,
        solve_master=pyomo_static_style_solver("appsi_highs"),
        solve_subproblem=pyomo_static_style_solver("appsi_highs"),
        max_iterations=1,
    )
    return bilevel_decomposition_run_rows(run)


def trajectory_csv() -> str:
    return format_bilevel_decomposition_run_rows(
        trajectory_rows(),
        output_format="csv",
    )


def main() -> int:
    print(trajectory_csv(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
