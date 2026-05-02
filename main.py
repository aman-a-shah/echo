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

        # Connect to Backboard (creates assistant + thread)
        success = await self.memory.initialize_session()
        if not success:
            await self.audio.speak("Failed to connect to memory system. Exiting.")
            sys.exit(1)

        # Recall last session from Backboard memory
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
            # Character keys
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()

                if char == 'q':
                    # Question mode
                    self.audio.play_earcon("ready")
                    self.audio.stop_speech()
                    question = self.audio.listen_for_question()
                    if question:
                        asyncio.run_coroutine_threadsafe(
                            self.orchestrator.ask_question(question), self.loop
                        )

                elif char == 'p':
                    # Toggle pause
                    is_paused = self.audio.toggle_pause()
                    self.orchestrator.auto_narrate = not is_paused
                    msg = "Paused." if is_paused else "Resumed."
                    print(msg)

                elif char in ('=', '+'):
                    self.audio.set_rate(self.audio.tts_rate + 25)
                    print(f"Speed: {self.audio.tts_rate} wpm")

                elif char == '-':
                    self.audio.set_rate(self.audio.tts_rate - 25)
                    print(f"Speed: {self.audio.tts_rate} wpm")

            # Special keys
            elif key == keyboard.Key.space:
                # Trigger immediate narration and enable auto-narrate
                self.orchestrator.auto_narrate = True
                asyncio.run_coroutine_threadsafe(
                    self.orchestrator.trigger_narration(), self.loop
                )

            elif key == keyboard.Key.esc:
                # Stop current speech immediately
                self.audio.stop_speech()

        except AttributeError:
            pass

    async def run(self):
        await self.initialize()

        # Start background agent loops
        self.orchestrator.start()

        # Start keyboard listener in its own thread
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

        print("\n=== Echo is running ===")
        print("Space      — Describe screen now")
        print("Q          — Ask a question (speak after the chime)")
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