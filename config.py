import os
from dotenv import load_dotenv
load_dotenv()

# API Keys
GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY  = os.getenv("OPENROUTER_API_KEY")
BACKBOARD_API_KEY   = os.getenv("BACKBOARD_API_KEY")
CEREBRAS_API_KEY    = os.getenv("CEREBRAS_API_KEY")

# App Configuration
HOTWORD          = "echo"
TTS_RATE_DEFAULT = 175

# ---------------------------------------------------------------------------
# Vision provider registry — V key cycles through these at runtime
# ---------------------------------------------------------------------------
VISION_PROVIDERS = [
    {
        "id":     "gemini",
        "label":  "Gemini",
        "models": {
            "narrator": "gemini-2.5-flash",
            "sentinel": "gemini-2.5-flash",
        },
    },
    {
        "id":     "openrouter_nvidia",
        "label":  "Open Router NVIDIA",
        "models": {
            "narrator": "nvidia/nemotron-nano-12b-v2-vl:free",  # vision + tools, 128K
            "sentinel": "nvidia/nemotron-nano-12b-v2-vl:free",
        },
    },
    {
        "id":     "openrouter_gemma",
        "label":  "Open Router Gemma",
        "models": {
            "narrator": "google/gemma-3-27b-it:free",  # vision, 131K
            "sentinel": "google/gemma-3-27b-it:free",
        },
    },
    {
        "id":     "openrouter_gemma4",
        "label":  "Open Router Gemma 4",
        "models": {
            "narrator": "google/gemma-4-31b-it:free",  # vision + tools, 262K
            "sentinel": "google/gemma-4-31b-it:free",
        },
    },
]

DEFAULT_VISION_PROVIDER_INDEX = 0

# Prompts
NARRATOR_SYSTEM_PROMPT = """You are Echo, a real-time voice-first AI companion for a blind gamer.
Your job is to concisely describe the current state of the game screen provided.
Focus on spatial awareness (what is to the left, right, ahead), key items, enemies, and UI status (e.g., health bar).
Be brief, action-oriented, and do not provide unnecessary fluff. Read the screen as if you are the player's eyes."""

SENTINEL_SYSTEM_PROMPT = """You are Echo's Sentinel Agent. You watch the game screen strictly for immediate dangers.
Respond ONLY with a short, urgent warning if an enemy or hazard is actively threatening the player (e.g., 'Warning: Skeleton approaching from behind!').
If there is no immediate danger, respond exactly with the word: SAFE."""

# ---------------------------------------------------------------------------
# Change-detection narration tuning
# ---------------------------------------------------------------------------

# How often to check for screen changes (seconds) — pure pixel diff, no API cost
# Faster poll = more responsive. 0.5s is safe since it's just a pixel diff.
CHANGE_CHECK_INTERVAL = 0.5

# How different the screen needs to be to trigger narration (0.0-1.0)
# 0.04 = 4% pixel change. Raise if too chatty, lower if missing events.
# Good starting points:
#   0.02 — very sensitive (dialogue text appearing, small UI changes)
#   0.04 — default (new enemy, scene transition, health bar drop)
#   0.10 — only major changes (entering new area, cutscene)
CHANGE_THRESHOLD = 0.04

# Minimum seconds between narration ATTEMPTS (cooldown starts when narration fires,
# not when it finishes speaking). Keep this low — the _narration_in_progress flag
# prevents pile-ups. 3s means Echo can narrate roughly every ~5-6s in practice
# (3s cooldown + ~2-3s API latency).
NARRATOR_INTERVAL = 10.0

# Seconds between sentinel danger checks
SENTINEL_INTERVAL = 5.0

# Memory LLM (text-only)
MEMORY_LLM = {
    "provider": "google",
    "model":    "gemini-2.5-flash",
}