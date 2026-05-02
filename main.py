import os
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "0"
os.environ["PATH"] += os.pathsep + "/opt/homebrew/bin" + os.pathsep + "/usr/local/bin"

import asyncio
from pynput import keyboard
from capture import ScreenCapturer
from audio import AudioController
from backboard_client import BackboardMemoryClient
from vision_client import VisionClient
from agents import AgentsOrchestrator
from config import VISION_PROVIDERS, DEFAULT_VISION_PROVIDER_INDEX


class EchoApp:
    def __init__(self):
        self.capture = ScreenCapturer()
        self.audio   = AudioController()
        self.memory  = BackboardMemoryClient()
        self.vision  = VisionClient()
        self.orchestrator = AgentsOrchestrator(
            self.capture, self.audio, self.memory, self.vision
        )
        self.loop       = asyncio.get_event_loop()
        self.is_running = True

        # Provider cycling state
        self._provider_index = DEFAULT_VISION_PROVIDER_INDEX
        self.vision.set_provider(VISION_PROVIDERS[self._provider_index])

    # ------------------------------------------------------------------ #
    #  Startup                                                             #
    # ------------------------------------------------------------------ #

    async def initialize(self):
        self.audio.play_earcon("ready")
        await self.audio.speak("Echo is warming up...")

        success = await self.memory.initialize_session()
        if not success:
            self.audio.play_earcon("error")
            await self.audio.speak("Memory unavailable, running without memory.")

        summary = await self.memory.get_session_summary()
        if summary and "first session" not in summary.lower():
            await self.audio.speak(f"Welcome back. {summary}")
        else:
            await self.audio.speak(
                "Hey, Echo here — ready when you are. "
                "I'll describe the screen as things change. Q to ask me something, "
                "V to switch vision, P to pause, or Escape to cut me off."
            )

    # ------------------------------------------------------------------ #
    #  Provider switching                                                  #
    # ------------------------------------------------------------------ #

    def _cycle_provider(self):
        """Advance to the next provider in the registry and announce it."""
        self._provider_index = (self._provider_index + 1) % len(VISION_PROVIDERS)
        new_provider = VISION_PROVIDERS[self._provider_index]
        self.vision.set_provider(new_provider)
        label = new_provider["label"]
        print(f"Vision provider: {label}")
        self.audio.play_earcon("memory")
        asyncio.run_coroutine_threadsafe(
            self.audio.speak(f"Switched to {label}", interrupt=True),
            self.loop,
        )

    # ------------------------------------------------------------------ #
    #  Hotkeys                                                             #
    # ------------------------------------------------------------------ #

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()

                if char == 'q':
                    # Beep → stop any speech → listen
                    self.audio.play_earcon("question")
                    self.audio.stop_speech()
                    question = self.audio.listen_for_question()
                    if question:
                        asyncio.run_coroutine_threadsafe(
                            self.orchestrator.ask_question(question), self.loop
                        )
                    else:
                        self.audio.play_earcon("error")
                        asyncio.run_coroutine_threadsafe(
                            self.audio.speak("I didn't catch that — try again.", interrupt=True),
                            self.loop,
                        )

                elif char == 'p':
                    is_paused = self.audio.toggle_pause()
                    self.orchestrator.auto_narrate = not is_paused
                    if is_paused:
                        self.audio.play_earcon("pause")
                        # Use say directly since audio is paused — bypass is_paused guard
                        asyncio.run_coroutine_threadsafe(
                            self._force_speak("Paused."),
                            self.loop,
                        )
                    else:
                        self.audio.play_earcon("resume")
                        asyncio.run_coroutine_threadsafe(
                            self.audio.speak("Resumed.", interrupt=False),
                            self.loop,
                        )
                    print("Paused." if is_paused else "Resumed.")

                elif char == 'v':
                    self._cycle_provider()

                elif char in ('=', '+'):
                    self.audio.set_rate(self.audio.tts_rate + 25)
                    self.audio.play_earcon("item")
                    asyncio.run_coroutine_threadsafe(
                        self.audio.speak(f"Speed up. {self.audio.tts_rate} words per minute.", interrupt=True),
                        self.loop,
                    )
                    print(f"Speed: {self.audio.tts_rate} wpm")

                elif char == '-':
                    self.audio.set_rate(self.audio.tts_rate - 25)
                    self.audio.play_earcon("item")
                    asyncio.run_coroutine_threadsafe(
                        self.audio.speak(f"Slowing down. {self.audio.tts_rate} words per minute.", interrupt=True),
                        self.loop,
                    )
                    print(f"Speed: {self.audio.tts_rate} wpm")


            elif key == keyboard.Key.esc:
                self.audio.stop_speech()
                self.audio.play_earcon("stop")
                print("Speech stopped.")

        except AttributeError:
            pass

    async def _force_speak(self, text: str):
        """Speak even while paused — used for pause confirmation."""
        import subprocess
        subprocess.Popen(["say", text])

    # ------------------------------------------------------------------ #
    #  Main loop                                                           #
    # ------------------------------------------------------------------ #

    async def run(self):
        self.loop = asyncio.get_running_loop()
        await self.initialize()
        self.orchestrator.start()

        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        print("\n=== Echo is running ===")
        print("Q          — Ask a question (speak after the beep)")
        print("V          — Cycle vision provider (Gemini → OpenRouter → ...)")
        print("P          — Pause / Resume")
        print("+ / -      — Speed up / slow down voice")
        print("Esc        — Stop current narration")
        print("Ctrl+C     — Quit Echo")
        print("=======================")
        print(f"Vision:    {self.vision.provider_label}")
        print(f"TTS:       {self.audio._tts_backend}\n")

        try:
            while self.is_running:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down Echo...")
        finally:
            self.orchestrator.stop()
            listener.stop()
            self.audio.stop_speech()
            await self.audio.speak("Echo signing off. Good luck out there.")


if __name__ == "__main__":
    app = EchoApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass