# Isoprax Agent Guidance

## Authority and scope

- The authoritative Isoprax v0.3 POC is the specification and Stage 0
  reference implementation baseline for this repository.
- The project-local `.specify/memory/constitution.md` governs project decisions.
- Use external reference material only where the authoritative Isoprax
  specification explicitly calls for reusable research hygiene. Do not import
  third-party corpus-admission, JEPA/profile, or evaluation assumptions by
  inference.

## Delivery rules

- Use Spec Kit for complex work: specify, plan, tasks, implement, then converge.
- Preserve the Structural/Semantic conformance distinction. Calibration alone
  never permits comparing non-commensurable cross-family scores.
- Keep Stage 0 claims synthetic and structural. Record only verification that
  was actually obtained.
- Use `uv` for Python environments, dependencies, and execution.
- Prefer focused conformance tests and the documented synthetic demo before
  broader validation.

## Repository layout

- Root `AGENTS.md` holds shared project instructions.
- `.agents/skills/` holds the Codex-integrated Spec Kit skills.
- `.specify/` holds Spec Kit state and feature artifacts.
