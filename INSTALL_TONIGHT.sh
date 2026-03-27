#!/usr/bin/env bash
# INSTALL_TONIGHT.sh
# Master install script — run this once on Jeff's computer.
# Does everything: nav fixes, CSS merge, venv, nav links, cron, autostart.
#
# Usage:
#   cd ~/Documents/dev/my_websites/jeffwillock
#   bash INSTALL_TONIGHT.sh

set -euo pipefail
REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

echo ""
echo "======================================"
echo "  JC Custom Guitars — Full Install"
echo "======================================"
echo ""

# ── 1. Fix nav logo everywhere ────────────────────────────────────────────────
echo "1) Fixing nav logo..."
OLD='JC<span>Custom</span>'
NEW='JC<span>Custom Guitars</span>'
for f in template.html project_template.html repairs_template.html \
          index.html repairs.html music.html guitar_template.html guitars_template.html; do
  [ -f "$f" ] && sed -i "s|${OLD}|${NEW}|g" "$f" && echo "   OK $f"
done
if ls projects/*.html 1>/dev/null 2>&1; then
  for f in projects/*.html; do
    sed -i "s|${OLD}|${NEW}|g" "$f" && echo "   OK $f"
  done
fi

# ── 2. Add Guitars nav link to all templates ──────────────────────────────────
echo ""
echo "2) Adding Guitars nav link..."
OLD_NAV='<li><a href="repairs.html">Repairs</a></li>'
NEW_NAV='<li><a href="repairs.html">Repairs</a></li>
      <li><a href="guitars.html">Guitars</a></li>'
OLD_NAV_SUB='<li><a href="../repairs.html">Repairs</a></li>'
NEW_NAV_SUB='<li><a href="../repairs.html">Repairs</a></li>
      <li><a href="../guitars.html">Guitars</a></li>'

for f in template.html repairs_template.html index.html repairs.html music.html; do
  if [ -f "$f" ] && ! grep -q 'href="guitars.html"' "$f"; then
    sed -i "s|${OLD_NAV}|${NEW_NAV}|g" "$f"
    echo "   OK $f"
  fi
done
for f in project_template.html; do
  if [ -f "$f" ] && ! grep -q 'guitars.html' "$f"; then
    sed -i "s|${OLD_NAV_SUB}|${NEW_NAV_SUB}|g" "$f"
    echo "   OK $f"
  fi
done
if ls projects/*.html 1>/dev/null 2>&1; then
  for f in projects/*.html; do
    if ! grep -q 'guitars.html' "$f"; then
      sed -i "s|${OLD_NAV_SUB}|${NEW_NAV_SUB}|g" "$f"
      echo "   OK $f"
    fi
  done
fi

# ── 3. Merge style_additions.css ─────────────────────────────────────────────
echo ""
echo "3) Merging styles..."
if [ -f "style_additions.css" ]; then
  if ! grep -q "specs-table" style.css; then
    echo "" >> style.css
    cat style_additions.css >> style.css
    echo "   OK merged into style.css"
  else
    echo "   SKIP already merged"
  fi
  rm style_additions.css
fi

# ── 4. Fix repairs.json if corrupt ───────────────────────────────────────────
echo ""
echo "4) Checking repairs.json..."
if python3 -c "import json; json.load(open('repairs.json'))" 2>/dev/null; then
  echo "   OK valid"
else
  cp repairs.json repairs.json.bak
  echo "[]" > repairs.json
  echo "   FIXED (was corrupt, reset to empty list)"
fi

# ── 5. Create/repair venv ─────────────────────────────────────────────────────
echo ""
echo "5) Setting up Python venv..."
if [ ! -f "$REPO/.venv/bin/python" ] || \
   ! "$REPO/.venv/bin/python" -c "import sys; sys.exit(0 if sys.prefix != sys.base_prefix else 1)" 2>/dev/null; then
  echo "   Creating fresh .venv..."
  rm -rf "$REPO/.venv"
  python3 -m venv "$REPO/.venv"
  echo "   OK created"
else
  echo "   OK exists"
fi

# ── 6. Install Python dependencies ───────────────────────────────────────────
echo ""
echo "6) Installing Python dependencies..."
"$REPO/.venv/bin/pip" install --quiet --upgrade pip
"$REPO/.venv/bin/pip" install --quiet \
  google-auth-oauthlib google-auth-httplib2 \
  google-api-python-client requests
echo "   OK"

# ── 7. Make scripts executable ────────────────────────────────────────────────
echo ""
echo "7) Setting permissions..."
chmod +x launch_jccustom_admin.sh watcher.py dashboard_server.py storage_check.py
echo "   OK"

# ── 8. Create _Incoming folder ────────────────────────────────────────────────
echo ""
echo "8) Creating _Incoming/ folder..."
mkdir -p "$REPO/_Incoming"
echo "   OK"

# ── 9. Full rebuild ───────────────────────────────────────────────────────────
echo ""
echo "9) Rebuilding all site pages..."
"$REPO/.venv/bin/python" - << 'PYEOF'
import sys, os
sys.path.insert(0, os.getcwd())
from manage import rebuild_all
rebuild_all()
print("   OK all pages rebuilt")
PYEOF

# ── 10. Autostart on login ────────────────────────────────────────────────────
echo ""
echo "10) Setting up autostart on login..."
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
DESKTOP
echo "   OK $AUTOSTART_DIR/jccustom.desktop"

# ── 11. Desktop shortcut ──────────────────────────────────────────────────────
echo ""
echo "11) Creating desktop shortcut..."
cp "$AUTOSTART_DIR/jccustom.desktop" "$HOME/Desktop/JC Custom Guitars.desktop"
chmod +x "$HOME/Desktop/JC Custom Guitars.desktop"
echo "   OK ~/Desktop/JC Custom Guitars.desktop"

# ── 12. Cron jobs ─────────────────────────────────────────────────────────────
echo ""
echo "12) Installing cron jobs..."
TMPFILE="$(mktemp)"
crontab -l 2>/dev/null > "$TMPFILE" || true
grep -v "jeffwillock" "$TMPFILE" > "${TMPFILE}.new" || true
mv "${TMPFILE}.new" "$TMPFILE"
cat >> "$TMPFILE" << CRON
# JC Custom — nightly auto-publish at midnight
0 0 * * * cd $REPO && $REPO/.venv/bin/python -c "from manage import publish_to_github_noninteractive; publish_to_github_noninteractive('nightly auto-publish')" >> /tmp/jeffwillock-cron.log 2>&1
# JC Custom — storage check every hour
0 * * * * $REPO/.venv/bin/python $REPO/storage_check.py >> /tmp/jeffwillock-storage.log 2>&1
CRON
crontab "$TMPFILE"
rm "$TMPFILE"
echo "   OK midnight publish + hourly storage check"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "======================================"
echo "  Install complete ✅"
echo "======================================"
echo ""
echo "  To start everything now:"
echo "    bash launch_jccustom_admin.sh"
echo ""
echo "  URLs:"
echo "    Admin UI  : http://127.0.0.1:8081"
echo "    Dashboard : http://127.0.0.1:8082"
echo ""
echo "  Photo watcher:"
echo "    Once Google Photos desktop app is installed,"
echo "    update WATCH_DIR in watcher.py then restart."
echo ""
echo "  On Jeff's iPad:"
echo "    Open Safari → http://[this machine's IP]:8082"
echo "    Share → Add to Home Screen"
echo ""
