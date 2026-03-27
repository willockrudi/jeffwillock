#!/usr/bin/env bash
# install_phase4.sh
# Sets up auto-start on login and cron jobs for JC Custom.
#
# Run once from the repo root:
#   bash install_phase4.sh

set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$WORKDIR/.venv/bin/python"
REPO="$WORKDIR"

echo ""
echo "=== JC Custom Phase 4 Install ==="
echo ""

# ── 1. Auto-start on login (.desktop in autostart) ───────────────────────────
echo "1) Setting up auto-start on login..."

AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/jccustom.desktop" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=JC Custom Guitars
Comment=Launch JC Custom shop dashboard
Exec=bash $REPO/launch_jccustom_admin.sh
Icon=$REPO/images/logo.png
Terminal=false
StartupNotify=false
Categories=Utility;
DESKTOP

echo "   OK autostart entry created: $AUTOSTART_DIR/jccustom.desktop"

# ── 2. Desktop shortcut ───────────────────────────────────────────────────────
echo ""
echo "2) Creating desktop shortcut..."

DESKTOP_FILE="$HOME/Desktop/JC Custom Guitars.desktop"
cp "$AUTOSTART_DIR/jccustom.desktop" "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"
echo "   OK desktop shortcut: $DESKTOP_FILE"

# ── 3. Cron jobs ──────────────────────────────────────────────────────────────
echo ""
echo "3) Installing cron jobs..."

# Export existing crontab (ignore error if empty)
TMPFILE="$(mktemp)"
crontab -l 2>/dev/null > "$TMPFILE" || true

# Remove old JC Custom cron entries if present
grep -v "jeffwillock" "$TMPFILE" > "${TMPFILE}.clean" || true
mv "${TMPFILE}.clean" "$TMPFILE"

# Nightly auto-publish at midnight
cat >> "$TMPFILE" << CRON
# JC Custom — nightly auto-publish at midnight
0 0 * * * cd $REPO && $PYTHON_BIN -c "from manage import publish_to_github_noninteractive; publish_to_github_noninteractive('nightly auto-publish')" >> /tmp/jeffwillock-cron.log 2>&1

# JC Custom — storage check every hour (warns if _Incoming has 50+ photos)
0 * * * * $REPO/.venv/bin/python $REPO/storage_check.py >> /tmp/jeffwillock-storage.log 2>&1
CRON

crontab "$TMPFILE"
rm "$TMPFILE"

echo "   OK cron jobs installed"
echo "   - Nightly publish: midnight every day"
echo "   - Storage check:   every hour"

# ── 4. Make launch script executable ─────────────────────────────────────────
echo ""
echo "4) Making scripts executable..."
chmod +x "$REPO/launch_jccustom_admin.sh"
chmod +x "$REPO/watcher.py"
chmod +x "$REPO/dashboard_server.py"
echo "   OK"

echo ""
echo "=== Phase 4 complete ==="
echo ""
echo "Auto-start:  Enabled — all services start when rudi logs in"
echo "Desktop:     Double-click 'JC Custom Guitars' on the desktop"
echo "Cron:        Nightly publish at midnight, storage check hourly"
echo ""
echo "To start everything right now:"
echo "  bash launch_jccustom_admin.sh"
echo ""
