"""
vision_client.py
----------------
Unified vision client that can call either Gemini (via google-generativeai)
or any OpenRouter model (via the OpenAI-compatible REST API).

Switching providers at runtime is a single call:
    client.set_provider(provider_config)

Rate-limit backoff is tracked per provider so switching resets the clock.
"""

import asyncio
import base64
import io
import time
from typing import Optional
from PIL import Image

import google.generativeai as genai
from openai import AsyncOpenAI

from config import GEMINI_API_KEY, OPENROUTER_API_KEY, SENTINEL_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Per-provider rate-limit state
# ---------------------------------------------------------------------------

class _ProviderState:
    def __init__(self):
        self.last_call: float = 0.0
        self.backoff: float = 0.0

    def is_limited(self) -> bool:
        if self.backoff <= 0:
            return False
        return (time.monotonic() - self.last_call) < self.backoff

    def mark_call(self):
        self.last_call = time.monotonic()

    def record_success(self):
        self.backoff = 0.0

    def record_rate_limit(self, retry_after: float = 0.0):
        if retry_after > 0:
            self.backoff = min(retry_after + 2.0, 120.0)
        else:
            self.backoff = min(max(self.backoff * 2, 5.0), 120.0)


def _parse_retry_delay(error: Exception) -> float:
    try:
        msg = str(error)
        if "retry_delay" in msg and "seconds:" in msg:
            val = msg.split("seconds:")[1].strip().split()[0].rstrip("}")
            return float(val)
        # OpenAI-style: "Please retry after 12 seconds"
        if "retry after" in msg.lower():
            parts = msg.lower().split("retry after")
            val = parts[1].strip().split()[0].rstrip("s").rstrip(".")
            return float(val)
    except Exception:
        pass
    return 0.0


def _image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---------------------------------------------------------------------------
# VisionClient
# ---------------------------------------------------------------------------

class VisionClient:
    """
    Single object the orchestrator uses for all vision calls.
    Call set_provider() to switch at runtime — takes effect immediately.
    """

    def __init__(self):
        # Gemini setup
        genai.configure(api_key=GEMINI_API_KEY)
        self._gemini_vision   = genai.GenerativeModel("gemini-2.5-flash")
        self._gemini_sentinel = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=SENTINEL_SYSTEM_PROMPT
        )

        # OpenRouter setup (OpenAI-compatible)
        self._or_client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY or "no-key",
            base_url="https://openrouter.ai/api/v1",
        )

        # Active provider config (matches shape from config.VISION_PROVIDERS)
        self._provider: dict = {
            "id":     "gemini",
            "label":  "Gemini",
            "models": {"narrator": "gemini-2.5-flash", "sentinel": "gemini-2.5-flash"},
        }

        # Rate-limit state per provider id
        self._states: dict[str, _ProviderState] = {}

    def set_provider(self, provider_config: dict):
        """Switch to a new provider at runtime. Resets nothing else."""
        self._provider = provider_config
        pid = provider_config["id"]
        if pid not in self._states:
            self._states[pid] = _ProviderState()
        print(f"[VisionClient] Switched to provider: {provider_config['label']}")

    @property
    def provider_label(self) -> str:
        return self._provider["label"]

    @property
    def _state(self) -> _ProviderState:
        pid = self._provider["id"]
        if pid not in self._states:
            self._states[pid] = _ProviderState()
        return self._states[pid]

    def is_rate_limited(self) -> bool:
        return self._state.is_limited()

    # ------------------------------------------------------------------ #
    #  Public call interface                                               #
    # ------------------------------------------------------------------ #

    async def describe(self, img: Image.Image, prompt: str) -> Optional[str]:
        """Narrator / Q&A call — uses the 'narrator' model slot."""
        return await self._call(img, prompt, slot="narrator")

    async def sentinel(self, img: Image.Image) -> Optional[str]:
        """Sentinel danger-check — uses the 'sentinel' model slot."""
        return await self._call(
            img,
            "Is there an immediate danger to the player right now?",
            slot="sentinel"
        )

    # ------------------------------------------------------------------ #
    #  Internal routing                                                    #
    # ------------------------------------------------------------------ #

    async def _call(self, img: Image.Image, prompt: str, slot: str) -> Optional[str]:
        if self._state.is_limited():
            return None

        pid = self._provider["id"]
        model = self._provider["models"][slot]

        try:
            self._state.mark_call()
            if pid == "gemini":
                result = await self._call_gemini(img, prompt, slot)
            else:
                result = await self._call_openrouter(img, prompt, model)
            self._state.record_success()
            return result
        except Exception as e:
            msg = str(e)
            is_rate_limit = (
                "429" in msg
                or "quota" in msg.lower()
                or "rate limit" in msg.lower()
                or "too many" in msg.lower()
            )
            if is_rate_limit:
                delay = _parse_retry_delay(e)
                self._state.record_rate_limit(delay)
                print(f"[{self._provider['label']}] Rate limited — backing off {self._state.backoff:.0f}s")
            else:
                print(f"[{self._provider['label']}] Error: {e}")
            return None

    async def _call_gemini(self, img: Image.Image, prompt: str, slot: str) -> str:
        model = self._gemini_sentinel if slot == "sentinel" else self._gemini_vision
        # Gemini SDK is synchronous — run in executor to avoid blocking the loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: model.generate_content([prompt, img])
        )
        return response.text.strip()

    async def _call_openrouter(self, img: Image.Image, prompt: str, model: str) -> str:
        b64 = _image_to_base64(img)
        response = await self._or_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text",      "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }
            ],
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()