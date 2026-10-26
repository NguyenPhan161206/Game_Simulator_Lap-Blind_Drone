"""Expose small generated observer evidence through CI logs for review."""
import base64
import json
from pathlib import Path
import sys

output = Path(sys.argv[1])
if not output.exists():
    print("No simulator output directory")
    raise SystemExit(0)
print("EVIDENCE_FILES", [(p.name, p.stat().st_size) for p in sorted(output.iterdir()) if p.is_file()])
for name in ("progress.json", "result.json"):
    path = output / name
    if path.exists():
        print("EVIDENCE_JSON " + name + " " + json.dumps(json.loads(path.read_text())))
telemetry = output / "telemetry.jsonl"
if telemetry.exists():
    lines = telemetry.read_text().splitlines()
    if lines:
        print("LAST_TELEMETRY " + lines[-1])
trajectories = output / "trajectories.json"
if trajectories.exists():
    traces = json.loads(trajectories.read_text())
    for family in ("u_trap","narrow_gap"):
        chosen = next((t for t in traces if family in t["case_id"] and t["policy"]=="reactive"),None)
        if chosen:
            print("REVIEW_TRAJECTORY " + json.dumps(chosen,separators=(",",":")))
image = output / "scene.jpg"
if image.exists() and image.stat().st_size <= 1024 * 1024:
    encoded = base64.b64encode(image.read_bytes()).decode()
    for index, offset in enumerate(range(0, len(encoded), 16000)):
        print(f"OBSERVER_JPEG_CHUNK {index}:" + encoded[offset:offset+16000])
