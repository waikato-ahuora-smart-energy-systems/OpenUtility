# Automatic release versioning

## Authorized scope and design

User requests OpenPinch-style automatic GitHub workflow version bumps with major
and minor selectors. Existing OpenUtility uses the same equal-version-only bump
as the local OpenPinch checkout. Extend it to honor labels added after a previous
bump, validate the resulting commit, and create the corresponding release tag.

Default is patch. Labels major/minor/patch take precedence over bracketed title
markers, with major winning conflicts. Compute the minimum target from main:
patch adds one patch; minor adds one minor and resets patch; major adds one major
and resets both lower components. Preserve any already higher candidate; reject
candidates behind main. Repeated execution must not keep incrementing versions.

CI updates pyproject.toml, uv.lock, and .bumpversion.toml together using the
existing pinned bump-my-version tool. All release checks use the resulting
commit. Record the required check on that commit when the bot creates it, so
validation does not rely on a second workflow being automatically triggered.
Release validation resolves one version/tag/commit identity. Create or verify
the vX.Y.Z tag before PyPI publication; create a GitHub release with the same
verified distributions after publication. Never move an existing tag.

This extends the existing release tooling unit. Reuse current architecture,
trusted publishing, main protection, and notebook validation. No library API,
new service, user stories, or new infrastructure design is needed.

## Steps

- [x] Compare OpenPinch and OpenUtility workflows and load current workflow rules.
- [x] Define version precedence, reset behavior, idempotence, and release identity.
- [x] Implement and test version planning and tag creation/verification helpers.
- [x] Wire exact-commit CI and version/tag/artifact publication through workflows.
- [x] Document label examples and release behavior.
- [x] Run focused behavior tests, regression checks, lint, and documentation build.
- [x] Record delivery and validation results.

## Testable properties and extension compliance

Test generated canonical semantic versions for monotonic advance, lower-component
reset, and idempotence. Generate bounded nonnegative version components, including
zero, so tests do not filter away relevant inputs. Version formatting/parsing
round trips are covered for generated tuples. Use behavioral CLI and local Git
remote tests for synchronized bump files and immutable tag identity.

Partial PBT: PBT-02, PBT-03, PBT-07, PBT-08, and PBT-09 apply to the pure version
planner; document and exercise the above properties. Security and resiliency
extensions remain disabled. Parse Python, TOML, YAML, and shell before use;
no diagrams are required.

Framework: Hypothesis in the dev extra; generated tests use seed 20260906 with default shrinking. Actual bump-my-version 1.2.3 integration verified patch, late minor, late major, repeated runs, clean commits, and synchronization of all three version files in a disposable Git repository.

## Validation results

- 223 tests passed, including generated version properties, late selector changes,
  CLI checks, local Git tag creation/retries/conflicts, and eight real shell-gate
  success/failure scenarios. Library coverage remains 90.24%.
- Actual bump-my-version 1.2.3 updated all three metadata files consistently
  through 0.1.3, 0.2.0, and 1.0.0; retries made no extra commit.
- Actionlint 1.7.12 passed for both workflows. YAML parsing and bash syntax
  validation passed for every run step.
- Ruff lint/format, mypy, Sphinx warnings-as-errors, lockfile/config checks,
  wheel/sdist build, Twine, and whitespace checks passed.
- The sdist includes the release-tag helper and its tests, plus all six public
  notebooks from the preceding task.

PBT compliance: PBT-02 and PBT-03 compliant through generated canonical-version
round trips and ordering/reset/idempotence invariants. PBT-07 compliant through
bounded structured version strategies including zero. PBT-08 compliant with
seed 20260906 and default Hypothesis shrinking. PBT-09 compliant: Hypothesis is
in the dev extra and runs in the normal CI test suite. Disabled security and
resiliency extensions remain skipped.

Changes are local and have not created a remote tag, release, or publication.
The workflow will apply the increment when a non-draft PR targets main; the
current source version stays 0.1.2 until that automation runs. Hosted GitHub
check reporting and publication still require the deployed workflow run.

Dependency audit: no known vulnerabilities found in the updated environment.
