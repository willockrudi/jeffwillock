#!/bin/bash
# =============================================================================
# JC CUSTOM GUITARS - ONE-TIME SETUP
# =============================================================================
# Run this script ONCE to set everything up:
#   bash setup.sh
#
# This will:
# 1. Create the JC Custom Guitars folder
# 2. Install the admin app on Desktop
# 3. Optionally enable auto-start on login
# 4. Show iPhone setup instructions
# =============================================================================

set -e

echo ""
echo "🎸 JC CUSTOM GUITARS - SETUP"
echo "============================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# =============================================================================
# 1. CHECK PYTHON
# =============================================================================
echo "Checking Python..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ $PYTHON_VERSION"
else
    echo "   ❌ Python not found!"
    echo ""
    echo "Please install Python:"
    echo "   1. Go to: https://www.python.org/downloads/"
    echo "   2. Download and install Python 3"
    echo "   3. Run this setup again"
    echo ""
    exit 1
fi

# =============================================================================
# 2. FIND OR CREATE GOOGLE DRIVE FOLDER
# =============================================================================
echo ""
echo "Looking for Google Drive..."

JC_FOLDER=""

# Check common Google Drive locations
for path in "$HOME/Google Drive/My Drive/JC Custom Guitars" \
            "$HOME/Google Drive/JC Custom Guitars" \
            "$HOME/Library/CloudStorage"/GoogleDrive-*/My\ Drive/JC\ Custom\ Guitars; do
    if [ -d "$path" ]; then
        JC_FOLDER="$path"
        break
    fi
done

# Check if Google Drive base exists
DRIVE_BASE=""
for path in "$HOME/Google Drive/My Drive" \
            "$HOME/Google Drive" \
            "$HOME/Library/CloudStorage"/GoogleDrive-*/My\ Drive; do
    if [ -d "$path" ]; then
        DRIVE_BASE="$path"
        break
    fi
done

if [ -n "$DRIVE_BASE" ] && [ -z "$JC_FOLDER" ]; then
    JC_FOLDER="$DRIVE_BASE/JC Custom Guitars"
    mkdir -p "$JC_FOLDER"
    echo "   ✅ Created: $JC_FOLDER"
elif [ -n "$JC_FOLDER" ]; then
    echo "   ✅ Found: $JC_FOLDER"
else
    echo "   ⚠️  Google Drive not found"
    JC_FOLDER="$HOME/JC Custom Guitars"
    mkdir -p "$JC_FOLDER"
    echo "   📁 Using local folder: $JC_FOLDER"
    echo ""
    echo "   To enable cloud sync later:"
    echo "   1. Install Google Drive: https://www.google.com/drive/download/"
    echo "   2. Move your folder to Google Drive"
fi

# Create data folder
mkdir -p "$JC_FOLDER/_site_data"

# =============================================================================
# 3. INSTALL MANAGE.PY
# =============================================================================
echo ""
echo "Installing admin server..."

cp "$SCRIPT_DIR/manage.py" "$JC_FOLDER/manage.py"
echo "   ✅ Installed: $JC_FOLDER/manage.py"

# =============================================================================
# 4. CREATE DESKTOP APP
# =============================================================================
echo ""
echo "Creating desktop app..."

APP_NAME="JC Custom Guitars"
APP_PATH="$HOME/Desktop/$APP_NAME.app"

# Remove old app if exists
rm -rf "$APP_PATH"

# Create app bundle
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Create launcher
cat > "$APP_PATH/Contents/MacOS/launch" << LAUNCHER
#!/bin/bash
cd "$JC_FOLDER"

# Kill existing
lsof -ti:8080 | xargs kill -9 2>/dev/null
sleep 0.3

# Start with auto-restart on crash
while true; do
    python3 "$JC_FOLDER/manage.py" 8080
    EXIT_CODE=\$?
    if [ \$EXIT_CODE -eq 0 ] || [ \$EXIT_CODE -eq 130 ]; then
        exit 0
    fi
    sleep 2
done
LAUNCHER

chmod +x "$APP_PATH/Contents/MacOS/launch"

# Create Info.plist
cat > "$APP_PATH/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launch</string>
    <key>CFBundleIdentifier</key>
    <string>com.jccustom.admin</string>
    <key>CFBundleName</key>
    <string>JC Custom Guitars</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
</dict>
</plist>
PLIST

echo "   ✅ Created: Desktop/JC Custom Guitars.app"

# =============================================================================
# 5. AUTO-START ON LOGIN (OPTIONAL)
# =============================================================================
echo ""
read -p "🚀 Start automatically when computer turns on? (y/n): " AUTO_START

if [ "$AUTO_START" = "y" ] || [ "$AUTO_START" = "Y" ]; then
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_PATH="$PLIST_DIR/com.jccustom.admin.plist"
    
    mkdir -p "$PLIST_DIR"
    
    # Remove old
    launchctl unload "$PLIST_PATH" 2>/dev/null
    
    cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jccustom.admin</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$JC_FOLDER/manage.py</string>
        <string>8080</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$JC_FOLDER</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/jccustom.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/jccustom.err</string>
</dict>
</plist>
PLIST

    launchctl load "$PLIST_PATH"
    echo "   ✅ Auto-start enabled!"
fi

# =============================================================================
# 6. DONE!
# =============================================================================
echo ""
echo "============================================================"
echo "✅ SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "📁 Your photos folder: $JC_FOLDER"
echo "🖥️  Desktop app: JC Custom Guitars.app"
echo "🌐 Admin URL: http://localhost:8080"
echo ""
echo "============================================================"
echo "📱 IPHONE SETUP (do this on dad's phone)"
echo "============================================================"
echo ""
echo "1. Install 'Google Drive' from App Store"
echo "2. Sign in with the SAME Google account"
echo "3. Open Google Drive app → Settings → Backup"
echo "4. Turn ON 'Photos & Videos'"
echo "5. Set upload folder to 'JC Custom Guitars'"
echo ""
echo "That's it! Photos will auto-upload to Google Drive"
echo "and appear in the admin automatically."
echo ""
echo "============================================================"
echo ""

# =============================================================================
# 7. START NOW?
# =============================================================================
read -p "🚀 Open the admin now? (y/n): " START_NOW

if [ "$START_NOW" = "y" ] || [ "$START_NOW" = "Y" ]; then
    open "$APP_PATH"
fi
