import asyncio
import google.generativeai as genai
from config import GEMINI_API_KEY, SENTINEL_SYSTEM_PROMPT, NARRATOR_INTERVAL, SENTINEL_INTERVAL
from capture import ScreenCapturer
from audio import AudioController
from backboard_client import BackboardMemoryClient

class AgentsOrchestrator:
    def __init__(self, capture: ScreenCapturer, audio: AudioController, memory: BackboardMemoryClient):
        self.capture = capture
        self.audio = audio
        self.memory = memory
        
        # Configure Gemini for Sentinel
        genai.configure(api_key=GEMINI_API_KEY)
        self.sentinel_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SENTINEL_SYSTEM_PROMPT
        )
        
        self.running = False
        self.narrator_task = None
        self.sentinel_task = None
        
        # We only auto-narrate if it's not paused
        self.auto_narrate = False 

    async def narrator_loop(self):
        """
        Runs every N seconds. Extracts frame, sends to Backboard for memory + narration.
        """
        while self.running:
            if self.auto_narrate and not self.audio.is_paused:
                await self.trigger_narration()
            await asyncio.sleep(NARRATOR_INTERVAL)

    async def trigger_narration(self):
        """
        Can be called manually (Spacebar) or via the loop.
        """
        print("Narrator Agent: Analyzing frame...")
        img_bytes = self.capture.capture_frame_bytes()
        prompt = "Describe the current scene."
        
        # Use Backboard so it Remembers
        response = self.memory.query_with_memory(prompt, img_bytes)
        print(f"Narrator response: {response}")
        
        await self.audio.speak(response, interrupt=True)

    async def sentinel_loop(self):
        """
        Runs frequently. Only looks for danger.
        Bypasses Backboard memory for absolute minimum latency.
        """
        while self.running:
            if not self.audio.is_paused:
                try:
                    img = self.capture.capture_frame()
                    response = self.sentinel_model.generate_content([
                        "Is there an immediate danger? Reply SAFE or provide a short warning.", 
                        img
                    ])
                    text = response.text.strip().upper()
                    
                    if "SAFE" not in text:
                        print(f"Sentinel Alert: {text}")
                        # Play urgent earcon and interrupt narrator
                        self.audio.play_earcon("danger")
                        await self.audio.speak(text, interrupt=True)
                except Exception as e:
                    print(f"Sentinel Error: {e}")
            await asyncio.sleep(SENTINEL_INTERVAL)

    def start(self):
        self.running = True
        loop = asyncio.get_event_loop()
        self.narrator_task = loop.create_task(self.narrator_loop())
        self.sentinel_task = loop.create_task(self.sentinel_loop())

    def stop(self):
        self.running = False
        if self.narrator_task:
            self.narrator_task.cancel()
        if self.sentinel_task:
            self.sentinel_task.cancel()

    async def ask_question(self, question: str):
        """
        Called when Q is pressed and user speaks a question.
        """
        print(f"Asking question: {question}")
        img_bytes = self.capture.capture_frame_bytes()
        response = self.memory.query_with_memory(question, img_bytes)
        print(f"Question response: {response}")
        await self.audio.speak(response, interrupt=True)
