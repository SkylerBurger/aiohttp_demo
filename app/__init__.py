from flask import Flask
from aiohttp import ClientSession
import feedparser

import asyncio
import json
import time

def create_app():
    app = Flask(__name__)

    with app.app_context():

        async def fetch(session, url):
            """
            Takes in a ClientSession and a URL string.
            Awaits a request to the given URL.
            Returns the payload.
            """
            async with session.get(url) as response:
                return await response.text()


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


        @app.route('/')
        async def main():
            """
            Takes in a Request object from the client.
            Creates a ClientSession and coroutines for each API.
            Awaits the normalized entries from the gathered coroutines.
            Returns all of the normalized entries.
            """
            start_time = time.perf_counter()
            entries = []
            async with ClientSession() as session:
                entries.append(normalize_github(session, 'https://api.github.com/search/repositories?q=language:python&sort=stars&order=desc', 'popular'))
                entries.append(normalize_github(session, 'https://api.github.com/search/repositories?q=language:python&sort=updated&order=desc', 'updated'))
                entries.append(normalize_pypi(session, 'https://pypi.org/rss/updates.xml', 'updated'))
                entries.append(normalize_pypi(session, 'https://pypi.org/rss/packages.xml', 'newest'))

                results = await asyncio.gather(*entries)

            elapsed_time = time.perf_counter() - start_time
            print(f'Elapsed time: {elapsed_time:0.2f}')
            return Flask.Response(json.dumps(results))

    return app