# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/13 18:44
# Auth: HJY

"""动态渲染"""

import requests

url = 'https://spa5.scrape.center/api/book/?limit=5000&offset=0'
response = requests.get(url).json()
print(len(response['results']))
