# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-02-24 17:42:40
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-02-25 10:49:45
import requests
import execjs
import json


class Music(object):
    """破解网易云音乐JS加密获取数据"""

    def __init__(self):
        self.get_comment_url = 'https://music.163.com/weapi/v1/resource/comments/R_SO_4_{}?csrf_token='

    @staticmethod
    def get_response(method=None, url=None, headers=None, data=None):
        """
        发起请求
        :params: method 请求类型：GET/POST
        :params: url 请求链接
        :params: headers 请求头
        :params: data post请求的表单
        """
        if method is None:
            return '请求参数有误 -- method is None'
        if url is None:
            return '请求链接有误 --- url is None'
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
                              "Chrome/88.0.4324.182 Safari/537.36",
            }
        if method == 'GET':
            response = requests.get(url=url, headers=headers)
        elif method == 'POST':
            response = requests.post(url=url, headers=headers, data=data)
        else:
            return '请求参数有误 -- method undefined'
        response.encoding = 'utf8'
        if response.status_code == 200:
            return response
        else:
            return '请求失败。状态码 %d' % response.status_code

    @staticmethod
    def get_token(music_id):
        """
        根据歌曲ID获取到对应的加密参数
        :param music_id: 需要抓取的歌曲ID
        """
        js_file = open('Music.js', encoding='utf8').read()
        ctx = execjs.compile(js_file, cwd=r'C:\Users\Spider\AppData\Roaming\npm\node_modules')
        token = ctx.call('start', music_id)
        return {
            'params': token['encText'],
            'encSecKey': token['encSecKey']
        }

    def get_comment(self, music_id):
        """
        获取评论数据
        :params music_id 歌曲id
        """
        comment_response = self.get_response(method='POST', url=self.get_comment_url.format(music_id),
                                             data=self.get_token(music_id=music_id)).json()
        # 解析这个json串，即可获取到对应的数据
        print(json.dumps(comment_response))

    def run(self):
        """启动函数"""
        test_music_id = 1366216050
        self.get_comment(music_id=test_music_id)


if __name__ == '__main__':
    m = Music()
    m.run()
