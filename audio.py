import asyncio
import subprocess
import speech_recognition as sr
from config import TTS_RATE_DEFAULT


class AudioController:
    def __init__(self):
        self.tts_rate = TTS_RATE_DEFAULT
        self.is_paused = False
        self.current_tts_process = None
        self.recognizer = sr.Recognizer()

    async def speak(self, text: str, interrupt: bool = False):
        """Speaks text using macOS 'say' command asynchronously."""
        if self.is_paused:
            return
        if interrupt:
            self.stop_speech()
        print(f"Echo says: {text}")
        clean_text = text.replace('"', '').replace("'", '')
        cmd = f'say -r {self.tts_rate} "{clean_text}"'
        self.current_tts_process = await asyncio.create_subprocess_shell(cmd)
        await self.current_tts_process.communicate()

    def stop_speech(self):
        """Stops currently playing speech."""
        if self.current_tts_process and self.current_tts_process.returncode is None:
            self.current_tts_process.terminate()
            self.current_tts_process = None
        subprocess.run(["killall", "say"], stderr=subprocess.DEVNULL)

    def set_rate(self, rate: int):
        self.tts_rate = max(50, min(400, rate))

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.stop_speech()
        return self.is_paused

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

    def play_earcon(self, sound_type: str):
        """Plays a distinct system sound for UI feedback."""
        # Always play resume/error sounds even when paused
        if self.is_paused and sound_type not in ("resume", "error"):
            return
        sounds = {
            "danger":   "/System/Library/Sounds/Basso.aiff",   # deep thud — danger
            "item":     "/System/Library/Sounds/Glass.aiff",   # glass ding — item found
            "ready":    "/System/Library/Sounds/Tink.aiff",    # light tick — startup
            "pause":    "/System/Library/Sounds/Funk.aiff",    # descending — paused
            "resume":   "/System/Library/Sounds/Pop.aiff",     # pop — resumed
            "question": "/System/Library/Sounds/Morse.aiff",   # beep — listening
            "error":    "/System/Library/Sounds/Sosumi.aiff",  # classic mac error
            "memory":   "/System/Library/Sounds/Ping.aiff",    # ping — memory stored
        }
        sound_file = sounds.get(sound_type, sounds["ready"])
        subprocess.Popen(["afplay", sound_file])