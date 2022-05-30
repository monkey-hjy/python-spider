# -*- encoding: utf-8 -*-
# NAME: crawler.py
# Date: 2022/05/30 23:05
# Auth: HJY
import requests
import execjs

ctx = execjs.compile(open('./demo.js', encoding='utf-8').read())
url = 'https://webapi.cninfo.com.cn/api/sysapi/p_sysapi1007'
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'mcode': ctx.call('getResCode')
}
data = {
    'tdate': '2022-05-27',
    'market': 'SZE'
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
