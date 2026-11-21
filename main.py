#!/usr/bin/env python3
"""Write the fixed Saturday 21 November 2026 news image to /output/entry.png.

The grader runs this file with no network. Both runs must produce identical bytes.
This program only copies the pre-rendered poster beside this file; it does not
draw, fetch, or call any image model.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "assets" / "entry.png"
DEST = Path("/output") / "entry.png"


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"missing fixed image: {SOURCE}")
    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, DEST)


if __name__ == "__main__":
    main()
