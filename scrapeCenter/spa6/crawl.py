# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/14 10:48
# Auth: HJY

"""js加密。有混淆"""

import hashlib
import requests
import time
import base64


def get_token():
    now_t = str(int(time.time()))
    _0x189cbb = ['/api/movie', now_t]
    _0xf7c3c7 = hashlib.sha1(','.join(_0x189cbb).encode('utf8')).hexdigest()
    _0x3c8435 = _0xf7c3c7 + ',' + now_t
    _0x104b5b = base64.b64encode(_0x3c8435.encode('utf8')).decode('utf8')
    return _0x104b5b

url = 'https://spa6.scrape.center/api/movie/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.115 Safari/537.36'
}
params = {
    'limit': 10,
    'offset': 10,
    'token': get_token(),
}
response = requests.get(url=url, headers=headers, params=params).json()
print(len(response['results']))
