# Quickstart: Runner Scope

Integrators provide a `RunnerBackend` to `run_prepared_execution`. The
reference implementation checks the returned controls and records the result;
it does not select or start Docker, Podman, a registry, or a host runtime.
