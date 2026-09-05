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
* fresh wheel-install smoke tests with HiGHS solves.

CI also exposes an explicit ``pr-gate`` job for GitHub branch protection. That
job depends on the complete pytest suite, the full release gate, and the
applicable release-version checks. Configure ``main`` so pull requests cannot be
merged until ``pr-gate`` succeeds.

For same-repository pull requests targeting ``main``, CI also maintains the
candidate release version. The version bump is selected from labels named
``major``, ``minor``, or ``patch``. If no label is present, CI also accepts
``[major]``, ``[minor]``, or ``[patch]`` in the pull-request title. The default
is ``patch``.

The bump job runs only when the pull-request branch has the same version as the
base branch. If the branch already carries a forward version, CI validates it
instead of bumping again. Fork pull requests cannot be pushed to by CI, so they
must provide a forward version manually before merging into ``main``.

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
automatic ``main`` releases, the release workflow validates the project version
directly.

The release workflow separates validation from publication. The ``validate`` job
runs the full release gate first and uploads only the verified distributions as
a GitHub Actions artifact. The ``publish`` job depends on ``validate``, downloads
that artifact, and is the only job bound to the protected ``pypi`` environment.

The PyPI upload job uses GitHub OpenID Connect trusted publishing:

.. code-block:: text

   owner: waikato-ahuora-smart-energy-systems
   repository: OpenUtility
   workflow: release.yml
   environment: pypi

Configure the same ``pypi`` environment in GitHub and PyPI. Recommended GitHub
environment rules are required reviewers and deployment restrictions that allow
the ``main`` branch and release tags matching ``v*``.
