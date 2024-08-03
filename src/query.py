import aiohttp
import asyncio
import certifi
import ssl

from pyppeteer import launch


ssl_context = ssl.create_default_context(cafile=certifi.where())
semaphore = asyncio.Semaphore(1)

async def fetch(session, url):
    async with semaphore:
        async with session.get(url) as response:
            return await response.text()
    
async def fetch_all(urls):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        texts = []
        for url in urls:
            text = await fetch(session, url)
            texts.append(text)
            await asyncio.sleep(3)
        return texts
