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
    _run([sys.executable, "-m", "mypy", "OpenUtility", "case_study"])
    _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--cov=OpenUtility",
            "--cov=case_study",
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
    _require("OpenUtility/py.typed" in names, "wheel must include OpenUtility/py.typed")
    _require(
        sum(name.startswith("case_study/") and name.endswith(".csv") for name in names)
        >= 34,
        "wheel must include checked case-study CSV assets",
    )
    _require(
        sum(
            name.startswith("case_study/") and name.endswith(".ipynb") for name in names
        )
        >= 3,
        "wheel must include case-study notebooks",
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
        import io

        import pyomo.environ as pyo
        from pyomo.environ import SolverFactory

        import OpenUtility
        from case_study.jimenez_romero_utility_system_optimization.cli import main

        assert "pyomo_static_style_solver" in OpenUtility.__all__
        assert SolverFactory("appsi_highs").available(exception_flag=False)

        model = pyo.ConcreteModel()
        model.x = pyo.Var(domain=pyo.Binary)
        model.objective = pyo.Objective(expr=model.x)
        solver = OpenUtility.pyomo_static_style_solver("appsi_highs")
        status = solver(model)
        assert status.termination_condition == "optimal"
        assert pyo.value(model.x) == 0

        output = io.StringIO()
        code = main(
            [
                "--catalog",
                "reported-equipment",
                "--view",
                "summary",
                "--format",
                "csv",
            ],
            stdout=output,
        )
        assert code == 0
        text = output.getvalue()
        assert "catalog,case_study,scenario,within_tolerance" in text
        assert "reported-equipment,contribution-2-case-study-2" in text
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
