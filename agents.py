import asyncio
import base64
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

        # Gemini for sentinel (vision, no memory needed — pure speed)
        genai.configure(api_key=GEMINI_API_KEY)
        self.sentinel_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SENTINEL_SYSTEM_PROMPT
        )
        # Gemini for narrator vision (image → text, then Backboard adds memory)
        self.narrator_vision_model = genai.GenerativeModel(
            model_name="gemini-2.5-flash"
        )

        self.running = False
        self.auto_narrate = False
        self.narrator_task = None
        self.sentinel_task = None

    async def narrator_loop(self):
        """Runs every NARRATOR_INTERVAL seconds for continuous narration."""
        while self.running:
            if self.auto_narrate and not self.audio.is_paused:
                await self.trigger_narration()
            await asyncio.sleep(NARRATOR_INTERVAL)

    async def trigger_narration(self):
        """
        Two-step process:
        1. Gemini Vision reads the screen and produces a raw description
        2. That description is sent to Backboard with memory='Auto'
           so context is stored and recalled across sessions
        """
        print("Narrator: Capturing frame...")
        try:
            img = self.capture.capture_frame()
            img_bytes = self.capture.capture_frame_bytes()

            # Step 1: Gemini Vision — describe the raw frame
            vision_response = self.narrator_vision_model.generate_content([
                "Describe what is on the game screen right now. "
                "Focus on: player position, enemies, items, health UI, and immediate hazards. "
                "Be concise — 2-3 sentences max.",
                img
            ])
            raw_description = vision_response.text.strip()
            print(f"Vision raw: {raw_description}")

            # Step 2: Backboard — enrich with memory context
            memory_prompt = (
                f"Current screen: {raw_description}\n\n"
                "Based on your memory of my previous sessions, narrate this moment for me. "
                "Reference past context if relevant (e.g. 'that enemy is back', 'you left that item earlier'). "
                "Keep it to 2-3 sentences."
            )
            narration = await self.memory.query_with_memory(memory_prompt)
            print(f"Narration: {narration}")
            await self.audio.speak(narration, interrupt=True)

        except Exception as e:
            print(f"Narrator error: {e}")

    async def sentinel_loop(self):
        """
        Fast danger-detection loop. Bypasses Backboard memory intentionally
        for minimum latency — just Gemini Vision checking for threats.
        """
        while self.running:
            if not self.audio.is_paused:
                try:
                    img = self.capture.capture_frame()
                    response = self.sentinel_model.generate_content([
                        "Is there an immediate danger to the player right now?",
                        img
                    ])
                    text = response.text.strip()
                    if "SAFE" not in text.upper():
                        print(f"Sentinel Alert: {text}")
                        self.audio.play_earcon("danger")
                        await self.audio.speak(text, interrupt=True)
                except Exception as e:
                    print(f"Sentinel error: {e}")
            await asyncio.sleep(SENTINEL_INTERVAL)

    async def ask_question(self, question: str):
        """
        Question mode: user asks something freeform.
        Vision sees the current screen, Backboard adds memory context.
        """
        print(f"Question: {question}")
        try:
            img = self.capture.capture_frame()

            # Get visual context
            vision_response = self.narrator_vision_model.generate_content([
                f"The player is asking: '{question}'. What does the current screen show that's relevant?",
                img
            ])
            visual_context = vision_response.text.strip()

            # Answer with memory
            memory_prompt = (
                f"The player asks: '{question}'\n"
                f"Current screen context: {visual_context}\n"
                "Answer the question using both the screen context and your memory of past sessions."
            )
            answer = await self.memory.query_with_memory(memory_prompt)
            print(f"Answer: {answer}")
            await self.audio.speak(answer, interrupt=True)
        except Exception as e:
            print(f"Question error: {e}")

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