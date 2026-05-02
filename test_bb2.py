import asyncio
from backboard_client import BackboardMemoryClient

async def test():
    client = BackboardMemoryClient()
    await client.initialize_session()
    
    print("\n--- No LLM ---")
    resp3 = await client.client.add_message(
        thread_id=client.thread_id,
        content="Based on your memory, briefly summarize what I accomplished in my last play session. If first session, say so.",
        llm_provider=None,
        model_name=None,
        memory="Always",
        stream=False,
    )
    print("No LLM response:", resp3)

asyncio.run(test())
