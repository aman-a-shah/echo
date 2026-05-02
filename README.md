# 🦇 Echo: AI-Powered Voice Navigation for Blind Gamers

![Echo Banner](https://img.shields.io/badge/HuskyHacks-2026-blue?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.10%2B-green?style=for-the-badge)
![Gemini AI](https://img.shields.io/badge/Google-Gemini_2.5_Flash-orange?style=for-the-badge)
![Backboard.io](https://img.shields.io/badge/Powered_by-Backboard.io-purple?style=for-the-badge)

> *"Echo is the co-pilot that never stops watching — a voice-first AI companion that describes, remembers, and responds, so blind players can experience any game on equal footing."*

---

## 🎯 The Problem

Over 285 million people worldwide live with visual impairment. For these individuals, video games — one of the world's largest entertainment industries — are almost entirely inaccessible. Existing solutions are fragmented: screen readers weren't built for fast-paced visual scenes, and the handful of accessible games built from scratch represent a tiny fraction of the catalog.

Echo solves this at the infrastructure level. Rather than building one accessible game, Echo is a universal **AI overlay** that makes *any* game playable through voice — turning sound into the primary interface and AI into the player's eyes.

## ✨ Features

- **Live Screen Narration**: Captures game frames continuously. Uses **Gemini 2.5 Flash** with a custom prompt tuned for spatial, action-oriented descriptions, read aloud in real-time.
- **On-Demand Description**: Instantly get a full scene breakdown by pressing a single key.
- **Question Mode**: Ask freeform questions ("What's to my left?", "How much health do I have?") using natural voice.
- **Stateful Memory**: Powered by **Backboard.io**, Echo remembers key facts across sessions: player preferences, previous locations, and inventory history. When you return, Echo gives you a recap of where you left off.
- **Multi-Agent Watchers**: Multiple agents run in parallel. While the narrator describes the scene, a background Sentinel agent watches for immediate danger and interrupts with urgent alerts.
- **Game Manual RAG**: Ask lore and strategy questions! Echo cross-references live screen data with an uploaded game manual (using Backboard RAG) to give you the perfect hints.
- **Invisible UI**: There is no screen to read and no mouse to click. Echo exists entirely in audio.

---

## 🛠️ Setup and Installation

### Prerequisites

Echo is designed primarily for macOS but uses cross-platform Python libraries.

1. **Python 3.10+**
2. **System Dependencies (macOS):**
   You'll need `portaudio` for microphone input (via `pyaudio`) and `flac` for the SpeechRecognition library.
   ```bash
   brew install portaudio flac
   ```

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/echo.git
   cd echo
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API Keys:**
   Create a `.env` file in the root directory and add your API keys:
   ```env
   GEMINI_API_KEY=your_gemini_key
   BACKBOARD_API_KEY=your_backboard_key
   # Optional: For cycling vision providers
   CEREBRAS_API_KEY=your_cerebras_key
   OPENROUTER_API_KEY=your_openrouter_key
   ```

---

## 🚀 Usage

To start Echo, simply run:

```bash
python main.py
```

Upon launching, Echo will greet you and summarize your previous session (if any). It will then run silently in the background, listening for your commands and hotkeys.

### ⌨️ Global Hotkeys

These commands work globally, even when the game window is focused:

- <kbd>Space</kbd> : Trigger an immediate, full-scene description.
- <kbd>Q</kbd> : Enter Question Mode (wait for the beep, then speak your question).
- <kbd>P</kbd> : Pause / Resume continuous narration.
- <kbd>V</kbd> : Cycle through Vision Providers (e.g., Gemini → OpenRouter).
- <kbd>+</kbd> / <kbd>-</kbd> : Increase / Decrease Text-to-Speech speaking rate.
- <kbd>Esc</kbd> : Stop the current narration immediately.

### 🎙️ Voice Commands

When in Question Mode (<kbd>Q</kbd>), you can ask things like:
- *"What's to my left?"*
- *"How much health do I have?"*
- *"Remember that the blue key is in the east room."* (Stores memory in Backboard)
- *"What happened last time?"* (Recalls session summary)

---

## 🧠 Technical Architecture

Echo combines several cutting-edge technologies into a seamless async pipeline:

| Layer | Technology | Role |
|-------|------------|------|
| **Screen Capture** | `mss` | Ultra-fast, cross-platform screen grabs without GPU overhead. |
| **Vision AI** | Gemini 2.5 Flash | Multimodal frame analysis optimized for spatial game state. |
| **Memory & State** | Backboard.io | Persistent game state and session history using `memory='Auto'`. |
| **Multi-Agent Sync** | `asyncio` & Threads | Parallel execution of Narrator and Sentinel (Danger) agents. |
| **Voice Input** | SpeechRecognition | Captures user queries to send to Gemini. |
| **Text-to-Speech** | macOS `say` / `pyttsx3` | Zero-dependency, native audio feedback. |

## 🏆 Hackathon Context
**HuskyHacks 2026**

Echo is designed to compete across multiple prize tracks:
- **🎯 Best Reach:** Directly removes the biggest barrier blind people face in gaming.
- **🧪 Wild Experiment:** The interface *is* the experiment—zero screen, zero cursor, entirely voice-operated.
- **🔧 Backboard.io Track:** Deeply integrated stateful memory, multi-agent orchestration, and document RAG.
- **✨ Google Gemini:** Powered by Gemini 2.5 Flash for rapid, multimodal scene comprehension.

---

*Built with ❤️ for a more accessible gaming future.*
