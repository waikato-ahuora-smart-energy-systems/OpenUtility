Jupyter examples
================

These six independent tutorials use small synthetic systems and the public
OpenUtility API. Each includes assumptions, units, tables, plots, and assertions
against analytical costs or energy balances. Start with the first two, then
choose the topics you need. The data illustrate model behavior rather than
representing a particular industrial site.

Install and run
---------------

Use Python 3.14.2 or newer and install the notebook extra:

.. code-block:: console

   python -m pip install "OpenUtility[notebook]>=0.1.2"
   python -m jupyterlab

Download a notebook below, open it in JupyterLab, select that environment's
Python kernel, and choose **Restart Kernel and Run All Cells**. HiGHS is included
in the package dependencies. No external files, private case studies, repository
checkout, or commercial solver are required. Notebooks also contain saved
example outputs for inspection before execution.

Tutorials
---------

.. list-table:: Public tutorial sequence
   :header-rows: 1
   :widths: 28 45 27

   * - Notebook
     - What you learn
     - Checkable result
   * - :download:`01 Quick start <notebooks/01_quick_start.ipynb>`
     - Build a model, solve with HiGHS, and extract a result table.
     - 100 kW grid demand costs 60,000 CU/year.
   * - :download:`02 Equipment selection <notebooks/02_equipment_selection.ipynb>`
     - Compare capital investment, fuel, and grid purchases.
     - Investing in the turbine reduces cost to 52,000 CU/year.
   * - :download:`03 Scenario analysis <notebooks/03_scenario_analysis.ipynb>`
     - Sweep electricity prices and demand; plot cost and fuel use.
     - Break-even tariffs agree with an analytical calculation.
   * - :download:`04 Heat pump <notebooks/04_heat_pump.ipynb>`
     - Define a performance map and connect waste heat to heating demand.
     - 100 kW source heat plus 50 kW electricity supplies 150 kW heat.
   * - :download:`05 Refrigeration and periods <notebooks/05_refrigeration_periods.ipynb>`
     - Share one investment across periods and optimize cooling dispatch.
     - Chiller runs at night; backup cooling supplies the peak period.
   * - :download:`06 Binary decomposition <notebooks/06_binary_decomposition.ipynb>`
     - Enumerate investment choices, apply no-good cuts, and track incumbents.
     - Best cost matches the monolithic MILP at 52,000 CU/year.

CU denotes arbitrary currency units. Electricity and fuel prices use CU/kWh;
power and thermal duties use kW. Each notebook explains any additional units.
The electricity examples use a zero-duty steam-level placeholder because the
current input schema requires a steam main. HPR examples use period hours for
energy costs and leave the static electricity subsystem idle.

The advanced notebook demonstrates the public binary-selection decomposition
helpers. It distinguishes exhausting a small candidate menu from convergence
based on a valid optimality bound. It does not reproduce a private thermodynamic
bilevel study.

Execution checks
----------------

CI and release validation build the wheel, install its notebook extra into a
fresh environment, and run every example in a separate kernel and empty working
directory. An assertion inside each kernel verifies that OpenUtility comes from
that installed environment. Every code cell executes; stale saved outputs cannot
make a failing notebook pass. Failures block the corresponding workflow gate.

The ``openutility-notebook-examples`` workflow artifact contains executed
notebooks and HTML previews. To reproduce this check from a checkout after
building the wheel:

.. code-block:: bash

   uv venv /tmp/openutility-examples
   wheels=(dist/*.whl)
   uv pip install --python /tmp/openutility-examples/bin/python "${wheels[0]}[notebook]"
   /tmp/openutility-examples/bin/python -I tools/check_notebooks.py \
       --output-dir /tmp/openutility-example-results

The checker writes outputs only to the requested directory. Keep that directory
outside the notebook source directory when verifying changes.
