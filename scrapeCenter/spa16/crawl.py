# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/18 15:14
# Auth: HJY

"""http2协议"""

import httpx
client = httpx.Client(http2=True)
url = 'https://spa16.scrape.center/api/book/?limit=18&offset=0'
headers = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'
}
response = client.get(url, headers=headers)
print(response.text)
