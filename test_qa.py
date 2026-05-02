import asyncio
from agents import AgentsOrchestrator
from capture import ScreenCapturer
from audio import AudioController
from backboard_client import BackboardMemoryClient
from vision_client import VisionClient
import time

async def test():
    cap = ScreenCapturer()
    aud = AudioController()
    mem = BackboardMemoryClient()
    vis = VisionClient()
    vis._state.backoff = 40.0 # Force rate limit
    vis._state.last_call = time.monotonic()
    
    orch = AgentsOrchestrator(cap, aud, mem, vis)
    print("Calling ask_question")
    await orch.ask_question("what direction should I head in")
    print("Done")

asyncio.run(test())
