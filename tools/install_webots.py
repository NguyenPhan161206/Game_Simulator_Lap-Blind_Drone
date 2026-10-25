"""Install the official pinned Linux tarball under .local/; no system changes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tarfile
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = "R2025a"
URL = f"https://github.com/cyberbotics/webots/releases/download/{VERSION}/webots-{VERSION}-x86-64.tar.bz2"
INSTALL = ROOT / ".local" / f"webots-{VERSION}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Only report the local executable")
    args = parser.parse_args()
    executable = INSTALL / "webots" / "webots"
    if executable.is_file():
        print(executable)
        return 0
    if args.check:
        print("Pinned local Webots is not installed.", file=sys.stderr)
        return 1
    if sys.platform != "linux":
        raise SystemExit("This installer supports Linux x86_64; use the official package on other platforms.")
    import platform
    if platform.machine() != "x86_64":
        raise SystemExit("The pinned archive is for x86_64 only.")
    if shutil.disk_usage(ROOT).free < 2 * 1024**3:
        raise SystemExit("At least 2 GiB free disk space is required for this local installation.")
    downloads = ROOT / ".local/downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    archive = downloads / f"webots-{VERSION}-x86-64.tar.bz2"
    if not archive.exists():
        temporary = archive.with_suffix(".partial")
        print("Downloading official release:", URL, flush=True)
        try:
            with urllib.request.urlopen(URL, timeout=30) as response, temporary.open("wb") as destination:
                shutil.copyfileobj(response, destination, 1024 * 1024)
            temporary.replace(archive)
        except (OSError, urllib.error.URLError) as error:
            raise SystemExit(f"Download failed; no simulator validation was performed: {error}")
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    INSTALL.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive, "r:bz2") as bundle:
        bundle.extractall(INSTALL, filter="data")
    if not executable.is_file():
        raise SystemExit("Archive extracted but the expected Webots executable is missing.")
    metadata = {"version": VERSION, "source": URL, "sha256_downloaded_archive": digest,
                "note": "Digest records the downloaded bytes; no publisher digest was available in this preset."}
    (INSTALL / "installation.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
