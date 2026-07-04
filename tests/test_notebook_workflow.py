from __future__ import annotations

import ast
import json
from pathlib import Path

import matplotlib
import pandas as pd

from case_study.jimenez_romero_utility_system_optimization.benchmarks import (
    get_contribution2_case_study2_best_configuration,
)
from case_study.jimenez_romero_utility_system_optimization.contribution2_computational_performance import (
    CONTRIBUTION2_COMPUTATIONAL_RESULTS,
    CONTRIBUTION2_MODEL_STATISTICS,
    CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS,
    contribution2_bilevel_benchmark_trajectory_rows,
    contribution2_computational_best_method_rows,
    contribution2_computational_method_summary_rows,
    contribution2_computational_result_rows,
    contribution2_model_statistic_rows,
    steam_property_comparison_rows,
)
from case_study.jimenez_romero_utility_system_optimization.contribution2_integrated_hot_oil_fsr import (
    run_contribution2_table_2_9_case_study,
)
from case_study.jimenez_romero_utility_system_optimization.style_stage1_hot_oil_and_steam_mains import (
    STYLE_STAGE1_HOT_OIL_AND_STEAM_MAIN_DESIGN_RESULTS,
    STYLE_STAGE1_STEAM_SYSTEM_TARGETS,
)


matplotlib.use("Agg")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE_STUDY_ROOT = (
    PROJECT_ROOT / "case_study" / "jimenez_romero_utility_system_optimization"
)
NOTEBOOK_PATHS = (
    CASE_STUDY_ROOT
    / "style_stage1_hot_oil_and_steam_mains"
    / "notebooks"
    / "replication.ipynb",
    CASE_STUDY_ROOT
    / "contribution2_integrated_hot_oil_fsr"
    / "notebooks"
    / "replication.ipynb",
    CASE_STUDY_ROOT
    / "contribution2_computational_performance"
    / "notebooks"
    / "replication.ipynb",
)
FORBIDDEN_NOTEBOOK_FILE_CALLS = {
    "open",
    "read_csv",
    "read_excel",
    "read_feather",
    "read_json",
    "read_parquet",
    "read_table",
    "read_text",
    "read_bytes",
}
NOTEBOOK_REPORT_TO_BENCHMARK_FIELD = {
    "utility_steam_flow": "utility_steam_generation",
    "total_annualized_cost": "total_cost",
}


def test_run_contribution2_table_2_9_case_study_returns_notebook_tables() -> None:
    case_study = run_contribution2_table_2_9_case_study(
        apply_fuel_targets=True,
        apply_operating_targets=True,
        solver_time_limit=20.0,
    )

    summary = case_study.summary_table()
    comparison = case_study.comparison_table()
    total_cost = case_study.field_table("total_annualized_cost")

    assert isinstance(summary, pd.DataFrame)
    assert isinstance(comparison, pd.DataFrame)
    assert summary["within_tolerance"].tolist() == [True, True, True, True]
    assert set(total_cost["field"]) == {"total_annualized_cost"}
    assert total_cost["actual"].tolist() == [66.74, 64.86, 55.16, 53.89]


def test_notebook_case_study_plots_field_comparison() -> None:
    case_study = run_contribution2_table_2_9_case_study(
        apply_fuel_targets=True,
        apply_operating_targets=True,
        solver_time_limit=20.0,
    )

    axes = case_study.plot_field_comparison("total_annualized_cost")

    assert axes.get_title() == "total_annualized_cost"
    assert len(axes.patches) == 8


def test_notebook_case_study_plots_summary_deviations() -> None:
    case_study = run_contribution2_table_2_9_case_study(
        apply_fuel_targets=True,
        apply_operating_targets=True,
        solver_time_limit=20.0,
    )

    axes = case_study.plot_summary_deviations()

    assert axes.get_title() == "Maximum absolute deviation by scenario"
    assert len(axes.patches) == 4


