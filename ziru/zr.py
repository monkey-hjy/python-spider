from pytesseract.pytesseract import image_to_string
import requests
from lxml import etree
from PIL import Image
import pytesseract
import re
import time
import os
import pymysql


class Ziru(object):

    def __init__(self):
        self._headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36'}
        self.city_info =  dict()
        self.cwd = '/'.join(__file__.split('/')[:-1])
        self.conn = pymysql.Connection(host='localhost', user='root', password='root', database='demo', port=3306)
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        self.conn.close()
    
    def get_response(self, url):
        response = requests.get(url, headers=self._headers)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            return response
        else:
            print(response.status_code)
            return None
    
    def get_city_info(self):
        response = self.get_response(url='https://www.ziroom.com/')
        if response is None:
            return
        html = etree.HTML(response.text)
        city_name = html.xpath('//a[@class="Z_city_option ani"]/text()')
        city_url = html.xpath('//a[@class="Z_city_option ani"]/@href')
        self.city_info = dict(zip(city_name, city_url))
    
    @staticmethod
    def image_identification(img_path):
        the_img = Image.open(img_path)
        result = pytesseract.image_to_string(the_img, config='--psm 7')
        os.remove(img_path)
        return list(result.strip())
    
    def get_zone_info(self, city_url):
        response = self.get_response(city_url + 'z/')
        if response is None:
            return
        html = etree.HTML(response.text)
        zone_url = html.xpath('//a[text()="区域"]/following-sibling::div/a/@href')
        zone_name = html.xpath('//a[text()="区域"]/following-sibling::div/a/text()')
        zone_info = dict(zip(zone_name, zone_url))
        for key in zone_info:
            print('开始获取{}的数据'.format(key))
            self.get_room_info('https:{}'.format(zone_info[key]))
    
    def get_room_info(self, url):
        response = self.get_response(url)
        if response is None:
            print('{}获取失败'.format(url))
            return
        print(url)
        html = etree.HTML(response.text)
        title = html.xpath('//h5[starts-with(@class, "title")]/a/text()')
        room_url = ['https:{}'.format(info) for info in html.xpath('//h5[starts-with(@class, "title")]/a/@href')]
        desc = html.xpath('//div[@class="desc"]/div[1]/text()')
        location = [info.strip() for info in html.xpath('//div[@class="location"]/text()')]
        room_price = list()
        room_element = html.xpath('//div[@class="Z_list"]/div[2]/div')
        for element in room_element:
            price = ''
            img_url = element.xpath('.//span[@class="num"]/@style')
            if not img_url:
                continue
            img_url = re.findall('url\((.*?)\)', img_url[0])[0]
            price_position = [float(re.findall('position: -(.*?)px', info)[0]) for info in element.xpath('.//span[@class="num"]/@style')]
            img_path = os.path.join(self.cwd, img_url.split('/')[-1])
            with open(img_path, 'wb') as f:
                f.write(self.get_response('https:{}'.format(img_url)).content)
            img_nums = self.image_identification(img_path)
            for position in price_position:
                price += img_nums[int(position / 20)]
            try:
                room_price.append(int(price))
            except:
                room_price.append(None)
        data = {
            '标题': title,
            '链接': room_url,
            '信息': desc,
            '地址': location,
            '价格': room_price,
        }
        self.save_data(data)
        next_url = html.xpath('//a[@class="next"]/@href')
        if next_url:
            self.get_room_info('https:{}'.format(next_url[0]))
    
    def save_data(self, item):
        data = list()
        for i in range(len(item['标题'])):
            info = list()
            for key in item.keys():
                info.append(item[key][i])
            data.append(info)
        sql = 'INSERT INTO ziru (title, url, info, location, price) VALUES (%s, %s, %s, %s, %s);'
        # print(data)
        self.cursor.executemany(sql, data)
        self.conn.commit()
        print('保存成功{}条'.format(len(data)))
    
    def run(self):
        self.get_zone_info('https://sh.ziroom.com/')


if __name__ == '__main__':
    s = Ziru()
    s.run()

