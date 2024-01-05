# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/13 18:13
# Auth: HJY

"""有token参数加密"""

import requests

from loguru import logger
import hashlib
import base64
import time


def get_token(offset):
    now_t = str(int(time.time()))
    res = hashlib.sha1(f'/api/movie,{offset},{now_t}'.encode('utf8')).hexdigest()
    res += f',{now_t}'
    res = base64.b64encode(res.encode('utf8')).decode()
    return res

url = 'https://spa2.scrape.center/api/movie/'
params = {
    'limit': 100,
    'offset': 0,
    'token': get_token(0)
}
response = requests.get(url, params=params).json()
for info in response['results']:
    logger.info(f'name: {info["name"]}, published_at: {info["published_at"]}, score: {info["score"]}')
