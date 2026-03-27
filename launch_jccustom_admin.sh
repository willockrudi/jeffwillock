#!/usr/bin/env bash
# launch_jccustom_admin.sh
# Starts all JC Custom services:
#   - manage.py web UI  (admin)    → http://127.0.0.1:8081
#   - dashboard_server.py          → http://127.0.0.1:8082
#   - watcher.py                   → watches _Incoming/ for new photos
#
# Double-click this file in the file manager to launch everything.

set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="$WORKDIR/.venv/bin/python"
ADMIN_LOG="/tmp/jeffwillock-admin.log"
DASHBOARD_LOG="/tmp/jeffwillock-dashboard.log"
WATCHER_LOG="/tmp/jeffwillock-watcher.log"
ADMIN_HOST="127.0.0.1"
ADMIN_PORT="8081"
DASH_PORT="8082"

# ── Create venv if missing ────────────────────────────────────────────────────
if [ ! -f "$PYTHON_BIN" ]; then
  echo "Creating .venv..."
  python3 -m venv "$WORKDIR/.venv"
  "$WORKDIR/.venv/bin/pip" install --quiet \
    google-auth-oauthlib google-auth-httplib2 \
    google-api-python-client requests
fi

cd "$WORKDIR"

# ── Start manage.py admin UI ──────────────────────────────────────────────────
if ! pgrep -f "manage.py web-ui ${ADMIN_HOST} ${ADMIN_PORT}" >/dev/null 2>&1; then
  echo "Starting admin UI..."
  nohup "$PYTHON_BIN" "$WORKDIR/manage.py" web-ui "$ADMIN_HOST" "$ADMIN_PORT" \
    >"$ADMIN_LOG" 2>&1 &
  sleep 1
else
  echo "Admin UI already running."
fi

# ── Start dashboard server ────────────────────────────────────────────────────
if ! pgrep -f "dashboard_server.py" >/dev/null 2>&1; then
  echo "Starting dashboard..."
  nohup "$PYTHON_BIN" "$WORKDIR/dashboard_server.py" \
    >"$DASHBOARD_LOG" 2>&1 &
  sleep 1
else
  echo "Dashboard already running."
fi

# ── Start photo watcher ───────────────────────────────────────────────────────
if ! pgrep -f "watcher.py" >/dev/null 2>&1; then
  echo "Starting photo watcher..."
  nohup "$PYTHON_BIN" "$WORKDIR/watcher.py" \
    >"$WATCHER_LOG" 2>&1 &
  sleep 1
else
  echo "Watcher already running."
fi

echo ""
echo "All services running."
echo "  Admin UI  : http://${ADMIN_HOST}:${ADMIN_PORT}"
echo "  Dashboard : http://127.0.0.1:${DASH_PORT}"
echo "  Logs      : $ADMIN_LOG"
echo "             $DASHBOARD_LOG"
echo "             $WATCHER_LOG"
echo ""

# ── Open dashboard in browser ─────────────────────────────────────────────────
sleep 1
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:${DASH_PORT}/" >/dev/null 2>&1 &
fi
