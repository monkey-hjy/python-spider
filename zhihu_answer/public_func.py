# -*- coding: utf-8 -*-
# File: public_func.py
# Date: 2024/1/5 11:03
# Auth: HJY
# Decs:
import ctypes
import os
import random
import time
from datetime import datetime
from hashlib import md5
import redis
import traceback
from urllib.parse import urlparse, parse_qs, urlencode

import pymysql
import requests
import queue
import threading
from requests import utils
from loguru import logger

# h：签名以来的固定数组
h = {
    "zb": [20, 223, 245, 7, 248, 2, 194, 209, 87, 6, 227, 253, 240, 128, 222, 91, 237, 9, 125, 157, 230, 93, 252,
           205, 90, 79, 144, 199, 159, 197, 186, 167, 39, 37, 156, 198, 38, 42, 43, 168, 217, 153, 15, 103, 80, 189,
           71, 191, 97, 84, 247, 95, 36, 69, 14, 35, 12, 171, 28, 114, 178, 148, 86, 182, 32, 83, 158, 109, 22, 255,
           94, 238, 151, 85, 77, 124, 254, 18, 4, 26, 123, 176, 232, 193, 131, 172, 143, 142, 150, 30, 10, 146, 162,
           62, 224, 218, 196, 229, 1, 192, 213, 27, 110, 56, 231, 180, 138, 107, 242, 187, 54, 120, 19, 44, 117,
           228, 215, 203, 53, 239, 251, 127, 81, 11, 133, 96, 204, 132, 41, 115, 73, 55, 249, 147, 102, 48, 122,
           145, 106, 118, 74, 190, 29, 16, 174, 5, 177, 129, 63, 113, 99, 31, 161, 76, 246, 34, 211, 13, 60, 68,
           207, 160, 65, 111, 82, 165, 67, 169, 225, 57, 112, 244, 155, 51, 236, 200, 233, 58, 61, 47, 100, 137,
           185, 64, 17, 70, 234, 163, 219, 108, 170, 166, 59, 149, 52, 105, 24, 212, 78, 173, 45, 0, 116, 226, 119,
           136, 206, 135, 175, 195, 25, 92, 121, 208, 126, 139, 3, 75, 141, 21, 130, 98, 241, 40, 154, 66, 184, 49,
           181, 46, 243, 88, 101, 183, 8, 23, 72, 188, 104, 179, 210, 134, 250, 201, 164, 89, 216, 202, 220, 50,
           221, 152, 140, 33, 235, 214],
    "zk": [1170614578, 1024848638, 1413669199, -343334464, -766094290, -1373058082, -143119608, -297228157,
           1933479194, -971186181, -406453910, 460404854, -547427574, -1891326262, -1679095901, 2119585428,
           -2029270069, 2035090028, -1521520070, -5587175, -77751101, -2094365853, -1243052806, 1579901135,
           1321810770, 456816404, -1391643889, -229302305, 330002838, -788960546, 363569021, -1947871109],
    "zm": [120, 50, 98, 101, 99, 98, 119, 100, 103, 107, 99, 119, 97, 99, 110, 111]
}
# salt: 签名依赖的最终数据
salt = '6fpLRqJO8M/c3jnYxFkUVC4ZIG12SiH=5v0mXDazWBTsuw7QetbKdoPyAl+hN9rgE'
# base_list: 第二次偏移需要使用的固定数组
base_list = [48, 53, 57, 48, 53, 51, 102, 55, 100, 49, 53, 101, 48, 49, 100, 55]


