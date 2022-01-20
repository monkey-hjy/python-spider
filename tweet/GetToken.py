# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-02-24 17:20:13
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-02-24 17:20:32
import requests


class GetToken(object):
    """获取到游客token"""
    def __init__(self):
        self.get_token_url = 'https://api.twitter.com/1.1/guest/activate.json'
        self.get_token_headers = {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        }

    def get_token(self, proxies_ip):
        proxies = {
            'http': 'http://{}'.format(proxies_ip),
            'https': 'http://{}'.format(proxies_ip),
        }
        err_count = 0
        while err_count < 5:
            try:
                response = requests.request(url=self.get_token_url, method="POST", headers=self.get_token_headers,
                                            timeout=15)
                response.close()
                return response.json().get('guest_token')
            except Exception as e:
                print(e)
                err_count += 1
