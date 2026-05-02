import asyncio
from pynput import keyboard
from capture import ScreenCapturer
from audio import AudioController
from backboard_client import BackboardMemoryClient
from agents import AgentsOrchestrator
import sys

class EchoApp:
    def __init__(self):
        self.capture = ScreenCapturer()
        self.audio = AudioController()
        self.memory = BackboardMemoryClient()
        self.orchestrator = AgentsOrchestrator(self.capture, self.audio, self.memory)
        self.loop = asyncio.get_event_loop()
        self.is_running = True

    async def initialize(self):
        # Play startup sound
        self.audio.play_earcon("ready")
        await self.audio.speak("Echo is warming up...")
        
        # Initialize Backboard Memory
        success = self.memory.initialize_session()
        if not success:
            await self.audio.speak("Failed to connect to Backboard. Exiting.")
            sys.exit(1)
            
        # Get session summary
        summary = self.memory.get_session_summary()
        if summary:
            await self.audio.speak(f"Welcome back. {summary}")
        else:
            await self.audio.speak("Echo is ready. Say 'Echo describe' to begin, or press Space.")

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                char = key.char.lower()
                if char == 'q':
                    # Enter Question Mode
                    self.audio.play_earcon("ready")
                    self.audio.stop_speech()
                    question = self.audio.listen_for_question()
                    if question:
                        # We schedule this in the event loop since pynput runs in a separate thread
                        asyncio.run_coroutine_threadsafe(self.orchestrator.ask_question(question), self.loop)
                
                elif char == 'p':
                    # Pause/Resume
                    is_paused = self.audio.toggle_pause()
                    state_msg = "Paused" if is_paused else "Resumed"
                    print(f"Echo {state_msg}")
                    # Only auto narrate if unpaused
                    self.orchestrator.auto_narrate = not is_paused

                elif char == '=' or char == '+':
                    self.audio.set_rate(self.audio.tts_rate + 25)
                    print(f"Rate increased to {self.audio.tts_rate}")

                elif char == '-':
                    self.audio.set_rate(max(50, self.audio.tts_rate - 25))
                    print(f"Rate decreased to {self.audio.tts_rate}")

            elif key == keyboard.Key.space:
                # Trigger immediate description
                self.orchestrator.auto_narrate = True # Enable continuous narration once started
                asyncio.run_coroutine_threadsafe(self.orchestrator.trigger_narration(), self.loop)

            elif key == keyboard.Key.esc:
                # Stop current narration immediately
                self.audio.stop_speech()
                
        except AttributeError:
            pass

    async def run(self):
        await self.initialize()
        
        # Start Agents
        self.orchestrator.start()
        
        # Start Hotkey Listener (runs in its own thread)
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()
        
        # Keep main loop running
        try:
            while self.is_running:
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            print("Exiting Echo...")
        finally:
            self.orchestrator.stop()
            listener.stop()

if __name__ == "__main__":
    app = EchoApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        pass
