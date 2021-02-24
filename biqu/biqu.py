# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-02-24 17:12:52
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-02-24 17:16:23
import requests
from lxml import etree
import random
from datetime import datetime

# 随机UA头
USER_AGENT = [
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
    "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
    "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
]


def get_response(url):
    headers = {
        'User-Agent': random.choice(USER_AGENT),
        'Host': 'www.paoshuzw.com',
        'Connection': 'keep-alive'
    }
    while True:
        # 发现请求次数多之后会出503。所以加上while循环，直到请求成功为止
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding
                return response.text
            else:
                raise KeyError
        except:
            headers['User-Agent'] = random.choice(USER_AGENT)


if __name__ == '__main__':
    # 在这里指定书籍的链接
    book_url = 'http://www.paoshuzw.com/8/8345/'
    html = etree.HTML(get_response(book_url))
    book_name = html.xpath('//div[@id="info"]/h1/text()')[0]
    zj_url = html.xpath('//div[@id="list"]//a/@href')
    for url in zj_url:
        html = etree.HTML(get_response('http://www.paoshuzw.com' + url))
        title = html.xpath('//h1/text()')[0].strip()
        content = ''.join(html.xpath('//div[@id="content"]/text()')).replace('\r', '\n')
        print(datetime.now(), title)
        with open(f'{book_name}.txt', 'a', encoding='utf8') as f:
            f.write(title + '\n')
            f.write(content + '\n\n')
