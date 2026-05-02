import asyncio
from backboard_client import BackboardMemoryClient

async def test():
    client = BackboardMemoryClient()
    await client.initialize_session()
    
    resp = await client.client.search_memories(
        assistant_id=client.assistant_id,
        query="What happened in my last play session?",
        limit=5
    )
    print("Search result type:", type(resp))
    print("Search result:", resp)

asyncio.run(test())
