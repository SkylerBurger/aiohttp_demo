from aiohttp import web, ClientSession
import feedparser

import asyncio
import time
import json
import os


__all__ = ["app"]

routes = web.RouteTableDef()

# =====
# FETCH
# =====

async def fetch(session, url):
    """
    Takes in a ClientSession and a URL string.
    Awaits a request to the given URL.
    Returns the payload.
    """
    async with session.get(url) as response:
        return await response.text()


# ===========
# NORMALIZERS
# ===========

async def normalize_reddit_webdev(session, url, category):
    """
    Takes in a ClientSession and a URL string to WebDev Subreddit.
    Awaits a fetch coroutine, then normalizes the payload.
    Returns the normalized entries.
    """
    print('url start', url)
    response = json.loads(await fetch(session, url))
    print('url done', url)
    entries = response['data']['children']
    normalized_entries = {
        'source': 'reddit',
        'category': category,
        'data':[]
    }

    for entry in entries:
        normalized_entries['data'].append({
            'title': entry['data'].get('title', None),
            'link': entry['data'].get('permalink', None),
            #some results have thumbnail urls
            'thumbnail': entry['data'].get('thumbnail', None),
        })

    return normalized_entries


async def normalize_reddit_programmerhumor(session, url, category):
    """
    Takes in a ClientSession and a URL string to Programmer Humor Subreddit.
    Awaits a fetch coroutine, then normalizes the payload.
    Returns the normalized entries.
    """
    print('url start', url)
    response = json.loads(await fetch(session, url))
    print('url done', url)

    entries = response['data']['children']
    normalized_entries = {
        'source': 'reddit',
        'category': category,
        'data':[]
    }

    for entry in entries:

        normalized_entries['data'].append({
            'title': entry['data'].get('title', None),
            'link': entry['data'].get('permalink', None),
            'image': entry['data'].get('url', None),
        })

    return normalized_entries


async def normalize_reddit_no_image(session, url, category):
    """
    Takes in a ClientSession and a URL string to Python Subreddit.
    Awaits a fetch coroutine, then normalizes the payload.
    Returns the normalized entries.
    """
    print('url start', url)
    response = json.loads(await fetch(session, url))
    print('url done', url)

    entries = response['data']['children']
    normalized_entries = {
        'source': 'reddit',
        'category': category,
        'data':[]
    }

    for entry in entries:
        normalized_entries['data'].append({
            'title': entry['data'].get('title', None),
            'link': entry['data'].get('permalink', None),
        })

    return normalized_entries


async def normalize_pypi(session, url, category):
    """
    Takes in a ClientSession and a URL string to PyPI.
    Awaits a fetch coroutine, then normalizes the payload.
    Returns the normalized entries.
    """
    print('url start', url)
    feed_data = feedparser.parse(await fetch(session, url))
    print('url done', url)
    entries = feed_data.entries
    normalized_entries = []
    for entry in entries:
        normalized_entries.append({
            'source': 'pypi',
            'category': category,
            'title': entry['title'],
            'link': entry['link'],
            'desc': entry['summary']
        })

    return normalized_entries


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


# ======
# ROUTES
# ======

@routes.get('/')
async def get_github(request):
    start_time = time.perf_counter()
    entries = []

    async with ClientSession() as session:
        entries.append(normalize_github(session, 'https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc', 'popular'))
        entries.append(normalize_github(session, 'https://api.github.com/search/repositories?q=language:python&sort=updated&order=desc', 'updated'))
        entries.append(normalize_reddit_webdev(session, 'https://www.reddit.com/r/webdev/.json?', 'webdev'))
        entries.append(normalize_reddit_programmerhumor(session, 'https://www.reddit.com/r/programmerhumor/.json?', 'programmerhumor'))
        entries.append(normalize_reddit_no_image(session, 'https://www.reddit.com/r/python/.json?', 'python'))
        entries.append(normalize_reddit_no_image(session, 'https://www.reddit.com/r/learnprogramming/.json?', 'learnprogramming'))
        entries.append(normalize_pypi(session, 'https://pypi.org/rss/updates.xml', 'updated'))
        entries.append(normalize_pypi(session, 'https://pypi.org/rss/packages.xml', 'newest'))

        results = await asyncio.gather(*entries)
    
    elapsed_time = time.perf_counter() - start_time
    print(f'Elapsed time: {elapsed_time:0.2f}')
    return web.Response(text=json.dumps(results))


# ===
# APP
# ===

app = web.Application()
app.add_routes(routes)