import asyncio
from backboard_client import BackboardMemoryClient

async def test():
    client = BackboardMemoryClient()
    await client.initialize_session()
    
    # Try with Auto
    print("\n--- Auto ---")
    resp = await client.query_with_memory("Based on your memory, briefly summarize what I accomplished in my last play session. If first session, say so.")
    print("Auto response:", resp)

    # Try to modify memory param directly in add_message
    print("\n--- Always ---")
    resp2 = await client.client.add_message(
        thread_id=client.thread_id,
        content="Based on your memory, briefly summarize what I accomplished in my last play session. If first session, say so.",
        llm_provider="google",
        model_name="gemini-2.5-flash",
        memory="Always",
        stream=False,
    )
    print("Always response:", resp2.content)

asyncio.run(test())
