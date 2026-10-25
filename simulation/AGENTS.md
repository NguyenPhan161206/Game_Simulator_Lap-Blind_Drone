# Simulation instructions

Follow the root AGENTS.md.
- Keep world geometry, collision geometry and sensing consistent.
- Declare which measurements are idealized, noisy, delayed or unavailable.
- Remove runtime image devices from the evaluated configuration; observer rendering is separate.
- Audit sample controllers for privileged-state and camera access before reuse.
- Record version and per-asset licenses before copying external worlds/models.
- A world loading successfully and a drone navigating successfully are separate checks.
