# -*- encoding: utf-8 -*-
# NAME: crawl.py
# Date: 2022/06/13 17:37
# Auth: HJY

"""静态网站。直接请求"""

import requests
from lxml import etree


def parse_page(page):
    url = 'https://ssr1.scrape.center/page/{}'.format(page)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.61 Safari/537.36'
    }
    response = requests.get(url=url, headers=headers)
    response.encoding = response.apparent_encoding
    html = etree.HTML(response.text)
    info_element = html.xpath('//div[@class="el-col el-col-18 el-col-offset-3"]/div')
    for info in info_element:
        title = info.xpath('.//h2/text()')[0]
        types = ','.join(info.xpath('.//div[@class="categories"]//span/text()'))
        score = info.xpath('.//p[@class="score m-t-md m-b-n-sm"]/text()')[0].strip()
        item = {'标题': title, '类型': types, '评分': score}
        print(f'page: {page}, item: {item}')
    if info_element:
        parse_page(page + 1)


parse_page(1)

