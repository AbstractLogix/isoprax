# Implementation Plan: Quality and Release Evidence Hygiene

Add `CHANGELOG.md` and a test that matches its release heading to the package
version. Ignore `.hypothesis/`, remove the mutmut single-module restriction,
run mutation tests against all package modules and repository tests, and add a
Hypothesis property for predeclaration identity stability.
