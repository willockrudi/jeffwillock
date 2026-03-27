#!/usr/bin/env bash
# phase1_finish.sh
# Run once from the repo root to complete Phase 1 setup.
#
# Usage:
#   cd /path/to/jeffwillock
#   bash phase1_finish.sh

set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "=== Phase 1 Finish Script ==="
echo ""

# ── 1. Fix nav logo ──────────────────────────────────────────────────────────
echo "1) Patching nav logo to 'JC Custom Guitars'..."

OLD='JC<span>Custom</span>'
NEW='JC<span>Custom Guitars</span>'

for f in template.html project_template.html repairs_template.html index.html repairs.html music.html; do
  if [ -f "$f" ]; then
    sed -i "s|${OLD}|${NEW}|g" "$f"
    echo "   OK $f"
  fi
done

if ls projects/*.html 1>/dev/null 2>&1; then
  for f in projects/*.html; do
    sed -i "s|${OLD}|${NEW}|g" "$f"
    echo "   OK $f"
  done
fi

# ── 2. Merge style_additions.css into style.css ──────────────────────────────
echo ""
echo "2) Merging style_additions.css into style.css..."

if [ -f "style_additions.css" ]; then
  if ! grep -q "specs-table" style.css; then
    echo "" >> style.css
    cat style_additions.css >> style.css
    echo "   OK appended to style.css"
  else
    echo "   SKIP already merged"
  fi
  rm style_additions.css
  echo "   OK removed style_additions.css"
else
  echo "   SKIP style_additions.css not found"
fi

# ── 3. Fix repairs.json ───────────────────────────────────────────────────────
echo ""
echo "3) Checking repairs.json..."

if python3 -c "import json; json.load(open('repairs.json'))" 2>/dev/null; then
  echo "   OK repairs.json is valid"
else
  echo "   FIXING repairs.json (contains HTML, not JSON)"
  cp repairs.json repairs.json.bak
  echo "[]" > repairs.json
  echo "   OK reset to empty list (backup: repairs.json.bak)"
fi

# ── 4. Rebuild ────────────────────────────────────────────────────────────────
echo ""
echo "4) Rebuilding site..."

python3 - <<'PYEOF'
import sys, os
sys.path.insert(0, os.getcwd())
from manage import rebuild_all
rebuild_all()
print("   OK all pages rebuilt")
PYEOF

echo ""
echo "=== Phase 1 complete ==="
echo ""
echo "New commands in manage.py:"
echo "  17) input-guitar"
echo "  18) edit-guitar"
echo "  19) edit-guitar-story"
echo "  20) list-guitars"
echo "  21) delete-guitar"
echo ""
echo "Or use the web UI (command 16) - Add Guitar card is on the dashboard."
echo ""
