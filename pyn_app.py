from aiohttp import web, ClientSession

import asyncio
import time
import json
import os


routes = web.RouteTableDef()


async def fetch(session, url):
    """
    Takes in a ClientSession and a URL string.
    Awaits a request to the given URL.
    Returns the payload.
    """
    async with session.get(url) as response:
        return await response.text()


async def normalize_github(session, url, category):
    """
    Takes in a ClientSession and a URL string to GitHub.
    Awaits a fetch coroutine, then normalizes the payload.
    Returns the normalized entries.
    """
    print('url start', url)
    response = json.loads(await fetch(session, url))
    print('url done', url)
    entries = response['items']
    normalized_entries = []

    for entry in entries:
        normalized_entries.append({
            'source': 'github',
            'category': category,
            'title': entry['name'],
            'link': entry['html_url'],
            'desc': entry['description'],
            'stars': entry['stargazers_count']
        })

    return normalized_entries


@routes.get('/')
async def get_github(request):
    start_time = time.perf_counter()
    entries = []

    async with ClientSession() as session:
        entries.append(normalize_github(session, 'https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc', 'popular'))
        entries.append(normalize_github(session, 'https://api.github.com/search/repositories?q=language:python&sort=updated&order=desc', 'updated'))

        results = await asyncio.gather(*entries)
    
    elapsed_time = time.perf_counter() - start_time
    print(f'Elapsed time: {elapsed_time:0.2f}')
    return web.Response(text=json.dumps(results))


app = web.Application()
app.add_routes(routes)


# Only for running this server locally by running this file
# web.run_app(app, host='localhost', port=8000)




async def start_app():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, os.environ['HOST'], os.environ['PORT'] or 3000)
    await site.start()
    print(f'**Your app is ready on localhost:8000')
    return runner, site

loop = asyncio.get_event_loop()
runner, site = loop.run_until_complete(start_app())
try:
    loop.run_forever()
except KeyboardInterrupt as err:
    loop.run_until_complete(runner.cleanup())