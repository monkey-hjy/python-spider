# -*- coding: utf-8 -*-
# Author:   玛卡巴卡
# Date:     2021/4/20 10:34
import datetime
import logging
import re
import time
from multiprocessing.dummy import Pool as ThreadPool
import requests
import pandas as pd
import random
import os
requests.packages.urllib3.disable_warnings()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
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


class WeiBo(object):
    """
    按照固定的关键词搜索
    采集得到的所有文章和评论信息
    """

    def __init__(self):
        self.get_wb_url = 'https://m.weibo.cn/api/container/getIndex'
        self.comment_url = 'https://m.weibo.cn/comments/hotflow'
        self._headers = {'user-agent': ''}
        self.wb_info_list = dict()
        self.content_id = list()
        self.content = list()
        self.comment_id = list()
        self.comment = list()
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s %(filename)s [line:%(lineno)d] %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename='f:/PDemo/spider_log/{}-{}.log'.format(__file__.split('/')[-1].split('.')[0], str(datetime.datetime.now()).split(" ")[0]),
                            filemode='a')

    def get_response(self, url, params=None, cookie=None):
        """发起请求"""
        err_count = 0
        while err_count < 5:
            try:
                time.sleep(1)
                if cookie is not None:
                    self._headers['cookie'] = cookie
                else:
                    self._headers = {'user-agent': random.choice(USER_AGENTS)}
                response = requests.get(url, params=params, headers=self._headers)
                if response.status_code == 200:
                    return response
                else:
                    err_count += 1
                    time.sleep(30)
            except:
                err_count += 1
        return None

    def get_wb_id(self, keyword, page):
        """获取微博ID"""
        wb_id_list = []
        params = {
            'containerid': '100103type=1&q={}'.format(keyword),
            'page_type': 'searchall',
            'page': page,
        }
        response = self.get_response(url=self.get_wb_url, params=params)
        if response is None:
            logging.error('- 关键词：{}，页码：{}\t出错'.format(keyword, page))
            return
        response = response.json()['data']['cards']
        for info in response:
            try:
                try:
                    self.wb_info_list[info['mblog']['id']] = info['mblog']['comments_count']
                    wb_id_list.append([info['mblog']['id'], info['mblog']['comments_count']])
                except:
                    self.wb_info_list[info['card_group'][0]['mblog']['id']] = info['card_group'][0]['mblog'][
                        'comments_count']
                    wb_id_list.append([info['card_group'][0]['mblog']['id'], info['card_group'][0]['mblog']['comments_count']])
            except Exception as e:
                pass
        logging.info('{}\t{}\t{}'.format(keyword, page, len(wb_id_list)))
        if wb_id_list:
            return True
        else:
            return False

    def get_wb_content(self, id):
        """获取微博原文"""
        url = 'https://m.weibo.cn/statuses/extend?id={}'.format(id)
        response = self.get_response(url=url)
        if response is None:
            return
        try:
            content = re.sub('<.*?>', '', response.json()['data']['longTextContent'])
            self.content_id.append(id)
            self.content.append(content)
            logging.info('- {}\t{}'.format(id, len(content)))
        except Exception as e:
            logging.error('- {}\t{}'.format(e, id))

    def get_wb_comment(self, wb_id):
        """获取微博评论"""
        max_id = 0
        max_id_type = 0
        while True:
            time.sleep(2)
            params = {
                'id': wb_id,
                'mid': wb_id,
                'max_id': max_id,
                'max_id_type': max_id_type,
            }
            err_count = 0
            while err_count < 4:
                response = self.get_response(url=self.comment_url, params=params, cookie='用户登录m.weibo.cn的cookie')
                if response is None:
                    logging.error('{}出错'.format(wb_id))
                    return
                try:
                    response.json()
                except:
                    logging.error('转JSON失败 --- {}'.format(response.text))
                    return None
                if response.json()['ok']:
                    try:
                        response = response.json()['data']
                        logging.info('- {}\t{}\t{}'.format(wb_id, max_id, len(response['data'])))
                        for info in response['data']:
                            self.comment_id.append(wb_id)
                            self.comment.append(re.sub('<.*?>', '', info['text']))
                        # 获取到下一页的ID，当作下次的参数使用
                        next_max_id = response['max_id']
                        max_id_type = response['max_id_type']
                        if next_max_id == 0:
                            return
                        logging.info('- 下一页{}'.format(next_max_id))
                        max_id = next_max_id
                        time.sleep(1)
                        break
                    except Exception as e:
                        err_count += 1
                        time.sleep(5)
                        logging.error('- {}\t{}\t{}'.format(wb_id, err_count, e))
                        if err_count == 4:
                            time.sleep(30)
                            return
                else:
                    logging.error('- {}\t{}'.format(response.json(), params))
                    return

    def run(self):
        """启动函数"""
        keyword_list = ['在这里放需要搜索的关键词']
        for keyword in keyword_list:
            self.__init__()
            logging.info('=== {} ==='.format(keyword))
            flag = True
            page = 1
            while flag:
                the_page_wb_id = self.get_wb_id(keyword=keyword, page=page)
                if the_page_wb_id:
                    page += 1
                else:
                    break
            logging.info(len(self.wb_info_list))
            pool = ThreadPool(20)
            pool.map(self.get_wb_content, list(self.wb_info_list.keys()))
            for key in self.wb_info_list.keys():
                if self.wb_info_list[key]:
                    self.get_wb_comment(wb_id=key)

            content_data = pd.DataFrame({
                '微博ID': self.content_id,
                '微博正文': self.content
            })

            comment_data = pd.DataFrame({
                '微博ID': self.comment_id,
                '评论': self.comment
            })

            """
            可以在此对数据进行持久化保存
            """


if __name__ == '__main__':
    t = WeiBo()
    t.run()
