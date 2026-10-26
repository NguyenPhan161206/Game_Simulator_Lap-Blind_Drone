"""Compact, original v2 evidence through CI logs, including failed cases."""
import base64
import json
from pathlib import Path
import sys

root=Path(sys.argv[1])
if not root.exists():print("V2 output missing:",root);raise SystemExit(0)
print("V2_EVIDENCE_FILES",[(p.name,p.stat().st_size) for p in sorted(root.iterdir()) if p.is_file()])
result=root/"result.json"
if result.exists():print("V2_RESULT "+json.dumps(json.loads(result.read_text()),separators=(",",":")))
traces=root/"trajectories.json"
if traces.exists():
    values=json.loads(traces.read_text())
    for policy in ("reactive","guarded","mapped"):
        selected=next((t for t in values if "u_trap" in t["case_id"] and t["policy"]==policy),None)
        if selected:print("V2_TRACE "+json.dumps(selected,separators=(",",":")))
failures=root/"failures.json"
if failures.exists():
    values=json.loads(failures.read_text())
    for policy in ("reactive","guarded","mapped"):
        selected=next((f for f in values if "u_trap" in f["case_id"] and f["policy"]==policy),None)
        if selected:print("V2_FAILURE "+json.dumps(selected,separators=(",",":")))
image=root/"scene.jpg"
if image.exists() and image.stat().st_size<=1024*1024:
    encoded=base64.b64encode(image.read_bytes()).decode()
    for i,offset in enumerate(range(0,len(encoded),16000)):print(f"V2_JPEG_CHUNK {i}:"+encoded[offset:offset+16000])
