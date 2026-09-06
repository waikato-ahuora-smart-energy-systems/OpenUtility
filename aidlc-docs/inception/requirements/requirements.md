# Release readiness requirements

The user approved the preceding five-step readiness plan with "go".
This is a small brownfield release-tooling and documentation correction.

- R1: The fresh wheel smoke test must import the installed distribution, even when launched from a checkout or with PYTHONPATH set.
- R2: Ship the advertised release tool in the source distribution.
- R3: Align README and changelog with candidate 0.1.2 and document PyPI installation.
- R4: Verify publishing account/project settings and use a confirmed RTD documentation URL when available.
- R5: Run the full release gate, including online audit and isolated installation.

No public optimization API or runtime dependency changes are required.
Existing security and resiliency extensions are disabled. PBT remains Partial;
PBT-01 through PBT-10 are N/A for this change: no new pure transformations,
serialization, algorithms, or stateful domain behavior; subprocess integration
is verified through deterministic regression tests and the installed-wheel gate.
