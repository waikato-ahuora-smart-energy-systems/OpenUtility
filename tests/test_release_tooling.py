from __future__ import annotations

import ast
from pathlib import Path
import tomllib


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_release_check_script_contains_required_gate_commands() -> None:
    script = PROJECT_ROOT / "tools" / "release_check.py"
    source = script.read_text()
    ast.parse(source)

    required_fragments = (
        '"ruff", "check"',
        "scripts/check_lockfile_version.py",
        "scripts/check_release_version.py",
        '"ruff", "format", "--check"',
        '"mypy"',
        '"pytest"',
        '"--cov-fail-under=90"',
        '"sphinx"',
        '"build", "--no-isolation"',
        '"twine", "check"',
        '"pip_audit"',
        '"uv", "pip", "install"',
        '"appsi_highs"',
    )

    for fragment in required_fragments:
        assert fragment in source


def test_github_workflows_run_release_gate_and_publish_with_trusted_publishing() -> (
    None
):
    ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text()
    release = (PROJECT_ROOT / ".github" / "workflows" / "release.yml").read_text()

    assert 'PYTHON_VERSION: "3.14.2"' in ci
    assert "python tools/release_check.py" in ci
    assert (
        "uv sync --frozen --extra dev --extra docs --extra notebook --extra release"
        in ci
    )
    assert "bump-version:" in ci
    assert "release-version:" in ci
    assert "bump-my-version==1.2.3" in ci
    assert "major" in ci
    assert "minor" in ci
    assert "patch" in ci
    assert "contents: write" in ci
    assert "scripts/check_lockfile_version.py" in ci
    assert "scripts/check_release_version.py" in ci

    assert 'PYTHON_VERSION: "3.14.2"' in release
    assert "python tools/release_check.py" in release
    assert (
        "uv sync --frozen --extra dev --extra docs --extra notebook --extra release"
        in release
    )
    assert "scripts/check_release_tag.py" in release
    assert "environment:" in release
    assert "name: pypi" in release
    assert "url: https://pypi.org/project/OpenUtility/" in release
    assert "id-token: write" in release
    assert "pypa/gh-action-pypi-publish@release/v1" in release


def test_version_bump_configuration_tracks_project_and_lockfile() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    bumpversion = tomllib.loads((PROJECT_ROOT / ".bumpversion.toml").read_text())
    lock = tomllib.loads((PROJECT_ROOT / "uv.lock").read_text())

    project_version = pyproject["project"]["version"]
    assert bumpversion["tool"]["bumpversion"]["current_version"] == project_version
    assert bumpversion["tool"]["bumpversion"]["tag"] is False
    assert bumpversion["tool"]["bumpversion"]["commit"] is True
    assert any(
        file_config["filename"] == "./uv.lock"
        and 'name = "openutility"' in file_config["search"]
        for file_config in bumpversion["tool"]["bumpversion"]["files"]
    )
    assert any(
        package["name"] == "openutility"
        and package["version"] == project_version
        and package.get("source") == {"editable": "."}
        for package in lock["package"]
    )


def test_release_helper_scripts_are_parseable_and_packaged() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text())
    sdist_includes = pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]["include"]
    assert "/.bumpversion.toml" in sdist_includes
    assert "/scripts" in sdist_includes

    for script_name in (
        "check_lockfile_version.py",
        "check_release_tag.py",
        "check_release_version.py",
    ):
        source = (PROJECT_ROOT / "scripts" / script_name).read_text()
        ast.parse(source)
