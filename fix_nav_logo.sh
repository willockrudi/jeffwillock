#!/usr/bin/env bash
# fix_nav_logo.sh
# Run once from the repo root to rename the nav logo to "JC Custom Guitars"
# everywhere in the project.
#
# Usage:
#   cd /path/to/jeffwillock
#   bash fix_nav_logo.sh

set -euo pipefail

OLD='JC<span>Custom</span>'
NEW='JC<span>Custom Guitars</span>'

FILES=(
  template.html
  project_template.html
  repairs_template.html
  index.html
  repairs.html
  music.html
)

echo "Patching nav logo..."

for f in "${FILES[@]}"; do
  if [ -f "$f" ]; then
    sed -i "s|${OLD}|${NEW}|g" "$f"
    echo "  ✅ $f"
  else
    echo "  ⚠️  $f not found — skipped"
  fi
done

# Also patch any existing generated project pages
for f in projects/*.html guitars/*.html 2>/dev/null; do
  if [ -f "$f" ]; then
    sed -i "s|${OLD}|${NEW}|g" "$f"
    echo "  ✅ $f"
  fi
done

echo ""
echo "Done. Run 'python3 manage.py' → rebuild to regenerate all pages cleanly."
