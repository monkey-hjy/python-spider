#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @File    :   bilibili_user.py    
# @Author  :   Monkey
# @DATE    :   2021/5/17 10:04
from gevent import monkey; monkey.patch_all()
import gevent.pool
import requests
import pymysql
import datetime


class BiliUser(object):
    """B站用户"""

    def __init__(self):
        self.pool = gevent.pool.Pool(size=50)
        # 10的7次幂。千万
        self.mid_list = list(range(1, pow(10, 7)))
        # self.mid_list = list(range(1, pow(10, 3)))
        self.conn = pymysql.Connect(host='localhost', user='root', password='root', port=3306, database='demo')
        self.cursor = self.conn.cursor()
        self.proxies = dict()
        self._headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'}
        self.data = []
        self.ips = []
        self.set_proxies()

    def set_proxies(self):
        """设置代理"""
        ip = "需要在这里填写上自己获取代理IP的方法"
        self.proxies = {
            'http': 'http://{}'.format(ip),
            'https': 'http://{}'.format(ip),
        }

    def get_fans_count(self, mid):
        """获取粉丝数量"""
        url = 'https://api.bilibili.com/x/relation/stat?vmid={}&jsonp=jsonp'.format(mid)
        response = requests.get(url, headers=self._headers, proxies=self.proxies).json()
        follower = response['data']['follower']
        following = response['data']['following']
        return follower, following

    def get_user_info(self, mid):
        """获取用户信息"""
        url = 'https://api.bilibili.com/x/space/acc/info?mid={}&jsonp=jsonp'.format(mid)
        err_count = 0
        while err_count < 5:
            try:
                response = requests.get(url, headers=self._headers, proxies=self.proxies, timeout=10).json()
                if response['code'] == 0:
                    nike_name = response['data']['name']
                    sex = response['data']['sex']
                    level = response['data']['level']
                    sign = response['data']['sign']
                    birthday = response['data']['birthday']
                    follower, following = self.get_fans_count(mid)
                    self.data.append([mid, nike_name, sex, level, sign, birthday, follower, following])
                    print('mid:{}\tdata:{}'.format(mid, len(self.data)))
                    if len(self.data) >= 100:
                        data, self.data = self.data, []
                        self.save_data(data)
                    break
                elif response['code'] == -412:
                    raise Exception
                else:
                    print(datetime.datetime.now(), response, mid)
                    break
            except Exception as e:
                err_count += 1
                self.set_proxies()
                # print(err_count, self.proxies, e)

    def save_data(self, data):
        """保存数据"""
        sql = "INSERT INTO bili (mid, nike_name, sex, level, sign, birthday, follower, following) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        self.cursor.executemany(sql, data)
        self.conn.commit()
        print('{}\t保存成功 --- {}'.format(datetime.datetime.now(), len(data)))

    def __del__(self):
        self.conn.close()

    def run(self):
        """启动函数"""
        self.pool.map(self.get_user_info, self.mid_list)
        if self.data:
            self.save_data(self.data)


if __name__ == '__main__':
    t = BiliUser()
    t.run()
