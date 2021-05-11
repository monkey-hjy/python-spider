#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @File    :   qcc.py    
# @Author  :   Monkey
# @DATE    :   2021/5/11 下午5:13 

import requests
import re
from lxml import etree


class QCC(object):
    """企查查爬虫"""

    def __init__(self):
        self._headers = {
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
        }

    def get_cookie(self):
        """发起一次测试请求，获取到搜索的cookie"""
        url = 'https://www.qcc.com/web/search?key=测试'
        response = requests.get(url, headers=self._headers, allow_redirects=False)
        response.encoding = 'utf8'
        result = re.findall(r'div>您的请求ID是: <strong>\n(.*?)</strong></div>',  response.text)
        if result:
            return result[0]

    def search(self, search_keyword):
        """搜索"""
        url = 'https://www.qcc.com/web/search?key={}'.format(search_keyword)
        headers = self._headers
        headers['cookie'] = 'acw_tc={}'.format(self.get_cookie())
        response = requests.get(url, headers=headers)
        response.encoding = 'utf8'
        html = etree.HTML(response.text)
        com_url = html.xpath('//a[@class="title"]/@href')
        print('搜索到{}条结果。即将开始获取详细信息...'.format(len(com_url)))
        for url in com_url:
            self.get_com_info(url)

    def get_com_info(self, url):
        """获取公司的详细信息"""
        response = requests.get(url, headers=self._headers)
        html = etree.HTML(response.text)
        info_elements = html.xpath('//table[@class="ntable"]/tr')
        item = {'url': url}
        flag = True
        for element in info_elements:
            if not flag:
                break
            for index in range(0, len(element.xpath('./td')), 2):
                try:
                    key = element.xpath('./td[{}]/text()'.format(index+1))[0].strip()
                    if key == '公司介绍：' or key == '经营范围':
                        flag = False
                    if key == '法定代表人':
                        item[key] = element.xpath('./td[{}]//h2/text()'.format(index+2))[0].strip()
                    else:
                        item[key] = element.xpath('./td[{}]//text()'.format(index+2))[0].strip()
                except:
                    pass
        print(item)

    def run(self):
        """启动函数"""
        self.search(search_keyword='腾讯')


if __name__ == '__main__':
    t = QCC()
    t.run()


