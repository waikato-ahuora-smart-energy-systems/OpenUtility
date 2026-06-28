from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from OpenUtility.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_cli_writes_style_table_2_9_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--uncalibrated",
            "--format",
            "json",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert any(
        row["scenario"] == "hot-oil-fsr-microgrid"
        and row["field"] == "fuel_consumption"
        for row in rows
    )


def test_cli_writes_style_table_2_9_summary_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "summary",
            "--format",
            "json",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert len(rows) == 4
    assert rows[0]["scenario"] == "utility-system-stand-alone"
    assert rows[0]["failing_fields"] == (
        "fuel_consumption;operating_cost;total_annualized_cost"
    )


def test_cli_can_apply_physical_profile_fuel_targets() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "summary",
            "--format",
            "json",
            "--solver-time-limit",
            "20",
            "--apply-fuel-targets",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert all("fuel_consumption" not in row["failing_fields"] for row in rows)


def test_cli_writes_physical_profile_fuel_targeted_summary_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--apply-fuel-targets",
            "--view",
            "summary",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_targeted_summary.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_targeted_operating_components() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--apply-fuel-targets",
            "--view",
            "operating-components",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_targeted_operating_components.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_targeted_operating_targets() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--apply-fuel-targets",
            "--view",
            "operating-targets",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_targeted_operating_targets.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_and_operating_targeted_summary() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--apply-fuel-targets",
            "--apply-operating-targets",
            "--view",
            "summary",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_and_operating_targeted_summary.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_family_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "fuel-families",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_families.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_ranking_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "fuel-ranking",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_ranking.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_equipment_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "fuel-equipment",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_equipment.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_capacity_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "fuel-capacity",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_capacity.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_diagnosis_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "fuel-diagnosis",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_diagnosis.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_physical_profile_fuel_target_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--catalog",
            "physical-profile",
            "--view",
            "fuel-targets",
            "--format",
            "csv",
            "--solver-time-limit",
            "20",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "table_2_9_physical_profile_fuel_targets.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_steam_property_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "steam-properties",
            "--format",
            "json",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert len(rows) == 6
    assert rows[0]["turbine"] == "VHP-ST 1"
    assert rows[0]["power_generation_deviation"] == pytest.approx(-0.14)


def test_cli_writes_model_derived_steam_property_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "steam-properties",
            "--computed",
            "--format",
            "json",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert rows[0]["real_isentropic_enthalpy_change"] == pytest.approx(
        0.1385,
        abs=1e-4,
    )


def test_cli_writes_model_statistics_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "model-statistics",
            "--format",
            "json",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert len(rows) == 12
    assert rows[5]["variable_count"] == 9550


def test_cli_writes_computational_results_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "computational-results",
            "--format",
            "json",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert len(rows) == 72
    assert rows[0]["optimality_gap"] == pytest.approx(0.031)


def test_cli_writes_computational_best_method_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "computational-results",
            "--view",
            "best-method",
            "--format",
            "json",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert len(rows) == 24
    assert rows[0]["best_method"] == "s-milp"


def test_cli_writes_computational_method_summary_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "computational-results",
            "--view",
            "method-summary",
            "--format",
            "json",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert rows[0]["method"] == "baron"
    assert rows[0]["time_limit_count"] == 16


def test_cli_writes_bilevel_trajectory_json_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "computational-results",
            "--view",
            "bilevel-trajectory",
            "--format",
            "json",
        ],
        stdout=stdout,
    )
    rows = json.loads(stdout.getvalue())

    assert exit_code == 0
    assert len(rows) == 24
    assert rows[0]["objective_value"] == pytest.approx(30.487)
    assert rows[0]["subproblem_status"] == "reported"


