"""
watcher.py — JC Custom photo watcher
Watches a local folder for new photos every 30 seconds.
New photos are copied into: _Incoming/

The source folder is wherever Google Photos desktop app syncs to on the Mac.
Set WATCH_DIR below — confirm the exact path when at Jeff's computer.

Run:
    .venv/bin/python watcher.py

Stop:
    Ctrl+C
"""

import json
import shutil
import time
import logging
from datetime import datetime, timezone
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.resolve()

# Folder that Google Photos desktop app syncs to.
# Confirm the exact path on Jeff's Mac and update this line.
# Common locations:
#   Google Photos desktop app:  ~/Pictures/Google Photos
#   iCloud Photos originals:    ~/Pictures/Photos Library.photoslibrary/originals
#   Manual drop folder:         ~/Downloads
WATCH_DIR = Path.home() / "Pictures" / "Google Photos"

# Where new photos land for assignment
INCOMING_DIR = ROOT / "_Incoming"

# How often to check (seconds)
POLL_INTERVAL = 30

# File types to pick up
MEDIA_EXTENSIONS = {
    # Photos
    ".jpg", ".jpeg", ".png", ".heic", ".heif",
    ".gif", ".webp", ".tiff", ".tif", ".raw", ".dng",
    # Videos
    ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".wmv", ".3gp",
}
PHOTO_EXTENSIONS = MEDIA_EXTENSIONS  # alias — covers photos and videos

# Remembers which files have already been copied
STATE_PATH = ROOT / "state.json"

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("watcher")

# ── State helpers ─────────────────────────────────────────────────────────────

def load_state() -> dict:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"seen": [], "last_poll": None}


def save_state(state: dict):
    STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


# ── Core poll ─────────────────────────────────────────────────────────────────

def poll(state: dict) -> int:
    if not WATCH_DIR.exists():
        log.warning(f"Watch folder not found: {WATCH_DIR}")
        log.warning("Update WATCH_DIR in watcher.py once Google Photos desktop app is installed.")
        return 0

    seen: set = set(state.get("seen") or [])
    new_count = 0

    # Walk recursively — Google Photos organises into year/month subfolders
    for path in sorted(WATCH_DIR.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in PHOTO_EXTENSIONS:
            continue

        key = str(path)
        if key in seen:
            continue

        # Avoid overwriting files with the same name
        dest = INCOMING_DIR / path.name
        if dest.exists():
            stem, suffix = path.stem, path.suffix
            i = 2
            while dest.exists():
                dest = INCOMING_DIR / f"{stem}_{i}{suffix}"
                i += 1

        shutil.copy2(path, dest)
        seen.add(key)
        new_count += 1
        log.info(f"  +  {path.name}  ->  _Incoming/")

    # Keep seen list bounded
    state["seen"] = list(seen)[-10000:]
    state["last_poll"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    return new_count


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    log.info("JC Custom photo watcher starting")
    log.info(f"  Watching : {WATCH_DIR}")
    log.info(f"  Incoming : {INCOMING_DIR}")
    log.info(f"  Interval : {POLL_INTERVAL}s")

    INCOMING_DIR.mkdir(parents=True, exist_ok=True)

    if not WATCH_DIR.exists():
        log.warning("")
        log.warning("  Watch folder does not exist yet.")
        log.warning(f"  Expected: {WATCH_DIR}")
        log.warning("  Install Google Photos desktop app and sign in,")
        log.warning("  or update WATCH_DIR in watcher.py to the correct path.")
        log.warning("  Watcher will keep retrying every 30 seconds.")
        log.warning("")

    state = load_state()
    log.info("Running. Press Ctrl+C to stop.")
    print()

    while True:
        try:
            count = poll(state)
            if count:
                log.info(f"Poll complete — {count} new photo(s) copied to _Incoming/")
            else:
                log.info("Poll complete — no new photos")
        except KeyboardInterrupt:
            log.info("Stopped.")
            break
        except Exception as e:
            log.error(f"Poll error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
