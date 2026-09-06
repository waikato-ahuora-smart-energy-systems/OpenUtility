"""Create a release tag on the validated commit, or verify an existing remote tag."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess


def git(*args: str, cwd: Path) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def ensure_release_tag(tag: str, commit: str, *, cwd: Path) -> None:
    """Never move a tag; remote identity must match the checked-out commit."""
    if re.fullmatch(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", tag) is None:
        raise ValueError("Release tag must use the exact form vX.Y.Z.")
    expected = git(
        "rev-parse", "--verify", "--end-of-options", f"{commit}^{{commit}}", cwd=cwd
    )
    if git("rev-parse", "HEAD", cwd=cwd) != expected:
        raise ValueError("Checkout does not match the validated release commit.")
    ref = f"refs/tags/{tag}"
    remote = subprocess.run(
        ["git", "ls-remote", "--exit-code", "origin", ref],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if remote.returncode == 0:
        git("fetch", "--no-tags", "origin", ref, cwd=cwd)
        if git("rev-parse", "FETCH_HEAD^{commit}", cwd=cwd) != expected:
            raise ValueError(f"Remote tag {tag} points to a different commit.")
        print(f"Verified existing {tag} at {expected}")
        return
    if remote.returncode != 2:  # git ls-remote uses 2 for no matching ref.
        raise RuntimeError(
            f"Cannot inspect remote release tag: {remote.stderr.strip()}"
        )
    local = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if local.returncode == 0:
        if git("rev-parse", f"{ref}^{{commit}}", cwd=cwd) != expected:
            raise ValueError(f"Local tag {tag} points to a different commit.")
    else:
        git("tag", "-a", tag, "-m", f"OpenUtility {tag}", expected, cwd=cwd)
    # A concurrent conflicting push fails; no force push is permitted.
    git("push", "origin", ref, cwd=cwd)
    print(f"Created {tag} at {expected}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag")
    parser.add_argument("commit")
    args = parser.parse_args()
    ensure_release_tag(args.tag, args.commit, cwd=Path.cwd())


if __name__ == "__main__":
    main()
