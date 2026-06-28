from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from OpenUtility.style import (
    bilevel_decomposition_run_rows,
    format_bilevel_decomposition_run_rows,
    run_static_style_fixed_assignment_decomposition,
    scipy_milp_static_style_solver,
    style_case_study_2_contribution2_physical_profile_catalog,
)


def trajectory_rows() -> tuple[dict[str, object], ...]:
    scenario = next(iter(style_case_study_2_contribution2_physical_profile_catalog()))
    run = run_static_style_fixed_assignment_decomposition(
        scenario,
        solve_master=scipy_milp_static_style_solver(),
        solve_subproblem=scipy_milp_static_style_solver(),
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
