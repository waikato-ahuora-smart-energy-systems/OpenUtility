Developer Checklist
===================

Install the package with development dependencies:

.. code-block:: bash

   python -m pip install -e ".[dev,docs,release]"

Run the full verification suite:

.. code-block:: bash

   python -m ruff check .
   python -m ruff format --check .
   python -m mypy OpenUtility
   python -m pytest --cov=OpenUtility --cov-report=term-missing --cov-fail-under=90
   python -m sphinx -W -b html docs /tmp/openutility-docs-html
   python -m build --no-isolation

Validate release metadata:

.. code-block:: bash

   python scripts/check_lockfile_version.py
   python scripts/check_release_version.py
   python scripts/check_release_tag.py v0.1.0

Run the single release gate:

.. code-block:: bash

   python tools/release_check.py

The release gate checks linting, formatting, typing, tests, docs, build
metadata, wheel contents, dependency audit, and a fresh-install smoke test.

The public test suite must not import or read private replication workflows.
Use small package-owned fixtures for reproducible tests.
