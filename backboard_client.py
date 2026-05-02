from backboard import BackboardClient
from config import BACKBOARD_API_KEY, NARRATOR_SYSTEM_PROMPT


class BackboardMemoryClient:
    def __init__(self):
        self.client = BackboardClient(api_key=BACKBOARD_API_KEY)
        self.assistant_id = None
        self.thread_id = None

    async def initialize_session(self):
        """Creates an Assistant and starts a new Thread for this play session."""
        print("Initializing Backboard memory session...")
        try:
            # Create (or reuse) a named assistant
            assistant = await self.client.create_assistant(
                name="Echo Gaming Companion",
                system_prompt=NARRATOR_SYSTEM_PROMPT,
                llm_provider="google",
                llm_model_name="gemini-2.5-flash",
            )
            self.assistant_id = assistant.assistant_id

            # Each session = a new thread, but memory persists across threads
            thread = await self.client.create_thread(self.assistant_id)
            self.thread_id = thread.thread_id

            print(f"Backboard ready. Assistant: {self.assistant_id[:8]}... Thread: {self.thread_id[:8]}...")
            return True
        except Exception as e:
            print(f"Failed to initialize Backboard: {e}")
            return False

    async def query_with_memory(self, prompt: str) -> str:
        """
        Sends a message with memory='Auto' so Backboard automatically
        extracts and stores relevant facts from every exchange.
        """
        if not self.thread_id:
            return "Memory not initialized."
        try:
            response = await self.client.add_message(
                thread_id=self.thread_id,
                content=prompt,
                memory="Auto",
                stream=False,
            )
            return response.content
        except Exception as e:
            print(f"Backboard error: {e}")
            return "There was an error communicating with memory."

    async def explicit_memory_store(self, fact: str) -> str:
        """For 'Echo, remember...' voice commands."""
        prompt = f"Please explicitly remember this fact for future sessions: {fact}"
        return await self.query_with_memory(prompt)

    async def get_session_summary(self) -> str:
        """Called on startup to recall what happened last session."""
        prompt = (
            "Based on your memory, briefly summarize what I accomplished in my last play session "
            "and what my current game state is. If this is the first session, say so."
        )
        return await self.query_with_memory(prompt)