#!/bin/bash
# setup_shortcut.sh
# -----------------
# Creates a macOS Automator Quick Action that launches Echo with a
# global keyboard shortcut (default: ⌃⌥⌘E — Control+Option+Cmd+E).
#
# Run once:  bash setup_shortcut.sh
# Then go to: System Settings → Keyboard → Keyboard Shortcuts → Services
#   find "Launch Echo", assign your preferred shortcut there.
#
# This script also creates a standalone .app you can put in your Dock.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_SCRIPT="$SCRIPT_DIR/echo_launch.sh"

# ---------------------------------------------------------------------------
# 1. Make launch script executable
# ---------------------------------------------------------------------------
chmod +x "$LAUNCH_SCRIPT"
echo "✓ Made echo_launch.sh executable"

# ---------------------------------------------------------------------------
# 2. Create a standalone Echo.app (double-click to launch)
# ---------------------------------------------------------------------------
APP_PATH="$SCRIPT_DIR/Echo.app"
mkdir -p "$APP_PATH/Contents/MacOS"

cat > "$APP_PATH/Contents/MacOS/Echo" << EOF
#!/bin/bash
bash "$LAUNCH_SCRIPT"
EOF
chmod +x "$APP_PATH/Contents/MacOS/Echo"

mkdir -p "$APP_PATH/Contents/Resources"
if [ -f "$SCRIPT_DIR/public/echo_logo.icns" ]; then
    cp "$SCRIPT_DIR/public/echo_logo.icns" "$APP_PATH/Contents/Resources/"
fi

cat > "$APP_PATH/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>         <string>Echo</string>
    <key>CFBundleIdentifier</key>   <string>com.echo.gaming</string>
    <key>CFBundleVersion</key>      <string>1.0</string>
    <key>CFBundleExecutable</key>   <string>Echo</string>
    <key>CFBundleIconFile</key>     <string>echo_logo.icns</string>
    <key>CFBundlePackageType</key>  <string>APPL</string>
    <key>LSUIElement</key>          <true/>
</dict>
</plist>
EOF

echo "✓ Created Echo.app at $APP_PATH"
echo "  → Drag Echo.app to your Dock for one-click launch."

# ---------------------------------------------------------------------------
# 3. Create Automator Quick Action (Service) for global shortcut
# ---------------------------------------------------------------------------
SERVICE_DIR="$HOME/Library/Services"
SERVICE_NAME="Launch Echo.workflow"
SERVICE_PATH="$SERVICE_DIR/$SERVICE_NAME"

mkdir -p "$SERVICE_DIR"
mkdir -p "$SERVICE_PATH/Contents"

cat > "$SERVICE_PATH/Contents/document.wflow" << WFLOW
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AMApplicationBuild</key>   <string>521.1</string>
    <key>AMApplicationVersion</key> <string>2.10</string>
    <key>AMDocumentVersion</key>    <string>2</string>
    <key>actions</key>
    <array>
        <dict>
            <key>action</key>
            <dict>
                <key>AMAccepts</key>
                <dict>
                    <key>Container</key> <string>List</string>
                    <key>Optional</key>  <true/>
                    <key>Types</key>     <array><string>com.apple.cocoa.string</string></array>
                </dict>
                <key>AMActionVersion</key>  <string>2.0.3</string>
                <key>AMApplication</key>    <array><string>Automator</string></array>
                <key>AMParameterProperties</key>
                <dict>
                    <key>COMMAND_STRING</key>
                    <dict>
                        <key>tokenizedValue</key>
                        <array><string>bash "$LAUNCH_SCRIPT"</string></array>
                    </dict>
                </dict>
                <key>AMProvides</key>
                <dict>
                    <key>Container</key> <string>List</string>
                    <key>Types</key>     <array><string>com.apple.cocoa.string</string></array>
                </dict>
                <key>ActionBundlePath</key>
                <string>/System/Library/Automator/Run Shell Script.action</string>
                <key>ActionName</key>   <string>Run Shell Script</string>
                <key>parameters</key>
                <dict>
                    <key>COMMAND_STRING</key> <string>bash "$LAUNCH_SCRIPT"</string>
                    <key>CheckedForUserDefaultShell</key> <true/>
                    <key>inputMethod</key>    <integer>0</integer>
                    <key>shell</key>          <string>/bin/bash</string>
                    <key>source</key>         <string></string>
                </dict>
            </dict>
        </dict>
    </array>
    <key>connectors</key> <dict/>
    <key>workflowMetaData</key>
    <dict>
        <key>workflowTypeIdentifier</key>
        <string>com.apple.Automator.servicesMenu</string>
    </dict>
</dict>
</plist>
WFLOW

echo "✓ Installed Quick Action: '$SERVICE_NAME'"
echo ""
echo "================================================================"
echo "  FINAL STEP — assign a keyboard shortcut:"
echo "  System Settings → Keyboard → Keyboard Shortcuts → Services"
echo "  Find 'Launch Echo' → click None → press your shortcut."
echo "  Recommended: ⌃⌥⌘E  (Control + Option + Cmd + E)"
echo "================================================================"