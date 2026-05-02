"""
echo_menubar.py
---------------
A macOS menu bar app that controls Echo.
Lives in your menu bar as 🎮 — click to start, stop, or check status.

Install dependency (once):
    pip install rumps

Run (stays in menu bar until quit):
    python echo_menubar.py

To auto-start on login, add echo_menubar.py to Login Items:
    System Settings → General → Login Items → add this script
    (or drag Echo Menubar.app into Login Items)
"""

import rumps
import subprocess
import os
import sys
import threading

# ---------------------------------------------------------------------------
# Find the Echo project directory — same folder as this script
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE   = os.path.join(SCRIPT_DIR, ".echo.pid")
LOG_FILE   = os.path.join(SCRIPT_DIR, "echo.log")

def _find_python() -> str:
    for candidate in [
        os.path.join(SCRIPT_DIR, ".venv", "bin", "python"),
        os.path.join(SCRIPT_DIR, "venv",  "bin", "python"),
    ]:
        if os.path.isfile(candidate):
            return candidate
    return sys.executable  # fall back to whichever python launched this script


def _echo_running() -> bool:
    if not os.path.isfile(PID_FILE):
        return False
    try:
        pid = int(open(PID_FILE).read().strip())
        os.kill(pid, 0)   # signal 0 = "are you alive?"
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        return False


def _start_echo():
    python = _find_python()
    main   = os.path.join(SCRIPT_DIR, "main.py")
    log    = open(LOG_FILE, "a")
    proc   = subprocess.Popen(
        [python, main],
        cwd=SCRIPT_DIR,
        stdout=log,
        stderr=log,
        start_new_session=True,   # detach from this process
    )
    with open(PID_FILE, "w") as f:
        f.write(str(proc.pid))


def _stop_echo():
    if not os.path.isfile(PID_FILE):
        subprocess.run(["pkill", "-f", "python.*main.py"], stderr=subprocess.DEVNULL)
        return
    try:
        pid = int(open(PID_FILE).read().strip())
        os.kill(pid, 15)   # SIGTERM — graceful shutdown
    except Exception:
        pass
    try:
        os.remove(PID_FILE)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Menu bar app
# ---------------------------------------------------------------------------

class EchoMenuBar(rumps.App):
    def __init__(self):
        super().__init__(
            name="Echo",
            title="🎮",          # icon shown in menu bar
            quit_button=None,    # we add our own quit item
        )
        self._build_menu()
        # Poll Echo's status every 3s to keep the icon up to date
        self._poll_timer = rumps.Timer(self._poll_status, 3)
        self._poll_timer.start()

    # ------------------------------------------------------------------ #
    #  Menu construction                                                   #
    # ------------------------------------------------------------------ #

    def _build_menu(self):
        running = _echo_running()
        self.menu.clear()
        self.title = "🎮●" if running else "🎮"

        if running:
            self.menu.add(rumps.MenuItem("● Echo is running", callback=None))
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("Stop Echo",    callback=self.stop_echo))
            self.menu.add(rumps.MenuItem("Restart Echo", callback=self.restart_echo))
        else:
            self.menu.add(rumps.MenuItem("Echo is stopped", callback=None))
            self.menu.add(rumps.separator)
            self.menu.add(rumps.MenuItem("▶  Start Echo", callback=self.start_echo))

        self.menu.add(rumps.separator)
        self.menu.add(rumps.MenuItem("Open log…",   callback=self.open_log))
        self.menu.add(rumps.MenuItem("Quit menubar", callback=self.quit_app))

    # ------------------------------------------------------------------ #
    #  Actions                                                             #
    # ------------------------------------------------------------------ #

    @rumps.clicked("▶  Start Echo")
    def start_echo(self, _=None):
        if _echo_running():
            rumps.notification("Echo", "", "Already running.")
            return
        threading.Thread(target=_start_echo, daemon=True).start()
        rumps.notification("Echo 🎮", "", "Starting…")
        # Give it a moment then refresh
        threading.Timer(2.0, self._build_menu).start()

    @rumps.clicked("Stop Echo")
    def stop_echo(self, _=None):
        _stop_echo()
        rumps.notification("Echo", "", "Stopped.")
        self._build_menu()

    @rumps.clicked("Restart Echo")
    def restart_echo(self, _=None):
        _stop_echo()
        threading.Timer(1.0, _start_echo).start()
        rumps.notification("Echo 🎮", "", "Restarting…")
        threading.Timer(3.0, self._build_menu).start()

    @rumps.clicked("Open log…")
    def open_log(self, _=None):
        subprocess.Popen(["open", LOG_FILE])

    def quit_app(self, _=None):
        rumps.quit_application()

    # ------------------------------------------------------------------ #
    #  Status polling                                                      #
    # ------------------------------------------------------------------ #

    def _poll_status(self, _=None):
        running = _echo_running()
        new_title = "🎮●" if running else "🎮"
        if self.title != new_title:
            self.title = new_title
            self._build_menu()


if __name__ == "__main__":
    EchoMenuBar().run()