def test_cli_writes_style_decomposition_trajectory_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--catalog",
            "physical-profile",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )

    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_physical_profile_decomposition_trajectories.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_style_decomposition_cost_comparison_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--catalog",
            "physical-profile",
            "--view",
            "summary",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_physical_profile_decomposition_cost_comparison.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_skipped_candidate_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-trajectory",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_skipped_candidate.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_cost_comparison_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-summary",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_cost_comparison.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_skipped_candidate_diagnostics() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-skips",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_skipped_candidates.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_pool_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-pool",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_pool.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_pool_comparison_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-pool-comparison",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_pool_comparison.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_selection_delta_report() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-selection-delta",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_selection_delta.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_selection_delta_summary() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-selection-summary",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_selection_delta_summary.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_skipped_delta_summary() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-skip-delta-summary",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_skip_delta_summary.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_audit_bundle() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-audit-bundle",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_audit_bundle.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_source_summary() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-source-summary",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_source_summary.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_source_detail() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-source-detail",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_source_detail.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_writes_candidate_decomposition_source_variables() -> None:
    stdout = io.StringIO()

    exit_code = main(
        [
            "--report",
            "style-decomposition",
            "--view",
            "candidate-source-variables",
            "--format",
            "csv",
        ],
        stdout=stdout,
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_source_variables.csv"
    )

    assert exit_code == 0
    assert stdout.getvalue() == f"{expected_output.read_text()}\n"


def test_cli_examples_match_generated_csv_reports() -> None:
    examples = (
        (
            "reported-equipment",
            ("--catalog", "reported-equipment"),
            PROJECT_ROOT / "examples" / "table_2_9_reported_equipment.csv",
        ),
        (
            "physical-profile",
            ("--catalog", "physical-profile"),
            PROJECT_ROOT / "examples" / "table_2_9_physical_profile.csv",
        ),
        (
            "steam-properties",
            ("--report", "steam-properties"),
            PROJECT_ROOT / "examples" / "steam_property_comparisons.csv",
        ),
        (
            "model-statistics",
            ("--report", "model-statistics"),
            PROJECT_ROOT / "examples" / "model_statistics.csv",
        ),
        (
            "computational-results",
            ("--report", "computational-results"),
            PROJECT_ROOT / "examples" / "computational_results.csv",
        ),
        (
            "computational-best-method",
            ("--report", "computational-results", "--view", "best-method"),
            PROJECT_ROOT / "examples" / "computational_best_methods.csv",
        ),
        (
            "computational-method-summary",
            ("--report", "computational-results", "--view", "method-summary"),
            PROJECT_ROOT / "examples" / "computational_method_summary.csv",
        ),
        (
            "computational-bilevel-trajectory",
            ("--report", "computational-results", "--view", "bilevel-trajectory"),
            PROJECT_ROOT / "examples" / "computational_bilevel_trajectory.csv",
        ),
    )

    for _, args, example_path in examples:
        stdout = io.StringIO()

        main([*args, "--format", "csv"], stdout=stdout)

        assert stdout.getvalue() == f"{example_path.read_text()}\n"


def test_reported_bilevel_comparison_example_matches_checked_output() -> None:
    example_script = PROJECT_ROOT / "examples" / (
        "contribution2_bilevel_reported_comparison.py"
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_bilevel_reported_comparison.csv"
    )

    result = subprocess.run(
        [sys.executable, str(example_script)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == expected_output.read_text()


def test_physical_profile_decomposition_smoke_example_matches_checked_output() -> None:
    example_script = PROJECT_ROOT / "examples" / (
        "contribution2_physical_profile_decomposition_smoke.py"
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_physical_profile_decomposition_smoke.csv"
    )

    result = subprocess.run(
        [sys.executable, str(example_script)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == expected_output.read_text()


def test_candidate_decomposition_skipped_candidate_example_matches_checked_output() -> None:
    example_script = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_skipped_candidate.py"
    )
    expected_output = PROJECT_ROOT / "examples" / (
        "contribution2_candidate_decomposition_skipped_candidate.csv"
    )

    result = subprocess.run(
        [sys.executable, str(example_script)],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == expected_output.read_text()
