#!/bin/bash
# setup_menubar.sh
# ----------------
# Installs the Echo menu bar controller.
# Run once from the Echo project folder:
#
#   bash setup_menubar.sh
#
# What it does:
#   1. Installs rumps (menu bar framework)
#   2. Creates Echo Menubar.app (double-click or add to Login Items)
#   3. Optionally adds it to Login Items so it auto-starts on login

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# 1. Find Python
# ---------------------------------------------------------------------------
if   [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/python"  ]; then PYTHON="$SCRIPT_DIR/venv/bin/python"
elif command -v python3 &>/dev/null;          then PYTHON="$(command -v python3)"
else echo "❌  Python not found."; exit 1; fi

echo "Using Python: $PYTHON"

# ---------------------------------------------------------------------------
# 2. Install rumps + edge-tts (if not already installed)
# ---------------------------------------------------------------------------
echo "Installing dependencies..."
"$PYTHON" -m pip install --quiet rumps edge-tts
echo "✓ rumps and edge-tts installed"

# ---------------------------------------------------------------------------
# 3. Build Echo Menubar.app
# ---------------------------------------------------------------------------
APP="$SCRIPT_DIR/Echo Menubar.app"
MACOS="$APP/Contents/MacOS"
mkdir -p "$MACOS"

# Launcher binary (shell script acting as the executable)
cat > "$MACOS/Echo Menubar" << LAUNCHER
#!/bin/bash
cd "$SCRIPT_DIR"
exec "$PYTHON" "$SCRIPT_DIR/echo_menubar.py"
LAUNCHER
chmod +x "$MACOS/Echo Menubar"

mkdir -p "$APP/Contents/Resources"
if [ -f "$SCRIPT_DIR/public/echo_logo.icns" ]; then
    cp "$SCRIPT_DIR/public/echo_logo.icns" "$APP/Contents/Resources/"
fi

# Info.plist — LSUIElement=true hides the app from the Dock
cat > "$APP/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>             <string>Echo Menubar</string>
    <key>CFBundleIdentifier</key>       <string>com.echo.menubar</string>
    <key>CFBundleVersion</key>          <string>1.0</string>
    <key>CFBundleExecutable</key>       <string>Echo Menubar</string>
    <key>CFBundleIconFile</key>         <string>echo_logo.icns</string>
    <key>CFBundlePackageType</key>      <string>APPL</string>
    <key>LSUIElement</key>              <true/>
    <key>NSHighResolutionCapable</key>  <true/>
</dict>
</plist>
PLIST

echo "✓ Created: $APP"
echo "  → Double-click to launch the menu bar controller"

# ---------------------------------------------------------------------------
# 4. Offer to add to Login Items via osascript
# ---------------------------------------------------------------------------
echo ""
read -r -p "Add Echo Menubar to Login Items (auto-start on login)? [y/N] " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    osascript << APPLESCRIPT
tell application "System Events"
    make new login item at end of login items with properties ¬
        {path:"$APP", hidden:true, name:"Echo Menubar"}
end tell
APPLESCRIPT
    echo "✓ Added to Login Items — Echo will start automatically on login."
else
    echo "  Skipped. You can add it manually:"
    echo "  System Settings → General → Login Items → add 'Echo Menubar.app'"
fi

# ---------------------------------------------------------------------------
# 5. Launch it now
# ---------------------------------------------------------------------------
echo ""
read -r -p "Launch Echo Menubar now? [Y/n] " launch
if [[ ! "$launch" =~ ^[Nn]$ ]]; then
    open "$APP"
    echo "✓ Echo Menubar launched — look for 🎮 in your menu bar."
fi

echo ""
echo "Done. From now on, click 🎮 in the menu bar to start or stop Echo."