class PublicFunc:

    def __init__(self, log_name='default') -> None:
        self.now_date = datetime.now().strftime('%Y%m%d')
        log_path = '/data/log' if os.path.exists('/data/log') else '/Users/monkey/Documents/log'
        logger.add(os.path.join(log_path, f'{log_name}_{self.now_date}.log'), encoding='utf-8',
                   enqueue=True, retention='10 days')
        self._headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        }

    @staticmethod
    def parse_params(url):
        url = urlparse(url)
        params = {k: v[0] for k, v in parse_qs(url.query).items()}
        return params

    @staticmethod
    def get_proxies():
        return {
            'http': 'xxx',
            'https': 'xxx',
        }

    def get_response(self, url, params=None, data=None, headers=None, method='get', cookies=None):
        err_count = 0
        e_res = None
        while err_count < 5:
            proxies = self.get_proxies()
            proxy_name = proxies.get('http').split('@')[-1].split('.')[1]
            try:
                headers = self._headers if headers is None else headers
                if method == 'get':
                    response = requests.get(url, params=params, timeout=15, headers=headers, proxies=proxies, cookies=cookies)
                elif method == 'post':
                    response = requests.post(url, data=data, timeout=15, headers=headers, cookies=cookies)
                else:
                    return None
                if response.status_code == 200:
                    response.encoding = 'utf8'
                    if '网络不给力，请稍后重试' in response.text and 'paging' not in response.text:
                        raise Exception('网络不给力，请稍后重试')
                    if '安全验证' in response.text and 'paging' not in response.text:
                        raise Exception('安全验证')
                    return response
                if '"code":4041,"name":"NotFoundError","message":"资源不存在"' in response.text:
                    return response
                raise Exception(response.status_code)
            except Exception as e:
                err_count += 1
                e_res = e
        return e_res

    @staticmethod
    def encrypt_md5(md5_str):
        """md5 加密"""
        md5_obj = md5()
        md5_obj.update(md5_str.encode())
        return md5_obj.hexdigest()

    @staticmethod
    def str_to_unicode(translate_str):
        """将str 使用ord 转换成 整型列表"""
        ord_list = list()
        for str_ in translate_str:
            ord_list.append(ord(str_))
        return ord_list

    @staticmethod
    def add_params_to_list(ord_list):
        """
        补全 ord_list 中数据
        首先第一个部分是 随机数 * 127
        第二部分是 0
        第三部分是 ord_list
        上面三部分构成长度为34的数组
        第四部分是 [14,14,14,14,14,14,14,14,14,14,14,14,14,14]
        最终构成长度为48为的数组
        :param ord_list:
        :return:
        """
        params_list = list()
        random_num = int(random.random() * 127)  # 随机值 控制每次签名不同
        params_list.append(random_num)
        params_list.append(0)
        params_list.extend(ord_list)
        params_list.extend([14 for i in range(14)])
        return params_list

    @staticmethod
    def get_head_16(params_list):
        """
        获取 params_list 前16位
        与数组base_list做异或操作：
        base_list=[48,53,57,48,53,51,102,55,100,49,53,101,48,49,100,55]
        :param params_list:
        :return:
        """
        head_16_list = [params_list[index] ^ base_list[index] ^ 42 for index in range(16)]
        return head_16_list

    def js_func_g_x(self, e, t):
        """
        还原js 函数 __g.x
        :param e:
        :param t:
        :return:
        """
        n = list()
        r = len(e) // 16
        # 16步进
        for i in range(0, r):
            a = [0 for i in range(16)]  # 16位列表
            o = e[16 * i: 16 * (i + 1)]
            for c in range(16):
                a[c] = o[c] ^ t[c]
            t = self.js_func_g_r(a)
            n.extend(t)
        return n

    def js_func_g_r(self, e):
        """
        还原js 函数 __g.r
        :param e:
        :return:
        """
        t = [0 for i in range(16)]  # 16位列表
        n = [0 for j in range(36)]  # 36位列表
        n[0] = self.js_func_b(e, 0)
        n[1] = self.js_func_b(e, 4)
        n[2] = self.js_func_b(e, 8)
        n[3] = self.js_func_b(e, 12)
        for r in range(32):
            o = self.js_func_g(n[r + 1] ^ n[r + 2] ^ n[r + 3] ^ h.get('zk')[r])
            n[r + 4] = n[r] ^ o
        self.js_func_i(n[35], t, 0)
        self.js_func_i(n[34], t, 4)
        self.js_func_i(n[33], t, 8)
        self.js_func_i(n[32], t, 12)
        return t

    @staticmethod
    def js_func_b(e, t):
        """
        还原js 函数B
        :param e:
        :param t:
        :return:
        """
        return (255 & e[t]) << 24 | (255 & e[t + 1]) << 16 | (255 & e[t + 2]) << 8 | 255 & e[t + 3]

    def js_func_g(self, e):
        """
        还原js function G
        :param e:
        :return:
        """

        t = [0 for i in range(4)]  # 16位列表
        n = [0 for j in range(4)]  # 36位列表
        self.js_func_i(e, t, 0)  # 调用 js_func_i 设定初始值
        n[0] = h.get('zb')[255 & t[0]]
        n[1] = h.get('zb')[255 & t[1]]
        n[2] = h.get('zb')[255 & t[2]]
        n[3] = h.get('zb')[255 & t[3]]
        r = self.js_func_b(n, 0)
        res = r ^ self.js_func_q(r, 2) ^ self.js_func_q(r, 10) ^ self.js_func_q(r, 18) ^ self.js_func_q(r, 24)
        return res

    def js_func_q(self, e, t):
        """
        还原js function Q
        :param e:
        :param t:
        :return:
        """
        res = (4294967295 & e) << t | self.unsigned_right_shitf(e, 32 - t)
        return res

    def js_func_i(self, e, t, n):
        """
        还原 js func i
        :param e:
        :param t:
        :param n:
        :return:
        """
        t[n] = 255 & self.unsigned_right_shitf(e, 24)
        t[n + 1] = 255 & self.unsigned_right_shitf(e, 16)
        t[n + 2] = 255 & self.unsigned_right_shitf(e, 8)
        t[n + 3] = 255 & e

    def unsigned_right_shitf(self, n, i):
        # 数字小于0，则转为32位无符号uint
        if n < 0:
            n = ctypes.c_uint32(n).value
        # 正常位移位数是为正数，但是为了兼容js之类的，负数就右移变成左移好了
        if i < 0:
            return -self.int_overflow(n << abs(i))
        return self.int_overflow(n >> i)

    @staticmethod
    def int_overflow(val):
        maxint = 2147483647
        if not -maxint - 1 <= val <= maxint:
            val = (val + (maxint + 1)) % (2 * (maxint + 1)) - maxint - 1
        return val

    @staticmethod
    def get_result_value_list(new_48_list):
        """转换数值列表"""
        # 将列表[i:i+3]切片,并饭庄
        result_value_list = list()
        split_list = [new_48_list[i:i + 3] for i in range(0, len(new_48_list), 3)]
        split_list.reverse()
        for i in range(len(split_list)):
            _temp_list = split_list[i]
            _temp_list.reverse()
            _val = i % 4
            if _val == 0:
                temp_value_1 = _temp_list[_val] ^ 58
                temp_value_2 = _temp_list[1] << 8
                temp_value_3 = _temp_list[2] << 16
            elif _val == 1:
                temp_value_1 = _temp_list[0]
                temp_value_2 = (_temp_list[_val] ^ 58) << 8
                temp_value_3 = _temp_list[2] << 16
            elif _val == 2:
                temp_value_1 = _temp_list[0]
                temp_value_2 = _temp_list[1] << 8
                temp_value_3 = (_temp_list[_val] ^ 58) << 16
            else:
                temp_value_1 = _temp_list[0]
                temp_value_2 = _temp_list[1] << 8
                temp_value_3 = _temp_list[2] << 16
            value = temp_value_1 | temp_value_2 | temp_value_3
            result_value_list.append(value)
        return result_value_list

    @staticmethod
    def make_zhihu_sign(result_value_list):
        """通过salt 转换签名字符串"""
        sign_str = ''
        for _value in result_value_list:
            sign_str += salt[_value & 63]
            sign_str += salt[_value >> 6 & 63]
            sign_str += salt[_value >> 12 & 63]
            sign_str += salt[_value >> 18 & 63]
        return sign_str

    def test_case(self, url, d_c0):
        md5_str = '101_3_3.0+' + url + d_c0
        md5_res = self.encrypt_md5(md5_str)
        ord_list = self.str_to_unicode(md5_res)
        params_list = self.add_params_to_list(ord_list)
        head_16_list = self.get_head_16(params_list)
        end_32_list = params_list[16:]
        new_16_list = self.js_func_g_r(head_16_list)
        new_32_list = self.js_func_g_x(end_32_list, new_16_list)
        new_48_list = list()
        new_48_list.extend(new_16_list)
        new_48_list.extend(new_32_list)
        result_value_list = self.get_result_value_list(new_48_list)
        sign_str = self.make_zhihu_sign(result_value_list)
        return sign_str

    def get_cookie_d_c0(self, proxies=None):
        end_sign = self.test_case('/udid', '')
        headers = {
            'x-zse-93': '101_3_3.0',
            'x-api-version': '3.0.91',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'x-zse-96': '2.0_' + end_sign,
            'accept': '*/*',
        }
        d_c0 = None
        err_count = 0
        while err_count <= 10:
            try:
                first_res = requests.post('https://www.zhihu.com/udid', data={}, headers=headers, proxies=proxies,
                                          timeout=60)
                cookie_t = utils.dict_from_cookiejar(first_res.cookies)
                d_c0 = cookie_t.get('d_c0')
                return d_c0
            except Exception as e:
                err_count += 1
                time.sleep(random.randint(1, 10))
                logger.error(f'get_cookie_d_c0 err_count:{err_count}, proxies: {proxies}, e: {e}')
        return d_c0

    def _get_end_sign(self, md5_str):
        # md5_str = '101_3_3.0+'+url+d_c0
        md5_res = self.encrypt_md5(md5_str)
        ord_list = self.str_to_unicode(md5_res)
        params_list = self.add_params_to_list(ord_list)
        head_16_list = self.get_head_16(params_list)
        end_32_list = params_list[16:]
        new_16_list = self.js_func_g_r(head_16_list)
        new_32_list = self.js_func_g_x(end_32_list, new_16_list)
        new_48_list = list()
        new_48_list.extend(new_16_list)
        new_48_list.extend(new_32_list)
        result_value_list = self.get_result_value_list(new_48_list)
        sign_str = self.make_zhihu_sign(result_value_list)
        return sign_str

    @staticmethod
    def get_headers(d_c0, end_sign):
        headers = {
            "cookie": f"d_c0={d_c0};",
            'x-zse-93': '101_3_3.0',
            'x-api-version': '3.0.91',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
            'x-zse-96': '2.0_' + end_sign,
            'accept': '*/*',
            # 'referer': 'https://www.zhihu.com/search?q=%E6%B5%B7%E8%B4%BC%E7%8E%8B%E7%B4%A2%E9%9A%86%E8%BA%AB%E4%B8%96%E6%8F%AD%E7%A7%98&type=zvideo&utm_content=search_hot',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'zh-CN,zh;q=0.9',
        }
        return headers

    def run(self, keyword):
        url = f'https://www.zhihu.com/api/v4/search_v3?gk_version=gz-gaokao&t=general&q={keyword}&correction=1&offset=0&limit=20&filter_fields=&lc_idx=0&show_all_topics=0&search_source=Filter&vertical=answer&time_interval=a_week'
        url_params = t.parse_params(url)
        params = url_params
        offset = url_params.get('offset', 0)
        req_url = 'https://www.zhihu.com/api/v4/search_v3'
        reply_num = 0
        while True:
            d_c0 = t.get_cookie_d_c0()
            end_sign = t._get_end_sign(f'101_3_3.0+/api/v4/search_v3?{urlencode(params)}+{d_c0}')
            headers = t.get_headers(d_c0, end_sign)
            response = t.get_response(url=req_url, headers=headers, params=params)
            if isinstance(response, requests.Response):
                break
            reply_num += 1
            logger.error(
                f'search keyword reply {reply_num} times! keyword: {keyword}, offset: {offset}, e: {response}')
            if reply_num > 50:
                return
        response = response.json()
        return response


if __name__ == '__main__':
    t = PublicFunc()
    keyword = '海贼王'
    t.run(keyword)

