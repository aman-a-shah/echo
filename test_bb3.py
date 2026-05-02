import asyncio
from backboard_client import BackboardMemoryClient

async def test():
    client = BackboardMemoryClient()
    await client.initialize_session()
    
    print("\n--- send_to_llm=False ---")
    resp3 = await client.client.add_message(
        thread_id=client.thread_id,
        content="Based on your memory, briefly summarize what I accomplished in my last play session. If first session, say so.",
        send_to_llm=False,
    )
    print("Response:", resp3)

asyncio.run(test())
