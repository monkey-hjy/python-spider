# -*- coding: utf-8 -*-
# Author:   玛卡巴卡
# Date:     2021/4/19 17:10

import requests
import time


class WBComment(object):
    """抓取微博全量评论。但是需要登录"""

    def __init__(self):
        self.comment_url = 'https://m.weibo.cn/comments/hotflow'
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
            'cookie': '用户登录后的cookie',
        }

    def get_response(self, url, params=None):
        """发起请求"""
        response = requests.get(url=url, headers=self._headers, params=params)
        if response.status_code == 200:
            return response
        else:
            print('出错。返回的状态码是：{}'.format(response.status_code))
            return None

    def start(self, wb_id):
        """启动函数，接受微博ID参数"""
        # 初始页码的ID。下一页的ID会存放在返回的数据中
        max_id = 0
        while True:
            params = {
                'id': wb_id,
                'mid': wb_id,
                'max_id': max_id,
                'max_id_type': 1,
            }
            response = self.get_response(url=self.comment_url, params=params)
            if response is None:
                print('{}出错'.format(weibo_id))
                return
            response = response.json()['data']
            print(max_id, len(response['data']), response['data'][0]['text'])
            # 获取到下一页的ID，当作下次的参数使用
            max_id = response['max_id']
            time.sleep(1)

