# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/13 18:40
# Auth: HJY

"""下滑页面获取新数据"""

import requests

url = 'https://spa3.scrape.center/api/movie/?limit=100&offset=0'
response = requests.get(url).json()
print(len(response['results']))
