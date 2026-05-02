#!/bin/bash
# echo_launch.sh
# --------------
# Launches Echo as a background process.
# Drop this anywhere and double-click it (or bind it to a shortcut).
#
# Usage:
#   ./echo_launch.sh          — start Echo
#   ./echo_launch.sh stop     — kill running Echo
#   ./echo_launch.sh restart  — stop then start

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.echo.pid"
LOG_FILE="$SCRIPT_DIR/echo.log"

# ---------------------------------------------------------------------------
# Find Python — prefer the venv inside the project folder
# ---------------------------------------------------------------------------
if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/python" ]; then
    PYTHON="$SCRIPT_DIR/venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="$(command -v python3)"
else
    osascript -e 'display notification "Python not found — check echo.log" with title "Echo"'
    echo "ERROR: Python not found." >> "$LOG_FILE"
    exit 1
fi

stop_echo() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            echo "Echo stopped (PID $PID)."
        else
            echo "Echo was not running."
        fi
        rm -f "$PID_FILE"
    else
        # Fallback: kill by process name
        pkill -f "python.*main.py" 2>/dev/null && echo "Echo stopped." || echo "Echo was not running."
    fi
}

start_echo() {
    # Don't start a second instance
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        osascript -e 'display notification "Echo is already running" with title "Echo"'
        echo "Echo already running."
        return
    fi

    cd "$SCRIPT_DIR" || exit 1

    # Launch detached, log to file
    nohup "$PYTHON" main.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    osascript -e 'display notification "Echo started in the background" with title "Echo 🎮"'
    echo "Echo started (PID $(cat "$PID_FILE")). Logs → $LOG_FILE"
}

case "${1:-start}" in
    stop)    stop_echo ;;
    restart) stop_echo; sleep 1; start_echo ;;
    *)       start_echo ;;
esac