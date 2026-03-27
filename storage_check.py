"""
storage_check.py — JC Custom storage warning
Run hourly by cron. Sends a desktop notification if _Incoming/ has
50+ photos waiting to be assigned.
"""

import os
import subprocess
from pathlib import Path

ROOT         = Path(__file__).parent.resolve()
INCOMING_DIR = ROOT / "_Incoming"
WARN_LIMIT   = 50

PHOTO_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".gif", ".webp", ".tiff", ".tif"}

def count_incoming() -> int:
    if not INCOMING_DIR.exists():
        return 0
    return sum(
        1 for f in INCOMING_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in PHOTO_EXTENSIONS
    )

def notify(title: str, message: str):
    """Send a desktop notification (works on Linux with libnotify)."""
    try:
        subprocess.run(
            ["notify-send", "--urgency=normal", "--icon=dialog-warning", title, message],
            timeout=5,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Also print so cron log captures it
    print(f"[storage_check] {title}: {message}")

def main():
    count = count_incoming()
    print(f"[storage_check] _Incoming/ has {count} photo(s)")

    if count >= WARN_LIMIT:
        notify(
            "JC Custom — Photos Waiting",
            f"{count} photos in _Incoming/ need to be assigned. Open the dashboard."
        )

if __name__ == "__main__":
    main()
