from aiohttp import web, ClientSession

import asyncio

from . import github

def main():
    

    async def start_async_app():
        runner = web.AppRunner(github)
        await runner.setup()
        
        return runner

    loop = asyncio.get_event_loop()
    runner = loop.run_until_complete(start_async_app())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(runner.cleanup())

main()