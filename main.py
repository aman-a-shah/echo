import asyncio
import sys
from pynput import keyboard
from capture import ScreenCapturer
from audio import AudioController
from backboard_client import BackboardMemoryClient
from agents import AgentsOrchestrator


class EchoApp:
    def __init__(self):
        self.capture = ScreenCapturer()
        self.audio = AudioController()
        self.memory = BackboardMemoryClient()
        self.orchestrator = AgentsOrchestrator(self.capture, self.audio, self.memory)
        self.loop = asyncio.get_event_loop()
        self.is_running = True

    async def initialize(self):
        """Startup sequence — plays sound, connects Backboard, recalls last session."""
        self.audio.play_earcon("ready")
        await self.audio.speak("Echo is warming up...")

        # Connect to Backboard
        success = await self.memory.initialize_session()
        if not success:
            self.audio.play_earcon("error")
            await self.audio.speak("Memory unavailable, running without memory.")

        # Recall last session
        summary = await self.memory.get_session_summary()
        if summary and "first session" not in summary.lower():
            await self.audio.speak(f"Welcome back. {summary}")
        else:
            await self.audio.speak(
                "Echo is ready. Press Space to describe the screen, "
                "Q to ask a question, P to pause, Escape to stop narration."
            )

    def on_press(self, key):
        """Hotkey handler — runs in a separate thread from pynput."""
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()

                if char == 'q':
                    # Question mode — morse beep signals listening
                    self.audio.play_earcon("question")
                    self.audio.stop_speech()
                    question = self.audio.listen_for_question()
                    if question:
                        asyncio.run_coroutine_threadsafe(
                            self.orchestrator.ask_question(question), self.loop
                        )
                    else:
                        # Nothing heard — signal error
                        self.audio.play_earcon("error")

                elif char == 'p':
                    # Pause / resume
                    is_paused = self.audio.toggle_pause()
                    self.orchestrator.auto_narrate = not is_paused
                    self.audio.play_earcon("pause" if is_paused else "resume")
                    print("Paused." if is_paused else "Resumed.")

                elif char in ('=', '+'):
                    self.audio.set_rate(self.audio.tts_rate + 25)
                    self.audio.play_earcon("item")
                    print(f"Speed: {self.audio.tts_rate} wpm")

                elif char == '-':
                    self.audio.set_rate(self.audio.tts_rate - 25)
                    self.audio.play_earcon("item")
                    print(f"Speed: {self.audio.tts_rate} wpm")

            elif key == keyboard.Key.space:
                # Trigger narration
                self.audio.play_earcon("ready")
                self.orchestrator.auto_narrate = True
                asyncio.run_coroutine_threadsafe(
                    self.orchestrator.trigger_narration(), self.loop
                )

            elif key == keyboard.Key.esc:
                # Stop speech immediately
                self.audio.stop_speech()
                self.audio.play_earcon("error")

        except AttributeError:
            pass

    async def run(self):
        await self.initialize()

        self.orchestrator.start()

        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        print("\n=== Echo is running ===")
        print("Space      — Describe screen now")
        print("Q          — Ask a question (speak after the beep)")
        print("P          — Pause / Resume")
        print("+ / -      — Speed up / slow down voice")
        print("Esc        — Stop current narration")
        print("Ctrl+C     — Quit Echo")
        print("=======================\n")

        try:
            while self.is_running:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down Echo...")
        finally:
            self.orchestrator.stop()
            listener.stop()
            self.audio.stop_speech()


if __name__ == "__main__":
    app = EchoApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass