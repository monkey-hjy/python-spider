#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# @File    :   dzdp_svg.py    
# @Author  :   Monkey
# @DATE    :   2021/5/13 下午4:54
import re
import requests


class DZDP(object):
    """大众点评"""

    def __init__(self):
        self.css_url = 'https://s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/80da73cea991b1dac8e6c3eb8cfe7461.css'
        self.svg_url = 'https://s3plus.meituan.net/v1/mss_0a06a471f9514fc79c981b5466f56b91/svgtextcss/20609a5f67dfd9a34fd762ac63e59960.svg'
        self.css_text = requests.get(self.css_url).text
        self.svg_info = {int(info.split('">')[0]): info.split('">')[1] for info in re.findall(r'y="(.*?)</text>', requests.get(self.svg_url).text)}

    def get_txt(self, code):
        """获取到编码对应的文字"""
        try:
            patt = '%s{background:(.*?);' % code
            index = re.findall(patt, self.css_text)[0].replace('px', '').replace('-', '').split(' ')
            index_x, index_y = int(index[0][:-2]), int(index[1][:-2])
            for key in self.svg_info:
                if key >= index_y:
                    return self.svg_info[key][index_x // 14]
        except:
            return code


if __name__ == '__main__':
    t = DZDP()
    print(t.get_txt(code='swnbb'))



