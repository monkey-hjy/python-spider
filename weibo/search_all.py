import json
import time

import pandas as pd
import requests
import random
import re
import datetime

from lxml import etree


class GetFansInfo(object):
    """搜索微博"""

    def __init__(self):
        self._headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
        }
        self.wb_id = list()
        self.user_name = list()
        self.content = list()
        self.create_date = list()
        self.img_list = list()

    @staticmethod
    def get_tid():
        """获取TID参数"""
        url = 'https://passport.weibo.com/visitor/genvisitor?cb=gen_callback&fp={"os":"1","browser":"Chrome89,0,4389,128","fonts":"undefined","screenInfo":"1920*1080*24","plugins":"Portable Document Format::internal-pdf-viewer::Chrome PDF Plugin|::mhjfbmdgcfjbbpaeojofohoefgiehjai::Chrome PDF Viewer|::internal-nacl-plugin::Native Client"}'
        response = requests.get(url).text
        tid = re.findall(r'"tid":"(.*?)"', response)[0]
        return tid

    def get_cookie(self):
        """获取 SUB 和 SUBP """
        tid = self.get_tid()
        while True:
            url = 'https://passport.weibo.com/visitor/visitor?a=incarnate&t={}&w=3&c=95&gc=&cb=cross_domain&from=weibo&_rand={}'.format(
                tid, random.random())
            response = json.loads(re.findall(r'\((.*?)\)', requests.get(url).text)[0])
            if response.get('retcode') == 20000000 and response.get('data').get('sub'):
                cookie = ''
                for key in response.get('data'):
                    cookie += '{}={};'.format(key.upper(), response.get('data').get(key))
                self._headers['cookie'] = cookie.rstrip(';')
                return response.get('data')
            else:
                tid = self.get_tid()

    def search(self):
        start_date = datetime.datetime.strptime('2020-12-11', '%Y-%m-%d')
        end_date = datetime.datetime.now() - datetime.timedelta(days=1)
        while start_date <= end_date:
            timescope1 = '{}-{}'.format(str(start_date).split()[0], start_date.hour)
            start_date += datetime.timedelta(hours=6)
            timescope2 = '{}-{}'.format(str(start_date).split()[0], start_date.hour)
            timescope = 'custom:{}:{}'.format(timescope1, timescope2)
            url = 'https://s.weibo.com/weibo'
            params = {
                'q': '华夏家博会',
                'typeall': '1',
                'suball': '1',
                'timescope': timescope,
                'Refer': 'g',
                'page': '1',
            }
            response = requests.get(url, headers=self._headers, params=params)
            response.encoding = 'utf8'
            if '未找到“华夏家博会”相关结果' in response.text:
                print(timescope, '无数据')
                continue
            html = etree.HTML(response.content)
            wb_info = html.xpath('//div[@action-type="feed_list_item"]')
            wb_id = html.xpath('//div[@action-type="feed_list_item"]/@mid')
            print(timescope, len(wb_info))
            for i in range(len(wb_info)):
                info = wb_info[i]
                user_name = info.xpath('.//a[@class="name"]/text()')
                content = ''.join(info.xpath('.//p[@class="txt"]//text()'))
                img_url = info.xpath('.//div[@node-type="feed_list_media_prev"]//img/@src')
                create_date = info.xpath('.//p[@class="from"]/a[1]/text()')
                if not user_name:
                    continue
                self.wb_id.append(wb_id[i])
                self.user_name.append(user_name[0].strip())
                self.content.append(content)
                self.img_list.append(img_url)
                self.create_date.append(create_date[0].strip())
                # item = {
                #     'ID': wb_id[i],
                #     '用户名': user_name[0].strip(),
                #     '内容': content,
                #     '图片链接': img_url,
                #     '时间': create_date[0].strip(),
                # }
                # print(item)
            time.sleep(3)
        data = pd.DataFrame({
            'ID': self.wb_id,
            '用户名': self.user_name,
            '内容': self.content,
            '图片链接': self.img_list,
            '时间': self.create_date,
        })
        data.to_excel('微博.xlsx', encoding='ANSI', index=False)

    def run(self):
        """启动函数"""
        self.search()


if __name__ == '__main__':
    t = GetFansInfo()
    t.run()
