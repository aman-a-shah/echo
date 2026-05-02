import asyncio

class App:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
    
    async def run(self):
        print(f"Init loop: {id(self.loop)}")
        print(f"Run loop:  {id(asyncio.get_running_loop())}")

app = App()
asyncio.run(app.run())
