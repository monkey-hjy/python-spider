# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-04-22 11:32:21
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-04-22 16:57:22
import json

import requests
import random
import re


class GetFansInfo(object):
    """获取某个账号粉丝的信息"""

    def __init__(self):
        # 参数1：用户ID。
        # 参数2：初始下标，下一页的下标会在本次请求返回
        self.get_fans_url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{}&since_id={}"
        # 参数1：用户ID
        self.get_info_url = "https://weibo.com/p/100505{}/info?mod=pedit_more"
        self._headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
        }

    def get_response(self, url):
        """解析到对应URL的response"""
        response = requests.get(url, headers=self._headers)
        if response.status_code == 200:
            response.encoding = response.apparent_encoding
            return response
        else:
            return None

    def get_fans_info(self, user_id):
        """获取粉丝的信息"""
        self.get_cookie()
        response = self.get_response(url=self.get_info_url.format(user_id))
        city = re.findall(r'所在地：.*?pt_detail\\">(.*?)<', response.text)[0]
        gender = re.findall(r'性别：.*?pt_detail\\">(.*?)<', response.text)[0]
        reg_date = re.findall(r'注册时间：.*?pt_detail\\">(.*?)<',
                              response.text)[0].replace('\\n', '').replace('\\r', '').strip()
        return city, gender, reg_date

    def get_fans_id(self, user_id, since_id=0):
        """获取到某个用户的粉丝"""
        response = self.get_response(url=self.get_fans_url.format(user_id, since_id))
        if response is None:
            print('哥们。这个用户解析好像有点问题....')
            return
        if response.json()['ok'] == 0:
            print('哥们。这个用户解析好像有点问题....')
            return
        fans_info_list = response.json()['data']['cards'][-1]['card_group']
        for info in fans_info_list:
            city, gender, reg_date = self.get_fans_info(user_id=info['user']['id'])
            item = {
                "the_fans_id": info['user']['id'],
                "screen_name": info['user']['screen_name'],
                "followers_count": info['user']['followers_count'],
                "follow_count": info['user']['follow_count'],
                "gender": gender,
                "city": city,
                "reg_date": reg_date
            }
            print(item)

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

    def run(self):
        """启动函数"""
        # emm 这里用鹿晗的ID作为测试。无他。俺只知道这一个明星。。。
        user_id = '1537790411'
        self.get_fans_id(user_id=user_id)


if __name__ == '__main__':
    t = GetFansInfo()
    t.run()
