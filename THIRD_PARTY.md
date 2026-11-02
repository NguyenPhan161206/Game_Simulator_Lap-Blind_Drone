# Third-party provenance

No simulator implementation, third-party robot mesh, dataset or trained weights are vendored. The prototype drone geometry and controllers are original project code. Webots itself is downloaded separately into ignored .local/ when installation is available.

| Component | Intended use | Source | License/status |
|---|---|---|---|
| Webots | Simulator runtime | https://github.com/cyberbotics/webots/releases/tag/R2025a | Engine: Apache-2.0; pinned R2025a; local/CI installation evidence reported separately |
| Webots Mavic example | Candidate reference only | https://github.com/cyberbotics/webots/tree/master/projects/robots/dji/mavic | Model header restricts use to Webots; not copied |
| GitHub Actions download-artifact | CI-only download of prior/validation raw evidence; no code vendored | https://github.com/actions/download-artifact/tree/v4 | Workflow revision `v4`, resolved SHA `d3f86a106a0bac45b974a628896c90dbdf5c8093` in preflight CI41389837671; MIT, https://raw.githubusercontent.com/actions/download-artifact/v4/LICENSE ; resolved action SHA is retained in CI setup logs |
| Snake_ANN | Historical inspiration/source audit | https://github.com/NguyenPhan161206/Snake_ANN | No source imported; see the discussion record |

Before importing anything, record the exact revision, files, license, modifications and attribution. An engine's license does not automatically cover every bundled asset.

The owner has not selected a license for this project's original code. Public repository visibility alone does not assign an open-source license.

API references inspected at tag R2025a: docs/reference/propeller.md, distancesensor.md, inertialunit.md, supervisor.md, physics.md, plus src/webots/nodes/WbPropeller.cpp (reaction torque sign). These references informed original implementation; no source snippets or Mavic controller/mesh were copied. The archive installer records its source URL and downloaded-byte SHA-256 in ignored local metadata.
