"""
audio.py
--------
AudioController — TTS, earcons, and speech recognition.

TTS backends (in priority order):
  1. edge-tts  — Microsoft Neural voices, free, no API key, very natural.
                 Install:  pip install edge-tts
  2. macOS say — Fallback if edge-tts is not installed.

Switch backend at runtime:  audio.set_tts_backend("say") / ("edge")
"""

import asyncio
import subprocess
import tempfile
import os
import speech_recognition as sr
from config import TTS_RATE_DEFAULT

# Try to import edge-tts — graceful fallback if not installed
try:
    import edge_tts
    _EDGE_AVAILABLE = True
except ImportError:
    _EDGE_AVAILABLE = False
    print("[Audio] edge-tts not found — using macOS 'say'. Run: pip install edge-tts")

# ---------------------------------------------------------------------------
# Natural-sounding Microsoft Neural voices (edge-tts)
# Pick one you like — all are free, no key needed.
# ---------------------------------------------------------------------------
EDGE_VOICES = {
    "default": "en-US-AndrewNeural",      # natural male, warm, conversational
    "female":  "en-US-JennyNeural",       # natural female, friendly
    "uk":      "en-GB-RyanNeural",        # British male
    "au":      "en-AU-WilliamNeural",     # Australian male
}
EDGE_VOICE = EDGE_VOICES["default"]

# edge-tts rate offset: "+0%" = normal, "+20%" = 20% faster
def _rate_to_edge(wpm: int) -> str:
    """Convert WPM (175 default) to edge-tts rate string."""
    # 150 wpm ≈ 0%, linear scale
    pct = int((wpm - 150) / 150 * 100)
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct}%"


class AudioController:
    def __init__(self):
        self.tts_rate = TTS_RATE_DEFAULT
        self.is_paused = False
        self.current_tts_process = None
        self.recognizer = sr.Recognizer()
        self._tts_backend = "edge" if _EDGE_AVAILABLE else "say"
        self._tts_lock: asyncio.Lock | None = None  # lazy-init inside the running loop

    # ------------------------------------------------------------------ #
    #  TTS                                                                 #
    # ------------------------------------------------------------------ #

    def set_tts_backend(self, backend: str):
        """Switch between 'edge' and 'say'."""
        if backend == "edge" and not _EDGE_AVAILABLE:
            print("[Audio] edge-tts not installed, staying on 'say'.")
            return
        self._tts_backend = backend
        print(f"[Audio] TTS backend: {backend}")

    async def speak(self, text: str, interrupt: bool = False):
        """Speaks text asynchronously using the active TTS backend."""
        if self.is_paused:
            return
        if interrupt:
            self.stop_speech()

        print(f"Echo says: {text}")

        if self._tts_lock is None:
            self._tts_lock = asyncio.Lock()
        async with self._tts_lock:
            if self._tts_backend == "edge" and _EDGE_AVAILABLE:
                await self._speak_edge(text)
            else:
                await self._speak_say(text)

    async def _speak_edge(self, text: str):
        """edge-tts: streams MP3 to a temp file, plays with afplay."""
        rate_str = _rate_to_edge(self.tts_rate)
        try:
            communicate = edge_tts.Communicate(text, EDGE_VOICE, rate=rate_str)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name

            await communicate.save(tmp_path)

            proc = await asyncio.create_subprocess_exec(
                "afplay", tmp_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            self.current_tts_process = proc
            await proc.communicate()
        except Exception as e:
            print(f"[edge-tts] Error: {e} — falling back to say")
            await self._speak_say(text)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    async def _speak_say(self, text: str):
        """macOS say fallback."""
        clean_text = text.replace('"', '').replace("'", '')
        cmd = f'say -r {self.tts_rate} "{clean_text}"'
        self.current_tts_process = await asyncio.create_subprocess_shell(cmd)
        await self.current_tts_process.communicate()

    def stop_speech(self):
        """Stops currently playing speech."""
        if self.current_tts_process and self.current_tts_process.returncode is None:
            self.current_tts_process.terminate()
            self.current_tts_process = None
        subprocess.run(["killall", "afplay", "say"], stderr=subprocess.DEVNULL)

    def set_rate(self, rate: int):
        self.tts_rate = max(50, min(400, rate))

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.stop_speech()
        return self.is_paused

    # ------------------------------------------------------------------ #
    #  Speech recognition                                                  #
    # ------------------------------------------------------------------ #

    def listen_for_question(self) -> str:
        """Listens for a spoken question and returns the text."""
        try:
            with sr.Microphone() as source:
                print("Listening for question...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print("Processing speech...")
                text = self.recognizer.recognize_google(audio)
                print(f"You asked: {text}")
                return text
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return ""
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return ""

    # ------------------------------------------------------------------ #
    #  Earcons                                                             #
    # ------------------------------------------------------------------ #

    def play_earcon(self, sound_type: str):
        """Plays a distinct system sound for UI feedback."""
        # Always play resume/error sounds even when paused
        if self.is_paused and sound_type not in ("resume", "error"):
            return
        sounds = {
            "danger":   "/System/Library/Sounds/Basso.aiff",    # deep thud — danger
            "item":     "/System/Library/Sounds/Glass.aiff",    # glass ding — item / speed
            "ready":    "/System/Library/Sounds/Tink.aiff",     # light tick — startup / space
            "pause":    "/System/Library/Sounds/Funk.aiff",     # descending — paused
            "resume":   "/System/Library/Sounds/Pop.aiff",      # pop — resumed
            "question": "/System/Library/Sounds/Morse.aiff",    # beep — listening
            "error":    "/System/Library/Sounds/Sosumi.aiff",   # classic mac error
            "memory":   "/System/Library/Sounds/Ping.aiff",     # ping — memory / provider switch
            "stop":     "/System/Library/Sounds/Hero.aiff",     # hero fanfare — ESC stop
        }
        sound_file = sounds.get(sound_type, sounds["ready"])
        subprocess.Popen(["afplay", sound_file])