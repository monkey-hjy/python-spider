# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-04-22 11:32:21
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-04-22 16:57:22
from gevent import monkey; monkey.patch_all()
import gevent.pool
import json
import requests
import random
import re
import pymongo
import datetime
import redis


class GetFansInfo(object):
    """获取某个账号粉丝的信息"""

    def __init__(self):
        self.mongo_conf = pymongo.MongoClient(host='127.0.0.1', port=27017)
        self.mongo_db = self.mongo_conf['data']['weibo']
        self.redis_conf = redis.StrictRedis()
        # 参数1：用户ID。
        # 参数2：初始下标，下一页的下标会在本次请求返回
        self.get_fans_url = "https://m.weibo.cn/api/container/getIndex?containerid=231051_-_fans_-_{}&since_id={}"
        # 参数1：用户ID
        self.get_info_url = "https://weibo.com/p/100505{}/info?mod=pedit_more"
        self._headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36",
        }
        self.get_cookie()
        self.err_count = 0

    def __del__(self):
        self.redis_conf.close()
        self.mongo_conf.close()

    def get_response(self, url):
        """解析到对应URL的response"""
        err_count = 0
        while err_count < 5:
            try:
                response = requests.get(url, headers=self._headers)
                if response.status_code == 200:
                    response.encoding = 'utf8'
                    if '<title>Sina Visitor System</title>' in response.text:
                        raise Exception
                    return response
                else:
                    raise Exception
            except:
                err_count += 1
                self.get_cookie()
        return None

    def get_fans_info(self, user_info):
        """获取粉丝的信息"""
        user_info = user_info['user']
        response = self.get_response(url=self.get_info_url.format(user_info['id']))
        if response is None:
            print('出错 === {}'.format(user_info))
            return
        city = re.findall(r'所在地：.*?pt_detail\\">(.*?)<', response.text)
        city = city[0] if city else '其他'
        gender = re.findall(r'性别：.*?pt_detail\\">(.*?)<', response.text)
        gender = gender[0] if gender else '未知'
        reg_date = re.findall(r'注册时间：.*?pt_detail\\">(.*?)<', response.text)
        reg_date = reg_date[0].replace('\\n', '').replace('\\r', '').strip() if reg_date else '未知'
        item = {
            "the_fans_id": user_info['id'],
            "screen_name": user_info['screen_name'],
            "followers_count": user_info['followers_count'],
            "follow_count": user_info['follow_count'],
            "gender": gender,
            "city": city,
            "reg_date": reg_date
        }
        self.mongo_db.insert_one(item)

    def get_fans_id(self, user_id, since_id=0):
        """获取到某个用户的粉丝"""
        print(datetime.datetime.now(), user_id, since_id)
        if since_id >= 4999:
            return
        response = self.get_response(url=self.get_fans_url.format(user_id, since_id))
        if response is None:
            print('哥们。这个用户解析好像有点问题....\t{} is None'.format(user_id))
            return
        elif response.json()['ok'] == 0:
            print('哥们。这个用户解析好像有点问题....\t{}\t{}\t{}'.format(self.err_count, user_id, response.json()))
            if self.err_count < 10:
                self.err_count += 1
                self.get_fans_id(user_id, since_id)
        else:
            pip = self.redis_conf.pipeline()
            [pip.sadd('new_wb_user', info['user']['id']) for info in response.json()['data']['cards'][-1]['card_group']]
            pip.execute()
            try:
                next_since_id = response.json()['data']['cardlistInfo']['since_id']
                if next_since_id:
                    self.err_count = 0
                    self.get_fans_id(user_id=user_id, since_id=next_since_id)
            except Exception as e:
                print(e, user_id, since_id, response.json())

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
        user_ids = list(set([line.replace('\n', '') for line in open('大V.txt', encoding='utf8').readlines()]))
        exist = [line.replace('\n', '') for line in open('exist.txt', encoding='utf8').readlines()]
        # # # 1、高并发跑。会有IP封禁问题。自行选择。。。
        # pool = gevent.pool.Pool(50)
        # pool.map(self.get_fans_id, user_ids)

        # 2、单线程跑。不会封禁IP。但是速度不是很快。
        for user_id in user_ids:
            if user_id in exist:
                continue
            self.get_fans_id(user_id)
            with open('exist.txt', encoding='utf8', mode='a') as f:
                f.write('{}\n'.format(user_id))


if __name__ == '__main__':
    t = GetFansInfo()
    t.run()
"""
小时候
总是盼望着
盼望着有自己的零花钱
盼望着有一辆属于自己的自行车
盼望着玩到天黑不回家
盼望着妈妈不再唠叨我

长大了
总是想着
想着可以不用每天算计着花钱
想着可以真正的散散步
想着可以在家里休息一整天
想着可以每天陪着妈妈说话

听说
20岁的人 怀念童年
40岁的人 怀念青春
60岁的人 怀念壮年
只有那些孩子会缠着人问
妈妈
我什么时候长大呀
    ---- H 2021/4/26 上海
    ---- 结尾摘自 《儿时的夏日》 热评 
"""
