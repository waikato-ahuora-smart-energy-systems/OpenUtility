from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys

from hypothesis import given, seed, strategies as st
import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versions = load_script("check_release_version")
tags = load_script("ensure_release_tag")
# Canonical release versions, including zero and large (non-single-digit) parts.
release_versions = st.tuples(
    *(st.integers(min_value=0, max_value=10000) for _ in range(3))
)


@pytest.mark.parametrize(
    ("labels", "title", "expected"),
    [
        ("", "", "patch"),
        ("documentation", "Normal change", "patch"),
        ("minor", "[major] change", "minor"),
        ("patch,major,minor", "", "major"),
        ("patch,minor", "", "minor"),
        (" MINOR ", "", "minor"),
        ("", "[MiNoR] feature", "minor"),
        ("", "[patch] [major] change", "major"),
        ("major-change", "minor cleanup", "patch"),
    ],
)
def test_bump_selector_precedence(labels, title, expected):
    assert versions.resolve_bump_part(labels, title) == expected


@pytest.mark.parametrize(
    ("current", "base", "part", "expected"),
    [
        ("0.1.2", "0.1.2", "patch", "0.1.3"),
        ("0.1.2", "0.1.2", "minor", "0.2.0"),
        ("0.1.2", "0.1.2", "major", "1.0.0"),
        ("0.1.3", "0.1.2", "minor", "0.2.0"),
        ("0.2.0", "0.1.2", "major", "1.0.0"),
        ("0.2.0", "0.1.2", "patch", "0.2.0"),
        ("2.4.7", "0.1.2", "major", "2.4.7"),
        ("1.9.9", "1.9.9", "patch", "1.9.10"),
    ],
)
def test_release_version_and_late_label_changes(current, base, part, expected):
    assert versions.plan_release_version(current, base, part) == expected


@seed(20260906)
@given(release_versions, st.sampled_from(("major", "minor", "patch")))
def test_generated_versions_advance_reset_and_are_idempotent(base_tuple, part):
    base = ".".join(map(str, base_tuple))
    assert versions._version_tuple(base) == base_tuple  # Canonical round trip.
    target = versions.plan_release_version(base, base, part)
    parsed = versions._version_tuple(target)
    position = ("major", "minor", "patch").index(part)
    assert parsed > base_tuple
    assert parsed[:position] == base_tuple[:position]
    assert parsed[position] == base_tuple[position] + 1
    assert all(value == 0 for value in parsed[position + 1 :])
    assert versions.plan_release_version(target, base, part) == target


@seed(20260906)
@given(release_versions, release_versions, st.sampled_from(("major", "minor", "patch")))
def test_generated_forward_versions_never_decrease(first, second, part):
    baseline, candidate = sorted((first, second))
    current = ".".join(map(str, candidate))
    base = ".".join(map(str, baseline))
    target = versions.plan_release_version(current, base, part)
    assert versions._version_tuple(target) >= candidate
    assert versions.plan_release_version(target, base, part) == target


@pytest.mark.parametrize(
    ("current", "base", "part"),
    [
        ("0.1.1", "0.1.2", "major"),
        ("v0.1.2", "0.1.2", "patch"),
        ("0.1.2", "01.1.2", "patch"),
        ("0.1.2", "0.1.2", "feature"),
    ],
)
def test_invalid_or_stale_candidates_are_rejected(current, base, part):
    with pytest.raises(ValueError):
        versions.plan_release_version(current, base, part)


def test_workflow_cli_checks_requested_increment_and_config(tmp_path):
    candidate = tmp_path / "candidate.toml"
    base = tmp_path / "base.toml"
    config = tmp_path / "bump.toml"
    candidate.write_text('[project]\nversion = "0.1.3"\n')
    base.write_text('[project]\nversion = "0.1.2"\n')
    config.write_text('[tool.bumpversion]\ncurrent_version = "0.1.3"\n')
    command = [
        sys.executable,
        str(ROOT / "scripts/check_release_version.py"),
        "--pyproject",
        str(candidate),
        "--base-pyproject",
        str(base),
        "--bump-config",
        str(config),
        "--labels=minor",
    ]
    planned = subprocess.run([*command, "--plan-bump"], capture_output=True, text=True)
    assert planned.returncode == 0 and planned.stdout.strip() == "0.2.0"
    checked = subprocess.run(
        [*command, "--require-bump"], capture_output=True, text=True
    )
    assert checked.returncode == 1 and "requires 0.2.0" in checked.stdout
    candidate.write_text('[project]\nversion = "0.2.0"\n')
    checked = subprocess.run(
        [*command, "--require-bump"], capture_output=True, text=True
    )
    assert checked.returncode == 1 and "configuration" in checked.stdout
    config.write_text('[tool.bumpversion]\ncurrent_version = "0.2.0"\n')
    subprocess.run([*command, "--require-bump"], check=True, capture_output=True)


