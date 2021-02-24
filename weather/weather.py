# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-02-24 17:28:36
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-02-24 17:29:00
# 中国天气网的接口。。。
import requests
from lxml import etree
import pandas as pd
from prettytable import PrettyTable
import os


def get_html(url):
    # 定义头文件
    headers = {'user-agent': 'Mozilla/5.0'}
    # 发起请求
    response = requests.get(url, headers=headers)
    # 修改编码
    response.encoding = 'utf8'
    # 处理成HTML格式
    html = etree.HTML(response.text)
    return html


# 获取城市信息并保存到本地
def get_cityinfo_write(html):
    print('获取城市信息')
    city_info = {}
    # 获取到城市信息
    province_url = html.xpath('//div[@class="lqcontentBoxheader"]//ul//li/a/@href')
    for i in range(len(province_url)):
        # 拼接出每个城市的URL，并获取到对应的HTML
        the_html = get_html('http://www.weather.com.cn' + province_url[i])
        # 解析出城市名称
        city_name = the_html.xpath('//div[@class="conMidtab3"]//tr//td[position()<3]/a/text()')
        # 解析出城市链接
        city_url = the_html.xpath('//div[@class="conMidtab3"]//tr//td[position()<3]/a/@href')
        # 将城市信息存储到city_info中
        for j in range(len(city_name)):
            if j != 0 and city_name[j] == city_name[0]:
                break
            else:
                city_info[city_name[j]] = city_url[j]
    # 给数据设置列名
    data = pd.DataFrame(columns=['city_name', 'city_url'])
    # 填充数据
    data['city_name'] = city_info.keys()
    data['city_url'] = city_info.values()
    # 保存到本地
    data.to_csv(file_path, index=False, encoding='utf8')


if __name__ == '__main__':
    # 实例化输出类
    p = PrettyTable()
    # 接口URL
    url = 'http://www.weather.com.cn/textFC/hb.shtml'
    # 调用获取HTML的方法
    html = get_html(url)
    file_path = '/home/monkey/File/中国天气网城市信息.csv'
    # 判断存放城市信息的数据文件是否存在。如果不存在，则调用get_cityinfo_write方法下载
    if not os.path.exists(file_path):
        get_cityinfo_write(html)
    # 读取城市信息
    data = pd.read_csv(file_path, encoding='utf8')
    # 获取到城市名称
    city_name = data['city_name'].tolist()
    # 获取到城市URL
    city_url = data['city_url'].tolist()
    # 让用户输入需要查询的城市
    name = input('请输入需要查询的城市名称：')
    # 如果名称输入正确，则进行查询
    if name in city_name:
        # 获取到当前城市天气信息的HTML
        city_html = get_html(city_url[city_name.index(name)])
        # 解析出时间
        date = city_html.xpath('//ul[@class="t clearfix"]//li//h1/text()')
        # 解析出天气
        wea = city_html.xpath('//ul[@class="t clearfix"]//li/p[@class="wea"]/text()')
        # 解析出温度列表
        tem_list = ''.join(city_html.xpath('//ul[@class="t clearfix"]//li/p[@class="tem"]//text()')).split('\n')
        # 取出正确的数据
        tem = [tem_list[i] for i in range(len(tem_list)) if i % 2 != 0]
        # 解析出风量
        win = city_html.xpath('//ul[@class="t clearfix"]//li/p[@class="win"]/i/text()')
        print('{}的天气如下'.format(name))
        # 把数据填充到表格中，美化输出
        p.add_column('日期', date)
        p.add_column('天气', wea)
        p.add_column('温度', tem)
        p.add_column('风量', win)
        print(p)
    else:
        print('输入的城市名称有误！')



