# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/13 17:46
# Auth: HJY

"""加http验证"""

import requests

url = 'https://ssr3.scrape.center/'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36',
    'Authorization': 'Basic YWRtaW46YWRtaW4='
}
response = requests.get(url, headers=headers)
print(response.text)
