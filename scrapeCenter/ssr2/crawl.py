# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/13 17:45
# Auth: HJY

"""无证书。关闭证书验证即可"""

import requests

url = 'https://ssr2.scrape.center/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36'
}
response = requests.get(url, headers=headers, verify=False)
print(response.text)
