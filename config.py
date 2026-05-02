import os
from dotenv import load_dotenv
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY")

# App Configuration
HOTWORD = "echo"
TTS_RATE_DEFAULT = 175  # Words per minute for macOS 'say'

# Prompts
NARRATOR_SYSTEM_PROMPT = """You are Echo, a real-time voice-first AI companion for a blind gamer.
Your job is to concisely describe the current state of the game screen provided.
Focus on spatial awareness (what is to the left, right, ahead), key items, enemies, and UI status (e.g., health bar).
Be brief, action-oriented, and do not provide unnecessary fluff. Read the screen as if you are the player's eyes."""

SENTINEL_SYSTEM_PROMPT = """You are Echo's Sentinel Agent. You watch the game screen strictly for immediate dangers.
Respond ONLY with a short, urgent warning if an enemy or hazard is actively threatening the player (e.g., 'Warning: Skeleton approaching from behind!').
If there is no immediate danger, respond exactly with the word: SAFE."""

# Agent Intervals
NARRATOR_INTERVAL = 2.0   # seconds between auto-narrations
SENTINEL_INTERVAL = 0.5   # seconds between danger checks