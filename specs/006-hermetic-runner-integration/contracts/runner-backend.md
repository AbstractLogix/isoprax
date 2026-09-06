# Runner Backend Contract

The runner backend is the single effect boundary. It receives a prepared commit and approved configuration and returns facts observed before and after command execution; it must not mutate the preparation or configuration.

## Input

- `commit`: one commit from a non-blocked `BuildPreparation`.
- `recipe_reference`: the preparation's frozen recipe reference.
- `configuration`: the immutable `ApprovedRunnerConfiguration`.

## Result facts

The backend result supplies:

- effective controls: immutable identity, frozen command, prepared source commit, non-root, source-read-only, work-storage-isolated, network-disabled, timeout, and resource limits;
- `command_started`: boolean;
- terminal `outcome`: `success`, `build_failed`, `timeout`, `interrupted`, or `unavailable`;
- diagnostic reason and non-negative duration in milliseconds;
- a mapping from declared artifact paths to bytes or an explicit unreadable marker; non-byte payloads are retained as unreadable evidence.

## Required behavior

- If any effective control is absent or differs from the approved configuration, the integration returns `blocked-before-compilation`; `command_started` must be false.
- `unavailable` with no command start is `blocked-before-compilation`.
- A non-success outcome after command start is `censored`.
- A `success` outcome requires command start and remains separate from artifact collection state.
- Backend exceptions are treated as unavailable infrastructure and retained as `blocked-before-compilation`.
