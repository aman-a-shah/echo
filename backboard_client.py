from backboard import BackboardClient
from config import BACKBOARD_API_KEY, NARRATOR_SYSTEM_PROMPT, MEMORY_LLM


class BackboardMemoryClient:
    def __init__(self):
        self.client = BackboardClient(api_key=BACKBOARD_API_KEY)
        self.assistant_id = None
        self.thread_id = None

    async def initialize_session(self):
        print("Initializing Backboard memory session...")
        try:
            assistant = await self.client.create_assistant(
                name="Echo Gaming Companion",
                system_prompt=NARRATOR_SYSTEM_PROMPT,
            )
            self.assistant_id = assistant.assistant_id
            thread = await self.client.create_thread(self.assistant_id)
            self.thread_id = thread.thread_id
            print(f"Backboard ready. Thread: {self.thread_id}")
            return True
        except Exception as e:
            print(f"Failed to initialize Backboard: {e}")
            return False

    async def query_with_memory(self, prompt: str) -> str:
        if not self.thread_id:
            return "Memory not initialized."
        try:
            response = await self.client.add_message(
                thread_id=self.thread_id,
                content=prompt,
                llm_provider=MEMORY_LLM["provider"],
                model_name=MEMORY_LLM["model"],
                memory="Auto",
                stream=False,
            )
            return response.content
        except Exception as e:
            print(f"Backboard error: {e}")
            return "There was an error communicating with memory."

    async def explicit_memory_store(self, fact: str) -> str:
        prompt = f"Please explicitly remember this fact for future sessions: {fact}"
        return await self.query_with_memory(prompt)

    async def get_session_summary(self) -> str:
        prompt = (
            "Based on your memory, briefly summarize what I accomplished in my last play session "
            "and my current game state. If this is the first session, say so."
        )
        return await self.query_with_memory(prompt)