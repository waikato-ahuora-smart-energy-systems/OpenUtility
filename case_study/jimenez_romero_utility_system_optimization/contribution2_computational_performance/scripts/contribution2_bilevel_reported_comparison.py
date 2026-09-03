from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    CONTRIBUTION2_COMPUTATIONAL_RESULTS,
)
from case_study.jimenez_romero_utility_system_optimization.contribution2_computational_performance import (
    contribution2_bilevel_benchmark_trajectory_rows,
    contribution2_bilevel_trajectory_comparison_rows,
    contribution2_synthetic_bilevel_decomposition_run,
    format_contribution2_bilevel_trajectory_comparison_rows,
)
from OpenUtility.utility_system import bilevel_decomposition_run_rows


def comparison_rows() -> tuple[dict[str, object], ...]:
    run = contribution2_synthetic_bilevel_decomposition_run(
        test_number=6,
        scenario=2,
    )
    return contribution2_bilevel_trajectory_comparison_rows(
        test_number=6,
        scenario=2,
        actual_rows=bilevel_decomposition_run_rows(run),
        benchmark_rows=contribution2_bilevel_benchmark_trajectory_rows(
            CONTRIBUTION2_COMPUTATIONAL_RESULTS,
        ),
    )


def comparison_csv() -> str:
    return format_contribution2_bilevel_trajectory_comparison_rows(
        comparison_rows(),
        output_format="csv",
    )


def main() -> int:
    print(comparison_csv(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
