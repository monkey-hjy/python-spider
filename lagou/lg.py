from gevent import monkey; monkey.patch_all()
import gevent.pool
import json
import random
import re

from lxml import etree
import execjs
import requests
from sns_spider.config.settings import USER_AGENTS
import pymongo


class LG(object):
    """拉钩 js逆向"""

    def __init__(self):
        self.client = pymongo.MongoClient(host='localhost', port=27017)
        self.mongo_col = self.client['demo']['lagou']
        self.js_file = open('lg.js', encoding='utf8').read()
        self._headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'referer': 'https://www.lagou.com/jobs/list_java/p-city_3?px=default',
        }
        self.token = ''
        self.proxies = dict()
        self.set_proxies()
        self.get_token()
        self.city_info = dict()

    def set_proxies(self):
        """设置代理"""
        url = 'http://18037721786.v4.dailiyun.com/query.txt?key=NP1E8E143F&word=&count=1&rand=true&ltime=0&norepeat=false&detail=false'
        ip = requests.get(url).text.strip()
        self.proxies = {
            'http': 'http://{}'.format(ip),
            'https': 'http://{}'.format(ip),
        }

    def get_response(self, url, params=None, data=None, method='GET'):
        while True:
            try:
                if method == 'GET':
                    response = requests.get(url, params=params, headers=self._headers, proxies=self.proxies)
                else:
                    response = requests.post(url, params=params, data=data, headers=self._headers, proxies=self.proxies)
                response.encoding = response.apparent_encoding
                return response
            except:
                self.set_proxies()
                self.get_token()

    def get_token(self):
        """获取到游客cookie"""
        url = 'https://www.lagou.com/gongsi/allCity.html'
        while True:
            headers = {'user-agent': random.choice(USER_AGENTS)}
            try:
                response = requests.get(url, headers=headers, allow_redirects=False, proxies=self.proxies, timeout=10)
                response.encoding = response.apparent_encoding
                user_trace_token = re.findall(r'user_trace_token=(.*?);', response.headers['Set-Cookie'])[0]
                x_http_token = re.findall(r'X_HTTP_TOKEN=(.*?);', response.headers['Set-Cookie'])[0]
                href = response.headers['Location']
                ctx = execjs.compile(self.js_file, cwd='/opt/homebrew/Cellar/node/16.3.0/bin/')
                self.token = ctx.call('window.gt.prototype.a',
                                      json.dumps({"href": href, "search": href.split('check.html')[1]}))
                self._headers['cookie'] = 'user_trace_token={};X_HTTP_TOKEN={};__lg_stoken__={}'.format(
                    user_trace_token, x_http_token, self.token)
                return
            except Exception as e:
                print('获取token失败\tproxies:{}\te:{}'.format(self.proxies, e))
                self.set_proxies()

    def get_city_info(self):
        """获取城市信息"""
        url = 'https://www.lagou.com/jobs/allCity.html'
        html = etree.HTML(self.get_response(url).text)
        city_url = html.xpath('//ul[@class="city_list"]/li/a/@href')
        city_name = html.xpath('//ul[@class="city_list"]/li/a/text()')
        self.city_info = {city_name[i]: city_url[i] for i in range(len(city_url))}

    def get_job_info(self, input_item):
        """获取职位信息"""
        url = 'https://www.lagou.com/jobs/positionAjax.json'
        params = {
            "px": "default",
            "city": input_item['city_name'],
            "district": input_item['district'],
            "needAddtionalResult": "false",
        }
        sid = ''
        page = 1
        while True:
            data = {
                "first": "true",
                "pn": page,
                "kd": input_item['keyword'],
                "sid": sid,
            }
            job_info = self.get_response(url, params=params, data=data, method='POST').json()
            if 'success' in job_info:
                sid = job_info['content']['showId']
                job_info = job_info['content']['positionResult']['result']
                if not job_info or page == 30:
                    break
                self.parse_info(job_info, input_item)
                print('{}\t页码：{}\t数据量：{}'.format(input_item, page, len(job_info)))
            page += 1

    def parse_info(self, job_info, input_item):
        """解析内容"""
        items = list()
        for info in job_info:
            item = {
                '_id': info['positionId'],
                'job_name': info['positionName'],
                'job_url': 'https://www.lagou.com/jobs/{}.html'.format(info['positionId']),
                'company_name': info['companyFullName'],
                'company_size': info['companySize'],
                'industry_field': info['industryField'],
                'finance_stage': info['financeStage'],
                'company_label': '，'.join(info['companyLabelList']).rstrip('，'),
                'skill_label': '，'.join(info['skillLables']).rstrip('，'),
                'position_label': '，'.join(info['positionLables']).rstrip('，'),
                'create_time': info['createTime'],
                'city': info['city'],
                'district': info['district'],
                'salary': info['salary'],
                'work_year': info['workYear'],
                'job_nature': info['jobNature'],
                'education': info['education'],
                'position_advantage': info['positionAdvantage'],
                'position_detail': info['positionDetail'],
                'position_address': info['positionAddress']
            }
            items.append(item)
        try:
            self.mongo_col.insert_many(items)
            # print('{}\t插入成功。本次插入{}条'.format(input_item, len(items)))
        except:
            for item in items:
                try:
                    self.mongo_col.insert_one(item)
                except:
                    pass

    def run(self):
        """启动函数"""
        self.get_city_info()
        # print(self.city_info)
        # for city_name, city_url in self.city_info.items():
        for city_name in ['郑州', '北京', '上海', '广州', '深圳']:
            city_url = self.city_info[city_name]
            if '-zhaopin' not in city_url:
                city_url = city_url.rstrip('/') + '-zhaopin/'
            response = self.get_response(url=city_url, method='GET')
            html = etree.HTML(response.text)
            district_name = html.xpath('//div[@data-type="district"]/a[position()>1]/text()')
            item = [{'city_name': city_name, 'district': name, 'keyword': 'python'} for name in district_name]
            print(item)
            pool = gevent.pool.Pool(size=1)
            pool.map(self.get_job_info, item)


if __name__ == '__main__':
    t = LG()
    t.run()