def git(cwd, *args):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


@pytest.fixture
def release_repo(tmp_path):
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", str(remote))
    repo = tmp_path / "checkout"
    git(tmp_path, "init", str(repo))
    git(repo, "config", "user.name", "Release test")
    git(repo, "config", "user.email", "release@example.invalid")
    git(repo, "config", "commit.gpgsign", "false")
    git(repo, "config", "tag.gpgsign", "false")
    (repo / "file").write_text("first\n")
    git(repo, "add", "file")
    git(repo, "commit", "-m", "First")
    git(repo, "remote", "add", "origin", str(remote))
    return repo


def test_release_tag_creation_and_retry_keep_exact_identity(release_repo):
    repo = release_repo
    commit = git(repo, "rev-parse", "HEAD")
    tags.ensure_release_tag("v0.1.3", commit, cwd=repo)
    assert git(repo, "cat-file", "-t", "refs/tags/v0.1.3") == "tag"
    first = git(repo, "ls-remote", "origin", "refs/tags/v0.1.3")
    # Rerun from a checkout without the local tag; the remote still controls identity.
    git(repo, "tag", "-d", "v0.1.3")
    tags.ensure_release_tag("v0.1.3", commit, cwd=repo)
    assert git(repo, "ls-remote", "origin", "refs/tags/v0.1.3") == first


def test_release_tag_cannot_move_to_a_new_commit(release_repo):
    repo = release_repo
    first = git(repo, "rev-parse", "HEAD")
    tags.ensure_release_tag("v0.1.3", first, cwd=repo)
    (repo / "file").write_text("second\n")
    git(repo, "commit", "-am", "Second")
    second = git(repo, "rev-parse", "HEAD")
    with pytest.raises(ValueError, match="Remote tag"):
        tags.ensure_release_tag("v0.1.3", second, cwd=repo)
    with pytest.raises(ValueError, match="Checkout"):
        tags.ensure_release_tag("v0.1.4", first, cwd=repo)
    assert git(repo, "rev-parse", "refs/tags/v0.1.3^{commit}") == first


def test_release_tag_remote_errors_fail_closed(release_repo):
    repo = release_repo
    git(repo, "remote", "set-url", "origin", str(repo / "missing.git"))
    with pytest.raises(RuntimeError, match="Cannot inspect remote"):
        tags.ensure_release_tag("v1.0.0", git(repo, "rev-parse", "HEAD"), cwd=repo)
    assert git(repo, "tag", "--list") == ""


@pytest.mark.parametrize(
    (
        "all_tests",
        "release_gate",
        "bump",
        "version_check",
        "head_repo",
        "base",
        "passes",
    ),
    [
        ("success", "success", "success", "success", "owner/repo", "main", True),
        ("failure", "success", "success", "success", "owner/repo", "main", False),
        ("success", "failure", "success", "success", "owner/repo", "main", False),
        ("success", "success", "failure", "success", "owner/repo", "main", False),
        ("success", "success", "success", "skipped", "owner/repo", "main", False),
        ("success", "success", "skipped", "success", "fork/repo", "main", True),
        ("success", "success", "skipped", "failure", "fork/repo", "main", False),
        ("success", "success", "skipped", "skipped", "owner/repo", "develop", True),
    ],
)
def test_required_gate_shell_rejects_unsuccessful_validation(
    all_tests,
    release_gate,
    bump,
    version_check,
    head_repo,
    base,
    passes,
):
    import os
    import textwrap

    workflow = (ROOT / ".github/workflows/ci.yml").read_text()
    gate = workflow.split("  pr-gate:", 1)[1]
    script = textwrap.dedent(
        gate.split("        run: |\n", 1)[1].split("      - name:", 1)[0]
    )
    result = subprocess.run(
        ["bash", "-c", script],
        env={
            **os.environ,
            "ALL_TESTS_RESULT": all_tests,
            "RELEASE_GATE_RESULT": release_gate,
            "BUMP_VERSION_RESULT": bump,
            "RELEASE_VERSION_RESULT": version_check,
            "HEAD_REPO": head_repo,
            "BASE_REF": base,
            "REPOSITORY": "owner/repo",
        },
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) is passes
