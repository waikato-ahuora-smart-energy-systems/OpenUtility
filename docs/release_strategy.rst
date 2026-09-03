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

CI also exposes an explicit ``all-tests`` job for GitHub branch protection. That
job runs the complete pytest suite with the package coverage threshold, and the
broader ``release-gate`` job depends on it.

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

Pushes to ``main`` run the same release gate. A releasable commit must therefore
have a synchronized ``pyproject.toml``, ``uv.lock``, and ``.bumpversion.toml``.

Publishing
----------

Production publishing is tag based. A tag must use the exact form ``vX.Y.Z`` and
must match the version in ``pyproject.toml``. The release workflow validates the
tag before running the release gate or publishing.

The tag workflow separates validation from publication. The ``validate`` job
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
environment rules are required reviewers and deployment restrictions for release
tags matching ``v*``.
