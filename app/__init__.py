from aiohttp import web

from .api_fetch import app as api_fetch

__all__ = ["api_fetch"]