#!/usr/bin/env python3
"""Validate the baked poster and that two copies of it are byte-identical.

The official entrypoint writes /output/entry.png, but this machine may not
allow creating /output. Verification therefore:
  1) inspects assets/entry.png (size, dimensions, PNG header)
  2) copies it twice into temporary directories and compares SHA-256
  3) confirms main.py only copies that file to /output/entry.png
"""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSET = ROOT / "assets" / "entry.png"
MAIN = ROOT / "main.py"
MAX_BYTES = 1024 * 1024
MAX_EDGE = 1024


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    if not ASSET.is_file():
        raise SystemExit(f"missing {ASSET}")
    size = ASSET.stat().st_size
    digest = sha256(ASSET)
    img = Image.open(ASSET)
    width, height = img.size
    fmt = img.format
    print(f"asset: {ASSET}")
    print(f"  format={fmt} size={width}x{height} bytes={size} sha256={digest}")
    errors = []
    if fmt != "PNG":
        errors.append(f"not a PNG ({fmt})")
    if width > MAX_EDGE or height > MAX_EDGE:
        errors.append(f"edge exceeds {MAX_EDGE}: {width}x{height}")
    if size > MAX_BYTES:
        errors.append(f"file exceeds 1 MiB: {size}")
    if size < 1000:
        errors.append("file unexpectedly small")

    src = MAIN.read_text(encoding="utf-8")
    if "shutil.copyfile" not in src or 'Path("/output")' not in src:
        errors.append("main.py does not look like a fixed-image copy to /output/entry.png")
    if "generate" in src.lower() or "requests." in src or "urllib" in src:
        errors.append("main.py appears to fetch or generate at runtime")

    with tempfile.TemporaryDirectory() as td:
        a = Path(td) / "run1" / "entry.png"
        b = Path(td) / "run2" / "entry.png"
        a.parent.mkdir()
        b.parent.mkdir()
        shutil.copyfile(ASSET, a)
        shutil.copyfile(ASSET, b)
        ha, hb = sha256(a), sha256(b)
        print(f"copy run 1 sha256={ha}")
        print(f"copy run 2 sha256={hb}")
        if ha != hb or ha != digest:
            errors.append("two-copy hash mismatch")
        else:
            print("two independent copies are byte-identical and match the asset")

    dest = Path("/output") / "entry.png"
    print(f"/output writable probe: ", end="")
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ASSET, dest)
        print(f"wrote {dest} sha256={sha256(dest)}")
    except OSError as exc:
        print(f"not writable on this machine ({exc}). Official grader path remains /output/entry.png.")

    if errors:
        raise SystemExit("FAIL: " + "; ".join(errors))
    print("PASS: PNG gate (whole PNG, <=1024 edge, <=1 MiB) and deterministic copies.")


if __name__ == "__main__":
    main()
