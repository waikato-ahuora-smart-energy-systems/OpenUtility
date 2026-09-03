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
    assert "actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8" in ci
    assert "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405" in ci
    assert "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d" in ci

    assert 'PYTHON_VERSION: "3.14.2"' in release
    assert "validate:" in release
    assert "publish:" in release
    assert "needs: validate" in release
    assert "python tools/release_check.py" in release
    assert (
        "uv sync --frozen --extra dev --extra docs --extra notebook --extra release"
        in release
    )
    assert "scripts/check_release_tag.py" in release
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in release
    assert (
        "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in release
    )
    assert "environment:" in release
    assert "name: pypi" in release
    assert "url: https://pypi.org/project/OpenUtility/" in release
    assert "id-token: write" in release
    assert "actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8" in release
    assert "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405" in release
    assert "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d" in release
    assert (
        "pypa/gh-action-pypi-publish@dc37677b2e1c63e2034f94d8a5b11f265b73ba33"
        in release
    )
    assert "skip-existing: true" in release


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
