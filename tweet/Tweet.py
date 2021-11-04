# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-02-24 17:18:02
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-02-24 17:23:17
from datetime import datetime
import requests
from GetToken import GetToken
import random
from prettytable import PrettyTable

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


class SearchTweet(GetToken):
    """
    根据关键词搜索推文或者用户
    使用游客token进行抓取数据，没有次数限制
    但是需要境外ip。。。
    """

    def __init__(self):
        super().__init__()
        self.start = datetime.now()
        # 定义请求头。需要按照下面的代码去获取游客token
        self.headers = {
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs'
                             '%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'user-agent': random.choice(USER_AGENT),
            'x-guest-token': self.get_token(proxies_ip='127.0.0.1:10809'),
        }
        # 获取数据的接口
        self.url = 'https://twitter.com/i/api/2/search/adaptive.json'

    def start_requests(self, search_key, search_type='tweet'):
        """
        开始搜索
        :param search_key: 搜素关键词
        :param search_type: 搜索类别。tweet/推文。   account/用户
        :return:
        """
        params = {
            "q": search_key,
            "count": 20,
        }
        if search_type == 'account':
            params['result_filter'] = 'user'
        response = requests.get(url=self.url, headers=self.headers, params=params, timeout=10)
        if response.status_code != 200:
            return f'{search_key} ERR  ===  {response}'
        tweets = response.json().get('globalObjects').get('tweets')
        users = response.json().get('globalObjects').get('users')
        if not len(tweets) and not len(users):
            return f'{search_key}未抓到数据'
        p = PrettyTable()
        if search_type == 'tweet':
            tweet_id = []
            create_time = []
            full_text = []
            user_name = []
            screen_name = []
            for key in tweets:
                tweet_id.append(key)
                create_time.append(tweets.get(key).get('created_at'))
                full_text.append(tweets.get(key).get('text'))
                user_id = tweets.get(key).get('user_id_str')
                user_name.append(users.get(user_id).get('name'))
                screen_name.append(users.get(user_id).get('screen_name'))
            p.add_column(fieldname='推文ID', column=tweet_id)
            p.add_column(fieldname='发文时间', column=create_time)
            p.add_column(fieldname='内容', column=full_text)
            p.add_column(fieldname='用户名', column=user_name)
            p.add_column(fieldname='账号', column=screen_name)
        else:
            user_name = []
            screen_name = []
            description = []
            for key in users:
                user_name.append(users.get(key).get('name'))
                screen_name.append(users.get(key).get('screen_name'))
                description.append(users.get(key).get('description'))
            p.add_column(fieldname='用户名', column=user_name)
            p.add_column(fieldname='账号', column=screen_name)
            p.add_column(fieldname='简介', column=description)
        return p

    def run(self):
        search_key = ['葫芦娃', '奥特曼']
        for key in search_key:
            result = self.start_requests(search_key=key, search_type='account')
            print(result)

    def __del__(self):
        end = datetime.now()
        print(f'开始：{self.start}，结束：{end}\n用时：{end-self.start}')


if __name__ == '__main__':
    t = SearchTweet()
    t.run()
