# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-02-24 17:20:13
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-02-24 17:20:32
import requests
import re


class GetToken(object):
    """获取到游客token"""
    def __init__(self):
        self.get_token_url = 'http://mobile.twitter.com/'
        self.get_token_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
            'Upgrade-Insecure-Requests': '1',
        }

    def get_token(self, proxies_ip):
        proxies = {
            'http': f'http://{proxies_ip}',
            'https': f'http://{proxies_ip}',
        }
        err_count = 0
        while err_count < 5:
            try:
                response = requests.get(url=self.get_token_url, headers=self.get_token_headers, timeout=10,
                                        proxies=proxies)
                result = re.findall(r'document.cookie.*gt=(.*?); Max-Age', response.text)
                return result[0]
            except:
                err_count += 1