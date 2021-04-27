# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-04-27 11:35:40
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-04-27 11:36:08
import requests
import hashlib
import time
import random


class YDDict(object):
    """有道翻译"""

    @staticmethod
    def get_data(keyword):
        """获取到其余的加密参数"""
        md = hashlib.md5()
        t = str(int(time.time() * 1000))
        i = t + str(random.randrange(10))
        md.update('fanyideskweb{}{}Tbh5E8=q6U3EXe+&L[4c@'.format(keyword, i).encode('utf8'))
        sign = md.hexdigest()
        return t, i, sign

    def translate(self, keyword='你好', data_from='AUTO', data_to='AUTO'):
        """
        对keyword进行翻译
        params: params_from 文本语言
        params: params_to 翻译成的语言类型
        """
        url = 'https://fanyi.youdao.com/translate?smartresult=dict&smartresult=rule'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
            'Referer': 'https://fanyi.youdao.com/?keyfrom=fanyi-new.logo',
            'Host': 'fanyi.youdao.com',
            'Origin': 'https://fanyi.youdao.com',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
        t, i, sign = self.get_data(keyword)
        data = {
            "i": keyword,
            "from": data_from,
            "to": data_to,
            "smartresult": "dict",
            "client": "fanyideskweb",
            "salt": i,
            "sign": sign,
            "lts": t,
            # 这里bv是对UA加密得到的，所以也写成了定值
            "bv": "62c1eba97402d4ff4eb261254e974c27",
            "doctype": "json",
            "version": "2.1",
            "keyfrom": "fanyi.web",
            "action": "FY_BY_REALTlME",
        }
        response = requests.post(url, headers=headers, data=data)
        # json中包含结果，自己解析一下OK
        print(response.json())


if __name__ == '__main__':
    t = YDDict()
    t.translate(keyword='中国')
