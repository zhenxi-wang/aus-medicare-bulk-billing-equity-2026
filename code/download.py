"""Retrieve or verify the two frozen public Medicare inputs."""
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen
import json

DATA = Path(__file__).resolve().parents[1] / "data"
WORKBOOKS = {"seifa.xlsx", "primary.xlsx"}

for entry in json.loads((DATA / "download_manifest.json").read_text(encoding="utf-8")):
    if entry["file"] not in WORKBOOKS:
        continue
    target = DATA / entry["file"]
    if target.exists():
        content = target.read_bytes()
    else:
        request = Request(entry["url"], headers={"User-Agent": "Mozilla/5.0 Medicare research"})
        with urlopen(request, timeout=120) as response:
            content = response.read()
    if len(content) != entry["bytes"] or sha256(content).hexdigest() != entry["sha256"]:
        raise SystemExit(f"Checksum or size mismatch for {target.name}. See data/README.md.")
    if not target.exists():
        temporary = target.with_suffix(".download")
        temporary.write_bytes(content)
        temporary.replace(target)
    print(f"Verified {target.name} ({len(content):,} bytes)")
