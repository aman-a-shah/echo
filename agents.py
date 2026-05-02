import asyncio
import time
from config import NARRATOR_INTERVAL, SENTINEL_INTERVAL, CHANGE_THRESHOLD, CHANGE_CHECK_INTERVAL
from capture import ScreenCapturer
from audio import AudioController
from backboard_client import BackboardMemoryClient
from vision_client import VisionClient


class AgentsOrchestrator:
    def __init__(
        self,
        capture: ScreenCapturer,
        audio: AudioController,
        memory: BackboardMemoryClient,
        vision: VisionClient,
    ):
        self.capture = capture
        self.audio   = audio
        self.memory  = memory
        self.vision  = vision

        self.running           = False
        self.auto_narrate      = True
        self.narrator_task     = None
        self.sentinel_task     = None
        self._last_narration: str        = ""
        self._last_narration_time: float = 0.0
        self._narration_in_progress      = False

    # ------------------------------------------------------------------ #
    #  Narrator — change-driven                                           #
    # ------------------------------------------------------------------ #

    async def narrator_loop(self):
        """
        Polls every CHANGE_CHECK_INTERVAL seconds.
        Key fix: capture_if_changed() (which advances _last_frame) is only
        called when we are actually ready to narrate — not while a narration
        is in flight. Otherwise the baseline keeps advancing during the API
        call, and the next diff shows 0 change even though the screen moved.
        """
        while self.running:
            await asyncio.sleep(CHANGE_CHECK_INTERVAL)

            if not self.auto_narrate or self.audio.is_paused:
                continue

            # Don't advance the diff baseline while an API call is in flight
            if self._narration_in_progress:
                continue

            # Cooldown check before doing any capture work
            if time.monotonic() - self._last_narration_time < NARRATOR_INTERVAL:
                continue

            if self.vision.is_rate_limited():
                continue

            # Cheap local pixel diff — only called when we're ready to act
            img, score = self.capture.capture_if_changed(threshold=CHANGE_THRESHOLD)
            if img is None:
                continue

            # Fire off as a background task — loop keeps running immediately
            self._last_narration_time = time.monotonic()
            asyncio.get_event_loop().create_task(self._do_narration(score))

    async def _do_narration(self, score: float):
        """
        Captures a FRESH frame right before the API call.
        _narration_in_progress is ALWAYS cleared in finally — can never get stuck.
        """
        if self._narration_in_progress:
            return
        self._narration_in_progress = True

        try:
            img = self.capture.capture_frame()

            if score > 0.3:
                context = "The scene has changed significantly."
            elif score > 0.1:
                context = "Something has changed on screen."
            else:
                context = "There is a small but potentially important change on screen."

            prompt = (
                "You are Echo, a voice assistant for a blind gamer. "
                f"{context} "
                "Describe what is on the game screen right now. "
                "Focus on: player position, enemies, items, health UI, and immediate hazards. "
                "Be concise — 2-3 sentences max."
            )

            try:
                raw = await asyncio.wait_for(self.vision.describe(img, prompt), timeout=15.0)
            except asyncio.TimeoutError:
                print("[Narrator] Vision API timed out — skipping")
                return

            if raw is None:
                return  # rate limited

            if raw == self._last_narration:
                return  # nothing new to say
            self._last_narration = raw

            try:
                memory_prompt = (
                    f"Current screen: {raw}\n\n"
                    "Based on your memory of my previous sessions, narrate this moment. "
                    "Reference past context if relevant. Keep it to 2-3 sentences."
                )
                narration = await asyncio.wait_for(
                    self.memory.query_with_memory(memory_prompt), timeout=10.0
                )
                print(f"Narration (diff={score:.2f}): {narration}")
                await self.audio.speak(narration, interrupt=True)
            except asyncio.TimeoutError:
                print("[Narrator] Memory API timed out — using raw description")
                await self.audio.speak(raw, interrupt=True)
            except Exception as e:
                print(f"Memory error, using raw description: {e}")
                await self.audio.speak(raw, interrupt=True)

        except Exception as e:
            print(f"[Narrator] Unexpected error: {e}")
        finally:
            self._narration_in_progress = False  # ALWAYS released

    # ------------------------------------------------------------------ #
    #  Sentinel                                                            #
    # ------------------------------------------------------------------ #

    async def sentinel_loop(self):
        """Danger detection on its own fixed interval, independent of narrator."""
        while self.running:
            wait = max(SENTINEL_INTERVAL, self.vision._state.backoff)
            await asyncio.sleep(wait)

            if self.audio.is_paused:
                continue

            img  = self.capture.capture_frame()
            text = await self.vision.sentinel(img)

            if text and "SAFE" not in text.upper():
                print(f"Sentinel Alert: {text}")
                self.audio.play_earcon("danger")
                await self.audio.speak(text, interrupt=True)

    # ------------------------------------------------------------------ #
    #  Q&A                                                                 #
    # ------------------------------------------------------------------ #

    async def ask_question(self, question: str):
        print(f"You asked: {question}")
        img = self.capture.capture_frame()

        prompt = (
            f"The player (who is blind) is asking: '{question}'. "
            "Describe only the parts of the game screen relevant to answering this question."
        )
        visual_context = await self.vision.describe(img, prompt)

        if visual_context is None:
            visual_context = "Vision API unavailable (rate limited). I cannot see the screen right now, but please answer based on memory if possible."

        try:
            memory_prompt = (
                f"The player asks: '{question}'\n"
                f"Current screen context: {visual_context}\n"
                "Answer using both the screen context and your memory of past sessions."
            )
            answer = await self.memory.query_with_memory(memory_prompt)
            print(f"Answer: {answer}")
            await self.audio.speak(answer, interrupt=True)
        except Exception as e:
            print(f"Memory error during Q&A: {e}")
            await self.audio.speak(visual_context, interrupt=True)

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

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