import asyncio
import google.generativeai as genai
from backboard import BackboardClient
from config import BACKBOARD_API_KEY, NARRATOR_SYSTEM_PROMPT, GEMINI_API_KEY


class BackboardMemoryClient:
    def __init__(self):
        self.client = BackboardClient(api_key=BACKBOARD_API_KEY)
        self.assistant_id = None
        self.thread_id = None
        
        # Configure local LLM to bypass Backboard generation costs
        genai.configure(api_key=GEMINI_API_KEY)
        self.llm = genai.GenerativeModel(
            "gemini-2.5-flash",
            system_instruction=(
                "You are Echo, a gaming companion. Answer the user's prompt using the retrieved memories. "
                "If there are no relevant memories, do not apologize—just answer the prompt naturally, or if asked about the past, say it's your first session together."
            )
        )

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
            # 1. Log to Backboard for passive memory extraction (costs no LLM chat credits)
            await self.client.add_message(
                thread_id=self.thread_id,
                content=prompt,
                send_to_llm=False,
            )
            
            # 2. Retrieve relevant memory context via RAG
            memories_response = await self.client.search_memories(
                assistant_id=self.assistant_id,
                query=prompt,
                limit=5
            )
            
            # 3. Format memories
            memory_context = ""
            if memories_response and "memories" in memories_response:
                memories = memories_response["memories"]
                memory_context = "\n".join([f"- {m.get('content', '')}" for m in memories])
            
            # 4. Synthesize response locally
            if memory_context.strip():
                local_prompt = f"Relevant Past Memories:\n{memory_context}\n\nUser Prompt: {prompt}"
            else:
                local_prompt = prompt
                
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm.generate_content(local_prompt)
            )
            return response.text.strip()
            
        except Exception as e:
            print(f"Backboard/Local LLM error: {e}")
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