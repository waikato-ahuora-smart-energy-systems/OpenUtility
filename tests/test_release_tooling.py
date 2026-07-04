from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_release_check_script_contains_required_gate_commands() -> None:
    script = PROJECT_ROOT / "tools" / "release_check.py"
    source = script.read_text()
    ast.parse(source)

    required_fragments = (
        '"ruff", "check"',
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

    assert 'python-version: "3.14"' in ci
    assert "python tools/release_check.py" in ci
    assert "uv sync --extra dev --extra docs --extra notebook --extra release" in ci

    assert 'python-version: "3.14"' in release
    assert "python tools/release_check.py" in release
    assert "id-token: write" in release
    assert "pypa/gh-action-pypi-publish@release/v1" in release
