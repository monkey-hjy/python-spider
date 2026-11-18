# -*- coding: utf-8 -*-
import base64
import hashlib
import json
import re
import time

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

API = 'https://apibi.cc/api'
USER_AGENT = 'Mozilla/5.0 (Linux; Android 10; Pixel 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'

_code = hashlib.md5(b'book@token.html').hexdigest()
IV, KEY = _code[:16].encode(), _code[16:].encode()


def token(params):
    data = json.dumps(params, separators=(',', ':')).encode()
    cipher = AES.new(KEY, AES.MODE_CBC, IV)
    return base64.b64encode(cipher.encrypt(pad(data, 16))).decode()


def api_get(path, params):
    for _ in range(3):
        response = requests.get(API + '/' + path, params=params,
                                headers={'user-agent': USER_AGENT}, timeout=20)
        if response.status_code == 200 and response.text.strip():
            return response.json()
        time.sleep(1.2)
    raise RuntimeError('{} 请求失败：HTTP {}'.format(path, response.status_code))


class SpiderBook(object):

    def __init__(self):
        self.book_name = input('输入书名：').strip()
        self.books = []

    def search_book(self):
        data = api_get('search', {'q': self.book_name})
        self.books = data.get('data') or []
        if not self.books:
            print('没有搜到：{}'.format(self.book_name))
            return
        for i, book in enumerate(self.books):
            print('编号{}信息：作者-{}\t书名-{}'.format(i, book.get('author', ''), book.get('title', '')))
        need_id = int(input('输入需要的书籍编号：'))
        self.download_book(self.books[need_id])

    def download_book(self, book):
        book_id = book['id']
        chapters = api_get('booklist', {'token': token({'id': book_id})})['list']
        filename = '{}.txt'.format(re.sub(r'[\\/:*?"<>|]', '_', book['title']))
        for i in range(len(chapters)):
            chapter = api_get('chapter', {'token': token({'id': book_id, 'chapterid': i + 1})})
            print('{}/{}\tname:{}\t字数:{}'.format(i + 1, len(chapters), chapter['chaptername'], len(chapter['txt'])))
            with open(filename, 'a', encoding='utf8') as f:
                f.write(chapter['chaptername'] + '\n')
                f.write(chapter['txt'] + '\n\n')
        print('下载完成：{}'.format(filename))

    def run(self):
        self.search_book()


if __name__ == '__main__':
    SpiderBook().run()
