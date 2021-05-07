# -*- coding: utf-8 -*-
# Author:   玛卡巴卡
# Date:     2021/5/6 14:39

import requests
from lxml import etree
import pymysql


class Lianjia(object):
    """抓取链家租房信息"""

    def __init__(self):
        self.conn = pymysql.Connect(host='localhost', port=3306, user='root', password='root', database='demo')
        self.cursor = self.conn.cursor()
        self._headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'}

    def __del__(self):
        self.conn.close()

    def get_response(self, url):
        """发起请求"""
        response = requests.get(url, headers=self._headers)
        if response.status_code == 200:
            response.encoding = 'utf8'
            return response
        else:
            print('url:{}\tresponse:{}'.format(url, response))

    def get_city_url(self):
        """获取到城市的链接"""
        url = 'https://www.lianjia.com/city/'
        html = etree.HTML(self.get_response(url).text)
        city_url = html.xpath('//ul[@class="city_list_ul"]//a/@href')
        for url in city_url:
            self.get_district_url(city_url=url)

    def get_district_url(self, city_url):
        """获取到区的链接"""
        html = etree.HTML(self.get_response(city_url + 'zufang/').text)
        district_url = html.xpath('//li[@class="filter__item--level2  "]/a/@href')
        for url in district_url:
            self.get_house_count(url=city_url[:-1] + url)

    def get_house_count(self, url):
        """获取当前区的房子数量"""
        html = etree.HTML(self.get_response(url).text)
        count = int(html.xpath('//span[@class="content__title--hl"]/text()')[0])
        if count:
            if count >= 3000:
                filter_next_url = html.xpath('//li[@class="filter__item--level3  "]/a/@href')
                for filter_url in filter_next_url:
                    the_filter_url = '/'.join(url.split('/')[:3]) + filter_url
                    html = etree.HTML(self.get_response(the_filter_url).text)
                    count = min(int(html.xpath('//span[@class="content__title--hl"]/text()')[0]), 3000)
                    self.start(the_filter_url, count // 30 + 1)
            else:
                self.start(url, count // 30 + 1)
        else:
            print('{} 无房源'.format(url))

    def start(self, url, end_page):
        """开始抓取数据"""
        for page in range(1, end_page+1):
            self.get_page_info(url='{}pg{}/'.format(url, page))

    def get_page_info(self, url):
        """获取当前页房源信息"""
        print(url, end='\t')
        err_count = 0
        response = self.get_response(url)
        html = etree.HTML(response.text)
        house_element = html.xpath('//div[@class="content__list--item"]')
        for element in house_element:
            try:
                house_url = '/'.join(url.split('/')[:3]) + element.xpath('./a/@href')[0]
                house_code = element.xpath('./@data-house_code')[0]
                title = element.xpath('./a/@title')[0]
                des = ''.join(element.xpath('./div/p[2]//text()')).replace('\n', '').replace('    ', ' ')
                price = int(element.xpath('./div/span/em/text()')[0])
                sql = "INSERT INTO lianjia (id, url, title, des, price) values ('%s', '%s', '%s', '%s', %d);" % (house_code, house_url, title, des, price)
                self.cursor.execute(sql)
                self.conn.commit()
            except Exception as e:
                err_count += 1
        print('出错占比：{}/{}'.format(err_count, len(house_element)))

    def run(self):
        """启动函数"""
        self.get_city_url()


if __name__ == '__main__':
    t = Lianjia()
    t.run()
