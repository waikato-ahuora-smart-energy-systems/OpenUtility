"""Run the OpenUtility release readiness gate."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    os.chdir(PROJECT_ROOT)

    _run([sys.executable, "-m", "ruff", "check", "."])
    _run([sys.executable, "-m", "ruff", "format", "--check", "."])
    _run([sys.executable, "-m", "mypy", "OpenUtility"])
    _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=OpenUtility",
            "--cov-report=term-missing",
            "--cov-fail-under=90",
        ],
    )
    with tempfile.TemporaryDirectory(prefix="openutility-docs-") as docs_dir:
        _run(
            [
                sys.executable,
                "-m",
                "sphinx",
                "-W",
                "-b",
                "html",
                "docs",
                docs_dir,
            ],
        )

    _build_distribution()
    wheel = _latest_wheel()
    _inspect_wheel(wheel)
    _run([sys.executable, "-m", "twine", "check", *map(str, sorted(_dist_files()))])

    if not args.skip_audit:
        _run([sys.executable, "-m", "pip_audit"])
    if not args.skip_smoke_install:
        _smoke_install(wheel)

    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-audit",
        action="store_true",
        help="Skip dependency audit. Intended only for offline local triage.",
    )
    parser.add_argument(
        "--skip-smoke-install",
        action="store_true",
        help="Skip fresh-environment wheel installation smoke test.",
    )
    return parser.parse_args(argv)


def _build_distribution() -> None:
    dist = PROJECT_ROOT / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    _run([sys.executable, "-m", "build", "--no-isolation"])


def _latest_wheel() -> Path:
    wheels = sorted((PROJECT_ROOT / "dist").glob("openutility-*.whl"))
    if not wheels:
        raise RuntimeError("release build did not produce an OpenUtility wheel")
    return wheels[-1]


def _dist_files() -> tuple[Path, ...]:
    return tuple((PROJECT_ROOT / "dist").glob("openutility-*"))


def _inspect_wheel(wheel: Path) -> None:
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata_name = next(name for name in names if name.endswith("METADATA"))
        metadata = archive.read(metadata_name).decode()
    requires_dist = tuple(
        line for line in metadata.splitlines() if line.startswith("Requires-Dist:")
    )
    _require(
        any("highspy>=1.15.1" in line for line in requires_dist),
        "wheel metadata must require highspy>=1.15.1",
    )
    _require(
        not any("scipy" in line.lower() for line in requires_dist),
        "wheel metadata must not directly require scipy",
    )
    _require(
        not any("openpinch" in line.lower() for line in requires_dist),
        "wheel metadata must not directly require OpenPinch",
    )
    _require("OpenUtility/py.typed" in names, "wheel must include OpenUtility/py.typed")
    _require(
        not any(name.startswith("case_study/") for name in names),
        "wheel must not include private case-study assets",
    )
    forbidden_fragments = (
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "examples/",
    )
    _require(
        not any(
            any(fragment in name for fragment in forbidden_fragments) for name in names
        ),
        "wheel contains cache artifacts or root examples",
    )


def _smoke_install(wheel: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="openutility-smoke-") as temp_dir:
        venv_dir = Path(temp_dir) / "venv"
        _run([sys.executable, "-m", "venv", str(venv_dir)])
        python = _venv_python(venv_dir)
        if shutil.which("uv") is not None:
            _run(["uv", "pip", "install", "--python", str(python), str(wheel)])
        else:
            _run([str(python), "-m", "pip", "install", str(wheel)])
        _run([str(python), "-c", _smoke_install_code()])


def _smoke_install_code() -> str:
    return textwrap.dedent(
        """
        import pyomo.environ as pyo
        from pyomo.environ import SolverFactory

        import OpenUtility

        assert "pyomo_utility_system_solver" in OpenUtility.__all__
        assert SolverFactory("appsi_highs").available(exception_flag=False)

        model = pyo.ConcreteModel()
        model.x = pyo.Var(domain=pyo.Binary)
        model.objective = pyo.Objective(expr=model.x)
        solver = OpenUtility.pyomo_utility_system_solver("appsi_highs")
        status = solver(model)
        assert status.termination_condition == "optimal"
        assert pyo.value(model.x) == 0

        units = {
            "source_temperature": "degC",
            "sink_temperature": "degC",
            "q_source": "kW",
            "q_sink": "kW",
            "electric_power": "kW",
        }
        level = OpenUtility.SteamLevelCandidate(
            name="MP_100",
            steam_main="MP",
            temperature=100.0,
            source_heat_available=0.0,
            sink_heat_demand=0.0,
            generation_enthalpy_delta=1.0,
            use_enthalpy_delta=1.0,
        )
        heat_pump_map = OpenUtility.HprPerformanceMap(
            schema_version="1.0",
            map_id="hp-map",
            mode="heat_pump",
            units=units,
            reference_capacity=150.0,
            interpolation_topology="ordered_part_load_curve",
            thermodynamic_backend="synthetic",
            model_id="smoke",
            provenance={"source": "release-smoke"},
            points=(
                OpenUtility.HprPerformancePoint(
                    name="full",
                    curve_id="curve",
                    source_temperature=40.0,
                    sink_temperature=80.0,
                    load_fraction=1.0,
                    q_source=100.0,
                    q_sink=150.0,
                    electric_power=50.0,
                ),
            ),
        )
        heat_pump_data = OpenUtility.UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(level,),
            power_demand=0.0,
            thermal_nodes=(
                OpenUtility.ThermalNode("waste", 40.0, "source"),
                OpenUtility.ThermalNode("heat", 80.0, "sink", heating_unit_cost=10.0),
            ),
            periods=(
                OpenUtility.OperatingPeriod(
                    name="day",
                    hours=1.0,
                    electricity_import_unit_cost=1.0,
                    source_heat_available={"waste": 100.0},
                    heating_demand={"heat": 150.0},
                ),
            ),
            hpr_performance_maps=(heat_pump_map,),
            hpr_candidates=(
                OpenUtility.HprCandidate(
                    name="hp",
                    mode="heat_pump",
                    map_id="hp-map",
                    source_node="waste",
                    sink_node="heat",
                    fixed_capacity=150.0,
                ),
            ),
        )
        heat_pump_model = OpenUtility.build_utility_system_model(heat_pump_data)
        status = solver(heat_pump_model)
        assert status.termination_condition == "optimal"
        assert pyo.value(heat_pump_model.hpr_q_sink["hp", "day"]) == 150.0

        refrigeration_map = OpenUtility.HprPerformanceMap(
            schema_version="1.0",
            map_id="ref-map",
            mode="refrigeration",
            units=units,
            reference_capacity=100.0,
            interpolation_topology="ordered_part_load_curve",
            thermodynamic_backend="synthetic",
            model_id="smoke",
            provenance={"source": "release-smoke"},
            points=(
                OpenUtility.HprPerformancePoint(
                    name="full",
                    curve_id="curve",
                    source_temperature=-5.0,
                    sink_temperature=35.0,
                    load_fraction=1.0,
                    q_source=100.0,
                    q_sink=125.0,
                    electric_power=25.0,
                ),
            ),
        )
        refrigeration_data = OpenUtility.UtilitySystemModelData(
            steam_mains=("MP",),
            steam_levels=(level,),
            power_demand=0.0,
            thermal_nodes=(
                OpenUtility.ThermalNode(
                    "cold",
                    -5.0,
                    "cooling",
                    cooling_unit_cost=10.0,
                ),
                OpenUtility.ThermalNode("reject", 35.0, "rejection"),
            ),
            periods=(
                OpenUtility.OperatingPeriod(
                    name="day",
                    hours=1.0,
                    electricity_import_unit_cost=1.0,
                    cooling_demand={"cold": 100.0},
                    rejection_capacity={"reject": 200.0},
                ),
            ),
            hpr_performance_maps=(refrigeration_map,),
            hpr_candidates=(
                OpenUtility.HprCandidate(
                    name="chiller",
                    mode="refrigeration",
                    map_id="ref-map",
                    source_node="cold",
                    rejection_node="reject",
                    fixed_capacity=100.0,
                ),
            ),
        )
        refrigeration_model = OpenUtility.build_utility_system_model(
            refrigeration_data
        )
        status = solver(refrigeration_model)
        assert status.termination_condition == "optimal"
        assert pyo.value(refrigeration_model.hpr_q_source["chiller", "day"]) == 100.0
        """,
    ).strip()


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(command: list[str]) -> None:
    print("$", " ".join(command), flush=True)
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


if __name__ == "__main__":
    raise SystemExit(main())
