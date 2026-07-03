from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import pandas as pd

from case_study.jimenez_romero_utility_system_optimization.contribution2_integrated_hot_oil_fsr import (
    run_contribution2_table_2_9_case_study,
)


matplotlib.use("Agg")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE_STUDY_ROOT = (
    PROJECT_ROOT / "case_study" / "jimenez_romero_utility_system_optimization"
)


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
    notebook_paths = (
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

    namespaces = [_execute_notebook(path) for path in notebook_paths]

    integrated_namespace = namespaces[1]
    summary = integrated_namespace["summary"]
    comparison = integrated_namespace["comparison"]

    assert isinstance(summary, pd.DataFrame)
    assert isinstance(comparison, pd.DataFrame)
    assert summary["within_tolerance"].tolist() == [True, True, True, True]

    stage1_namespace = namespaces[0]
    assert isinstance(stage1_namespace["steam_targets"], pd.DataFrame)
    assert isinstance(stage1_namespace["hot_oil_results"], pd.DataFrame)

    computational_namespace = namespaces[2]
    assert isinstance(computational_namespace["model_statistics"], pd.DataFrame)
    assert isinstance(computational_namespace["computational_results"], pd.DataFrame)
    assert isinstance(
        computational_namespace["steam_property_comparisons"],
        pd.DataFrame,
    )


def _execute_notebook(notebook_path: Path) -> dict[str, object]:
    notebook = json.loads(notebook_path.read_text())
    namespace: dict[str, object] = {"__name__": "__main__"}

    for index, cell in enumerate(notebook["cells"], start=1):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        exec(compile(source, f"{notebook_path}:{index}", "exec"), namespace)

    return namespace