def test_case_study_replication_notebooks_execute(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))

    namespaces = [_execute_notebook(path) for path in NOTEBOOK_PATHS]

    integrated_namespace = namespaces[1]
    summary = integrated_namespace["summary"]
    comparison = integrated_namespace["comparison"]

    assert isinstance(summary, pd.DataFrame)
    assert isinstance(comparison, pd.DataFrame)
    assert summary["within_tolerance"].tolist() == [True, True, True, True]
    for row in comparison.to_dict("records"):
        benchmark = get_contribution2_case_study2_best_configuration(row["scenario"])
        benchmark_field = NOTEBOOK_REPORT_TO_BENCHMARK_FIELD.get(
            row["field"],
            row["field"],
        )
        assert row["benchmark"] == getattr(benchmark, benchmark_field)
        assert bool(row["within_tolerance"]) is True

    stage1_namespace = namespaces[0]
    assert isinstance(stage1_namespace["steam_targets"], pd.DataFrame)
    assert isinstance(stage1_namespace["hot_oil_results"], pd.DataFrame)
    pd.testing.assert_frame_equal(
        stage1_namespace["steam_targets"],
        pd.DataFrame(target.__dict__ for target in STYLE_STAGE1_STEAM_SYSTEM_TARGETS),
    )
    pd.testing.assert_frame_equal(
        stage1_namespace["hot_oil_results"],
        pd.DataFrame(
            result.__dict__
            for result in STYLE_STAGE1_HOT_OIL_AND_STEAM_MAIN_DESIGN_RESULTS
        ),
    )

    computational_namespace = namespaces[2]
    assert isinstance(computational_namespace["model_statistics"], pd.DataFrame)
    assert isinstance(computational_namespace["computational_results"], pd.DataFrame)
    assert isinstance(
        computational_namespace["steam_property_comparisons"],
        pd.DataFrame,
    )
    pd.testing.assert_frame_equal(
        computational_namespace["model_statistics"],
        pd.DataFrame(
            contribution2_model_statistic_rows(CONTRIBUTION2_MODEL_STATISTICS)
        ),
    )
    pd.testing.assert_frame_equal(
        computational_namespace["computational_results"],
        pd.DataFrame(
            contribution2_computational_result_rows(CONTRIBUTION2_COMPUTATIONAL_RESULTS)
        ),
    )
    pd.testing.assert_frame_equal(
        computational_namespace["steam_property_comparisons"],
        pd.DataFrame(
            steam_property_comparison_rows(CONTRIBUTION2_STEAM_PROPERTY_COMPARISONS)
        ),
    )
    pd.testing.assert_frame_equal(
        computational_namespace["best_methods"],
        pd.DataFrame(
            contribution2_computational_best_method_rows(
                CONTRIBUTION2_COMPUTATIONAL_RESULTS
            )
        ),
    )
    pd.testing.assert_frame_equal(
        computational_namespace["method_summary"],
        pd.DataFrame(
            contribution2_computational_method_summary_rows(
                CONTRIBUTION2_COMPUTATIONAL_RESULTS
            )
        ),
    )
    pd.testing.assert_frame_equal(
        computational_namespace["bilevel_trajectory"],
        pd.DataFrame(
            contribution2_bilevel_benchmark_trajectory_rows(
                CONTRIBUTION2_COMPUTATIONAL_RESULTS
            )
        ),
    )


def test_case_study_replication_notebooks_do_not_read_generated_outputs() -> None:
    for path in NOTEBOOK_PATHS:
        for source in _notebook_code_sources(path):
            lowered_source = source.lower()
            assert "outputs/" not in lowered_source
            assert ".csv" not in lowered_source
            tree = ast.parse(source, filename=str(path))
            for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
                assert _call_name(call) not in FORBIDDEN_NOTEBOOK_FILE_CALLS


def _execute_notebook(notebook_path: Path) -> dict[str, object]:
    namespace: dict[str, object] = {"__name__": "__main__"}

    for index, source in enumerate(_notebook_code_sources(notebook_path), start=1):
        exec(compile(source, f"{notebook_path}:{index}", "exec"), namespace)

    return namespace


def _notebook_code_sources(notebook_path: Path) -> tuple[str, ...]:
    notebook = json.loads(notebook_path.read_text())
    return tuple(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""
