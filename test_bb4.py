import asyncio
import google.generativeai as genai
from config import BACKBOARD_API_KEY, GEMINI_API_KEY
from backboard import BackboardClient

class MockMemoryClient:
    def __init__(self):
        self.client = BackboardClient(api_key=BACKBOARD_API_KEY)
        self.assistant_id = None
        self.thread_id = None
        genai.configure(api_key=GEMINI_API_KEY)
        self.llm = genai.GenerativeModel("gemini-2.5-flash")

    async def initialize(self):
        assistant = await self.client.create_assistant(name="Echo Gaming Companion")
        self.assistant_id = assistant.assistant_id
        thread = await self.client.create_thread(self.assistant_id)
        self.thread_id = thread.thread_id

    async def query_with_memory(self, prompt: str) -> str:
        try:
            await self.client.add_message(
                thread_id=self.thread_id,
                content=prompt,
                send_to_llm=False,
            )
            
            memories_response = await self.client.search_memories(
                assistant_id=self.assistant_id,
                query=prompt,
                limit=5
            )
            
            memory_context = ""
            if memories_response and "memories" in memories_response:
                memories = memories_response["memories"]
                memory_context = "\n".join([f"- {m.get('content', '')}" for m in memories])
            
            if memory_context.strip():
                local_prompt = f"Relevant Past Memories:\n{memory_context}\n\nPrompt: {prompt}"
            else:
                local_prompt = prompt
                
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm.generate_content(local_prompt)
            )
            return response.text.strip()
        except Exception as e:
            return f"Error: {e}"

async def test():
    client = MockMemoryClient()
    await client.initialize()
    resp = await client.query_with_memory("Based on your memory, briefly summarize what I accomplished in my last play session. If first session, say so.")
    print("Response:", resp)

asyncio.run(test())
