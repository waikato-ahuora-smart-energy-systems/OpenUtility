Release Strategy
================

OpenUtility uses a guarded release path based on the OpenPinch workflow model,
adapted to this package's smaller public surface.

Pull requests
-------------

Pull requests run the full release gate on Python 3.14.2. The gate checks:

* the editable project version in ``uv.lock`` matches ``pyproject.toml``;
* the project version is a strict ``X.Y.Z`` release version;
* Ruff linting and formatting;
* mypy over ``OpenUtility``;
* pytest with the configured coverage threshold;
* Sphinx documentation with warnings treated as failures;
* source and wheel builds;
* wheel metadata and contents;
* ``twine check``;
* dependency audit;
* fresh wheel-install smoke tests with HiGHS solves, using isolated Python
  outside the checkout and checking that imports come from the installed wheel.

CI also exposes an explicit ``pr-gate`` job for GitHub branch protection. That
job depends on the complete pytest suite, the full release gate, and the
applicable release-version checks. Configure ``main`` so pull requests cannot be
merged until ``pr-gate`` succeeds.

For same-repository pull requests targeting ``main``, CI also maintains the
candidate release version. The version bump is selected from labels named
``major``, ``minor``, or ``patch``. If no label is present, CI also accepts
``[major]``, ``[minor]``, or ``[patch]`` in the pull-request title. The default
is ``patch``.

Labels take precedence over title markers. Within either source, ``major`` wins
over ``minor``, which wins over ``patch``. These are pull-request labels or title
markers; the resulting Git release tag is the full version, such as ``v0.2.0``.

.. list-table:: Version selection when main is at 0.1.2
   :header-rows: 1

   * - Selector
     - Package version
     - Release tag
   * - None, ``patch``, or ``[patch]``
     - 0.1.3
     - v0.1.3
   * - ``minor`` or ``[minor]``
     - 0.2.0
     - v0.2.0
   * - ``major`` or ``[major]``
     - 1.0.0
     - v1.0.0

The minimum target is calculated from the version on ``main``. A minor bump
resets patch to zero; a major bump resets minor and patch to zero. If a PR has
already been bumped to 0.1.3, adding ``minor`` changes it to 0.2.0. Repeating the
same run keeps that version. Removing a label never downgrades an already higher
candidate. Candidates behind main must first synchronize with main.

The bot commits synchronized changes to ``pyproject.toml``, ``uv.lock``, and
``.bumpversion.toml`` on the PR branch. Both test jobs and the version check use
the resulting commit SHA. If the bot creates a new commit, the final job records
the required GitHub Actions ``pr-gate`` check on that commit only after all
applicable checks succeed. This avoids depending on another bot-push workflow
run. The workflow requires ``contents: write`` for the bump and ``checks: write``
for that result; no additional personal token is needed.

Draft PRs are not bumped. Fork PRs cannot be pushed to by CI, so they must supply
a synchronized version meeting the selected increment before merging into main.

Main branch
-----------

Protect ``main`` with a repository ruleset or branch protection rule that
requires pull requests, requires the ``pr-gate`` status check, blocks force
pushes, and prevents deletion. Pushes to ``main`` should come from merges only.
When the post-merge CI run completes successfully for a push event on ``main``,
the ``Release`` workflow starts automatically from the exact commit SHA that CI
tested. A releasable commit must therefore have a synchronized
``pyproject.toml``, ``uv.lock``, and ``.bumpversion.toml``.

Publishing
----------

Production publishing is CI-success based for ``main``. Tag pushes matching
``v*`` remain available as an explicit manual release path. A tag must use the
exact form ``vX.Y.Z`` and must match the version in ``pyproject.toml``. For
automatic ``main`` releases, the release workflow resolves the version from the
tested commit and validates the matching bump configuration and lockfile.

The release workflow separates validation from publication. The ``validate`` job
runs the full release gate first and uploads only the verified distributions as
a GitHub Actions artifact. The ``tag-release`` job then creates the annotated
``vX.Y.Z`` tag on that exact validated commit. An existing tag must point to the
same commit; a conflicting tag stops publication and is never moved.

The ``publish`` job depends on validation and tag verification, downloads the
verified artifact by its immutable ID, and is the only job bound to the protected
``pypi`` environment. After PyPI publication succeeds, ``github-release`` creates
the GitHub release with the same tag and distribution files. Package metadata
uses ``X.Y.Z`` while the Git tag and GitHub release use the ``vX.Y.Z`` spelling.

Retries preserve the version and tag. Artifact IDs connect consumers to the
validation output even when failed jobs are rerun; full validation retries use
distinct artifact names. Runs for the same source commit are serialized.
Read the Docs builds from the merged source version as configured by its webhook.

The PyPI upload job uses GitHub OpenID Connect trusted publishing:

.. code-block:: text

   owner: waikato-ahuora-smart-energy-systems
   repository: OpenUtility
   workflow: release.yml
   environment: pypi

Configure the same ``pypi`` environment in GitHub and PyPI. Recommended GitHub
environment rules are required reviewers and deployment restrictions that allow
the ``main`` branch and release tags matching ``v*``.
