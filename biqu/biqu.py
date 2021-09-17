# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-02-24 17:12:52
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-02-24 17:16:23
import requests
from lxml import etree
import random
from datetime import datetime, time

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


class SpiderBook(object):

    def __init__(self):
        self.search_url = 'https://www.biqooge.com/modules/article/search.php'
        self._headers = {'user-agent': random.choice(USER_AGENT)}
    
    def search_book(self):
        book_name = self.book_name
        data = {
            'searchtype': 'articlename',
            'searchkey': book_name.encode('gbk'),
        }
        response = requests.post(self.search_url, headers=self._headers, data=data)
        response.encoding = response.apparent_encoding
        html = etree.HTML(response.text)
        name = html.xpath('//tr[@id="nr"]/td[1]/a/text()')
        book_url = html.xpath('//tr[@id="nr"]/td[1]/a/@href')
        author = html.xpath('//tr[@id="nr"]/td[3]/text()')
        for i in range(len(name)):
            print('编号{}信息：作者-{}\t书名-{}'.format(i, author[i], name[i]))
        need_id = int(input('输入需要的书籍编号：'))
        self.download_book(book_url[need_id])
    
    def download_book(self, book_url):
        response = requests.get(book_url, headers=self._headers)
        response.encoding = response.apparent_encoding
        html = etree.HTML(response.text)
        zj_info = html.xpath('//dt[contains(text(), "章节目录")]/following-sibling::dd')
        for i in range(len(zj_info)):
            info = zj_info[i]
            zj_name = info.xpath('./a/text()')[0]
            zj_url = 'https://www.biqooge.com' + info.xpath('./a/@href')[0]
            zj_response = requests.get(zj_url, headers=self._headers)
            zj_response.encoding = zj_response.apparent_encoding
            zj_html = etree.HTML(zj_response.text)
            content = ''.join(zj_html.xpath('//div[@id="content"]/text()'))
            print('{}/{}\tname:{}\turl:{}'.format(i+1, len(zj_info), zj_name, zj_url))
            with open('{}.txt'.format(self.book_name), 'a', encoding='utf8') as f:
                f.write(zj_name + '\n')
                f.write(content + '\n\n')
    
    def run(self):
        self.book_name = '完美世界'
        self.search_book()


if __name__ == '__main__':
    s = SpiderBook()
    s.run()
