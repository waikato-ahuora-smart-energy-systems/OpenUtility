from __future__ import annotations

import json
from pathlib import Path

import matplotlib
import pandas as pd

from OpenUtility import run_thesis_table_2_9_case_study


matplotlib.use("Agg")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_run_thesis_table_2_9_case_study_returns_notebook_tables() -> None:
    case_study = run_thesis_table_2_9_case_study(
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
    case_study = run_thesis_table_2_9_case_study(
        apply_fuel_targets=True,
        apply_operating_targets=True,
        solver_time_limit=20.0,
    )

    axes = case_study.plot_field_comparison("total_annualized_cost")

    assert axes.get_title() == "total_annualized_cost"
    assert len(axes.patches) == 8


def test_notebook_case_study_plots_summary_deviations() -> None:
    case_study = run_thesis_table_2_9_case_study(
        apply_fuel_targets=True,
        apply_operating_targets=True,
        solver_time_limit=20.0,
    )

    axes = case_study.plot_summary_deviations()

    assert axes.get_title() == "Maximum absolute deviation by scenario"
    assert len(axes.patches) == 4


def test_thesis_case_study_example_notebook_executes(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MPLCONFIGDIR", str(tmp_path / "matplotlib"))
    notebook_path = (
        PROJECT_ROOT / "examples" / "notebooks" / "thesis_table_2_9_case_study.ipynb"
    )
    notebook = json.loads(notebook_path.read_text())
    namespace: dict[str, object] = {"__name__": "__main__"}

    for index, cell in enumerate(notebook["cells"], start=1):
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        exec(compile(source, f"{notebook_path}:{index}", "exec"), namespace)

    summary = namespace["summary"]
    comparison = namespace["comparison"]

    assert isinstance(summary, pd.DataFrame)
    assert isinstance(comparison, pd.DataFrame)
    assert summary["within_tolerance"].tolist() == [True, True, True, True]
