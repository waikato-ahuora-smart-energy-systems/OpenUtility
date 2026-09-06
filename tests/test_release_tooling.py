from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
import sys
import tomllib

import pytest

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
    assert 'branches: ["main", "develop"]' in ci
    assert "all-tests:" in ci
    assert "needs: [all-tests, bump-version]" in ci
    assert "Run all tests with coverage" in ci
    assert "python tools/release_check.py" in ci
    assert (
        "uv sync --frozen --extra dev --extra docs --extra notebook --extra release"
        in ci
    )
    assert "bump-version:" in ci
    assert "release-version:" in ci
    assert "pr-gate:" in ci
    pr_gate = ci.split("  pr-gate:", maxsplit=1)[1]
    assert "always() && github.event_name == 'pull_request'" in pr_gate
    assert "- all-tests" in pr_gate
    assert "- release-gate" in pr_gate
    assert "- bump-version" in pr_gate
    assert "- release-version" in pr_gate
    assert 'test "${ALL_TESTS_RESULT}" = "success"' in pr_gate
    assert 'test "${RELEASE_GATE_RESULT}" = "success"' in pr_gate
    assert 'test "${BUMP_VERSION_RESULT}" = "success"' in pr_gate
    assert 'test "${RELEASE_VERSION_RESULT}" = "success"' in pr_gate
    assert "bump-my-version==1.2.3" in ci
    assert "PR_LABELS: ${{ join(github.event.pull_request.labels.*.name" in ci
    assert "PR_TITLE: ${{ github.event.pull_request.title }}" in ci
    assert "contents: write" in ci
    assert "GH_TOKEN: ${{ github.token }}" in ci
    assert "AUTHORIZATION: bearer ${GH_TOKEN}" not in ci
    bump_job = ci.split("  bump-version:", maxsplit=1)[1].split(
        "  release-version:",
        maxsplit=1,
    )[0]
    release_version_job = ci.split("  release-version:", maxsplit=1)[1]
    assert "persist-credentials: true" in bump_job
    assert (
        "https://x-access-token:${GH_TOKEN}@github.com/${BASE_REPOSITORY}.git"
        in release_version_job
    )
    assert "unset GH_TOKEN" in release_version_job
    assert "scripts/check_lockfile_version.py" in ci
    assert "scripts/check_release_version.py" in ci
    assert "actions/checkout@08c6903cd8c0fde910a37f88322edcfb5dd907a8" in ci
    assert "actions/setup-python@a309ff8b426b58ec0e2a45f0f869d46889d02405" in ci
    assert "astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d" in ci

    assert 'PYTHON_VERSION: "3.14.2"' in release
    assert "workflow_run:" in release
    assert 'workflows: ["CI"]' in release
    assert 'branches: ["main"]' in release
    assert "types: [completed]" in release
    assert "github.event.workflow_run.conclusion == 'success'" in release
    assert "github.event.workflow_run.event == 'push'" in release
    assert "github.event.workflow_run.head_branch == 'main'" in release
    assert "github.event.workflow_run.head_sha" in release
    assert "validate:" in release
    assert "publish:" in release
    assert "needs: validate" in release
    assert "python tools/release_check.py" in release
    assert (
        "uv sync --frozen --extra dev --extra docs --extra notebook --extra release"
        in release
    )
    assert "scripts/check_release_tag.py" in release
    assert "scripts/check_release_version.py" in release
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in release
    assert (
        "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c" in release
    )
    assert (
        "name: openutility-dist-${{ github.run_id }}-${{ github.run_attempt }}"
        in release
    )
    assert "artifact-ids: ${{ needs.validate.outputs.distribution-id }}" in release
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

    assert "bump --new-version" in bump_job
    assert "--plan-bump" in bump_job
    assert "--require-bump" in release_version_job
    assert 'echo "head-sha=$(git rev-parse HEAD)"' in bump_job
    assert (
        ci.count("ref: ${{ needs.bump-version.outputs.head-sha || github.sha }}") == 2
    )
    assert "checks: write" in pr_gate
    assert '-f name=pr-gate -f head_sha="${VALIDATED_SHA}"' in pr_gate
    assert "success() && needs.bump-version.outputs.head-sha != ''" in pr_gate
    assert "needs: [validate, tag-release]" in release
    assert "needs: [validate, publish]" in release
    assert "scripts/ensure_release_tag.py" in release
    assert "--verify-tag --generate-notes" in release
    assert "cancel-in-progress: false" in release


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
    assert "/tools" in sdist_includes

    for script_name in (
        "check_lockfile_version.py",
        "check_release_tag.py",
        "check_release_version.py",
        "ensure_release_tag.py",
    ):
        source = (PROJECT_ROOT / "scripts" / script_name).read_text()
        ast.parse(source)


def test_wheel_smoke_ignores_checkout_and_pythonpath(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Exercise the smoke subprocess with an import trap on PYTHONPATH."""
    spec = importlib.util.spec_from_file_location(
        "release_check", PROJECT_ROOT / "tools" / "release_check.py"
    )
    assert spec is not None and spec.loader is not None
    release_check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release_check)

    (tmp_path / "checkout_import_trap.py").write_text(
        'raise RuntimeError("Imported from PYTHONPATH")\n'
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path))
    smoke_code = (
        "import importlib.util, pathlib, sys\n"
        f"assert pathlib.Path.cwd() != pathlib.Path({str(PROJECT_ROOT)!r})\n"
        "assert sys.flags.isolated\n"
        "assert importlib.util.find_spec('checkout_import_trap') is None\n"
    )
    monkeypatch.setattr(release_check, "_smoke_install_code", lambda: smoke_code)
    monkeypatch.setattr(release_check.shutil, "which", lambda _: None)
    run = release_check._run
    completed = []

    def run_without_install(command, **kwargs):
        # Avoid network/venv creation here; the full release gate tests those.
        if "-c" in command:
            run([sys.executable, *command[1:]], **kwargs)
            completed.append(True)

    monkeypatch.setattr(release_check, "_run", run_without_install)
    release_check._smoke_install(tmp_path / "unused.whl")
    assert completed == [True]
