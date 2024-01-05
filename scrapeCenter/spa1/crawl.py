# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/13 18:10
# Auth: HJY

"""Ajax请求返回数据"""

import requests
from loguru import logger

url = 'https://spa1.scrape.center/api/movie/?limit=100&offset=0'
response = requests.get(url).json()
for info in response['results']:
    logger.info(f'name: {info["name"]}, published_at: {info["published_at"]}, score: {info["score"]}')
