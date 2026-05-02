from backboard import BackboardClient
from config import BACKBOARD_API_KEY, NARRATOR_SYSTEM_PROMPT
import base64

class BackboardMemoryClient:
    def __init__(self):
        self.client = BackboardClient(api_key=BACKBOARD_API_KEY)
        self.assistant_id = None
        self.thread_id = None

    async def initialize_session(self):
        """
        Creates an Assistant and starts a new Thread for the session.
        """
        print("Initializing Backboard memory session...")
        try:
            assistant = await self.client.create_assistant(
                name="Echo Gaming Companion",
                system_prompt=NARRATOR_SYSTEM_PROMPT,
                llm_provider="google",
                llm_model_name="gemini-2.5-flash"
            )
            self.assistant_id = assistant.assistant_id

            thread = await self.client.create_thread(self.assistant_id)
            self.thread_id = thread.thread_id

            print("Backboard session initialized successfully.")
            return True
        except Exception as e:
            print(f"Failed to initialize Backboard: {e}")
            return False

    async def query_with_memory(self, prompt: str) -> str:
        """
        Sends a message to the Backboard Thread with persistent memory.
        """
        if not self.thread_id:
            return "Memory not initialized."
        try:
            response = await self.client.add_message(
                thread_id=self.thread_id,
                content=prompt,
                memory="Auto",
                stream=False
            )
            return response.content
        except Exception as e:
            print(f"Error communicating with Backboard: {e}")
            return "There was an error communicating with memory."

    async def explicit_memory_store(self, fact: str) -> str:
        prompt = f"Please explicitly remember this fact for future reference: {fact}"
        return await self.query_with_memory(prompt)

    async def get_session_summary(self) -> str:
        prompt = "Summarize what I accomplished last session and my current game state based on your memory."
        return await self.query_with_memory(prompt)
