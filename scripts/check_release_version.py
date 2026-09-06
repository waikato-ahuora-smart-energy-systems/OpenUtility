"""Validate the strict project release version and optional forward advance."""

from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path

_VERSION_PART = r"(?:0|[1-9]\d*)"
RELEASE_VERSION_PATTERN = re.compile(
    rf"(?P<major>{_VERSION_PART})\."
    rf"(?P<minor>{_VERSION_PART})\."
    rf"(?P<patch>{_VERSION_PART})\Z",
)
REPO_ROOT = Path(__file__).resolve().parents[1]


def read_project_version(pyproject: Path) -> str:
    """Return one canonical ``X.Y.Z`` project version."""
    with pyproject.open("rb") as handle:
        version = str(tomllib.load(handle)["project"]["version"])
    if RELEASE_VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError(
            f"Project version {version!r} must use the exact form X.Y.Z.",
        )
    return version


def validate_version_advance(pyproject: Path, base_pyproject: Path) -> str:
    """Return the current version when it strictly exceeds the base version."""
    current = read_project_version(pyproject)
    base = read_project_version(base_pyproject)
    if _version_tuple(current) <= _version_tuple(base):
        raise ValueError(
            f"Release version {current!r} must be greater than base version {base!r}.",
        )
    return current


def resolve_bump_part(labels: str = "", title: str = "") -> str:
    """Use labels before title markers, with major > minor > patch precedence."""
    named_labels = {label.strip().lower() for label in labels.split(",")}
    markers = set(re.findall(r"\[(major|minor|patch)\]", title.lower()))
    for choices in (named_labels, markers):
        for part in ("major", "minor", "patch"):
            if part in choices:
                return part
    return "patch"


def plan_release_version(current: str, base: str, part: str) -> str:
    """Return a base-relative bump without downgrading or repeatedly bumping."""
    candidate = _version_tuple(current)
    baseline = _version_tuple(base)
    if candidate < baseline:
        raise ValueError(f"Candidate version {current!r} is behind base {base!r}.")
    major, minor, patch = baseline
    if part == "major":
        target = (major + 1, 0, 0)
    elif part == "minor":
        target = (major, minor + 1, 0)
    elif part == "patch":
        target = (major, minor, patch + 1)
    else:
        raise ValueError(f"Unknown version part {part!r}.")
    return ".".join(str(number) for number in max(candidate, target))


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=REPO_ROOT / "pyproject.toml",
        help="Project metadata containing the candidate release version.",
    )
    parser.add_argument(
        "--base-pyproject",
        type=Path,
        default=None,
        help="Optional base-branch metadata that the candidate must exceed.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--plan-bump", action="store_true", help="Print the target version"
    )
    mode.add_argument(
        "--require-bump",
        action="store_true",
        help="Require the requested bump or higher",
    )
    parser.add_argument("--labels", default="", help="Comma-separated PR labels")
    parser.add_argument(
        "--title", default="", help="PR title with optional [part] marker"
    )
    parser.add_argument(
        "--bump-config", type=Path, help="Also check bump configuration"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Validate and print the candidate release version."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.plan_bump or args.require_bump) and args.base_pyproject is None:
        parser.error("Bump planning and validation require --base-pyproject")
    try:
        version = read_project_version(args.pyproject)
        if args.bump_config is not None:
            with args.bump_config.open("rb") as handle:
                configured = tomllib.load(handle)["tool"]["bumpversion"][
                    "current_version"
                ]
            if configured != version:
                raise ValueError(
                    "Bump configuration does not match the project version."
                )
        if args.plan_bump or args.require_bump:
            target = plan_release_version(
                version,
                read_project_version(args.base_pyproject),
                resolve_bump_part(args.labels, args.title),
            )
            if args.require_bump and version != target:
                raise ValueError(
                    f"Requested release requires {target}; found {version}."
                )
            version = target
        elif args.base_pyproject is not None:
            version = validate_version_advance(args.pyproject, args.base_pyproject)
    except (KeyError, OSError, TypeError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(exc)
        return 1
    print(version)
    return 0


def _version_tuple(version: str) -> tuple[int, int, int]:
    match = RELEASE_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError(f"Project version {version!r} must use the exact form X.Y.Z.")
    return tuple(int(match.group(name)) for name in ("major", "minor", "patch"))


if __name__ == "__main__":
    raise SystemExit(main())
