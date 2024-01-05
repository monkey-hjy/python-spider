# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/14 11:35
# Auth: HJY

"""
wasm加密
e = this.$wasm.asm.encrypt(offset, time);
"""

import requests
import pywasm

import time
import os

wasm_fun = pywasm.load('scrapeCenter/spa14/Wasm.wasm')
res = wasm_fun.exec('encrypt', [0, int(time.time())])

url = 'https://spa14.scrape.center/api/movie/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.115 Safari/537.36'
}
params = {
    'limit': 100,
    'offset': 0,
    'sign': res
}
response = requests.get(url, headers=headers, params=params).json()
print(len(response['results']))
