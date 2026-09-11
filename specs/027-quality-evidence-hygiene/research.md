# Research: Quality and Release Evidence Hygiene

The repository had package and citation version metadata but no changelog,
left `.hypothesis/` unignored, configured mutmut for only
`build_qualification.py`, and used Hypothesis in one test file. The fix keeps
the current `0.1.0` release while making the controls reproducible.
