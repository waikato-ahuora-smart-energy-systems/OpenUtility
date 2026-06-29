Developer Checklist
===================

Install the package with development dependencies:

.. code-block:: bash

   python -m pip install -e ".[dev]"

Run the full verification suite:

.. code-block:: bash

   python -m pytest
   python -m ruff check .

Run the notebook workflow test directly:

.. code-block:: bash

   python -m pytest tests/test_notebook_workflow.py

Build the Read the Docs source locally:

.. code-block:: bash

   python -m sphinx -b html docs /tmp/openutility-docs-html

Recreate the calibrated benchmark comparison report:

.. code-block:: bash

   openutility-style-table2-9 --catalog physical-profile --apply-fuel-targets --apply-operating-targets --format csv

Open the checked notebook example:

.. code-block:: bash

   jupyter lab examples/notebooks/style_table_2_9_case_study.ipynb
