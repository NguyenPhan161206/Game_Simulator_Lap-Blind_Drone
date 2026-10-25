# Source instructions

Follow the root AGENTS.md and docs/architecture/data-contracts.md.
- Put simulator-specific device/world access only in blind_drone/adapters/webots.
- Navigation consumes explicitly constructed observations and the mission goal.
- Evaluation can inspect ground truth; it cannot enrich navigation inputs.
- Specify frames, units, timestamps and invalid-data handling before implementing interfaces.
- Module READMEs mark intended responsibilities, not implemented behavior.
