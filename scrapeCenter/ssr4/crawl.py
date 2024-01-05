# -*- encoding: utf-8 -*-
# NAME: scrapy.py
# Date: 2022/06/13 17:49
# Auth: HJY

"""做延时。异步加快速度"""

import requests
import asyncio
import aiohttp
from loguru import logger

import time


start_time = time.time()


async def get(url):
    session = aiohttp.ClientSession()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',
    }
    response = await session.get(url, headers=headers, verify_ssl=False)
    await response.text()
    await session.close()
    return response


async def start(page):
    url = f'https://ssr4.scrape.center/page/{page}'
    logger.info(f'get {url}')
    response = await get(url)
    logger.info(f'get {url} done, response.status={response.status}')


tasks = [asyncio.ensure_future(start(page)) for page in range(1, 10)]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(tasks))
end_time = time.time()
logger.info(f'耗时: {end_time - start_time}')

