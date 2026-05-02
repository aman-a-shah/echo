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
        """Plays a distinct system sound for alerts."""
        if self.is_paused:
            return
        sounds = {
            "danger": "/System/Library/Sounds/Basso.aiff",
            "item":   "/System/Library/Sounds/Glass.aiff",
            "ready":  "/System/Library/Sounds/Tink.aiff",
        }
        sound_file = sounds.get(sound_type, sounds["ready"])
        subprocess.Popen(["afplay", sound_file])


if __name__ == "__main__":
    async def test():
        ac = AudioController()
        ac.play_earcon("ready")
        await ac.speak("Audio controller is working correctly.")
        print("Speak a test question now...")
        q = ac.listen_for_question()
        if q:
            await ac.speak(f"You said: {q}")
    asyncio.run(test())