import async_timeout
from aiohttp import ClientSession

async def fetch(url):
    with async_timeout.timeout(20):
        async with ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()
