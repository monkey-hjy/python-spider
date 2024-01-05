# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/14 11:27
# Auth: HJY

"""数据存储在js中"""

import requests

url = 'https://spa7.scrape.center/js/main.js'
response = requests.get(url).text
print(response)
