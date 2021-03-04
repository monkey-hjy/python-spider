# -*- coding: utf-8 -*-
# @Author: monkey-hjy
# @Date:   2021-03-04 11:18:58
# @Last Modified by:   monkey-hjy
# @Last Modified time: 2021-03-04 11:19:17
# 天天基金网数据抓取

import requests
import time
import re
import json
import pandas as pd
import random

file_path = '基金查询.xlsx'
fund_codes = ['001606', '000924', '005962', '004997', '006751']
start_date = '2019-01-01'
end_date = '2021-10-30'
url = 'http://api.fund.eastmoney.com/f10/lsjz'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
    'Referer': 'http://fundf10.eastmoney.com/',
}
result = dict()
result_fsrq = []
for fund_code in fund_codes:
    params = {
        "callback": f"jQuery183{''.join([str(random.randrange(0, 10)) for _ in range(17)])}_{int(time.time() * 1000)}",
        "fundCode": fund_code,
        "pageIndex": "1",
        "pageSize": "100000",
        "startDate": start_date,
        "endDate": end_date,
        "_": str(int(time.time() * 1000)),
    }
    response = json.loads(re.findall(r'\((.*)\)', requests.get(url, headers=headers, params=params).text, re.S)[0])
    # 日期
    FSRQ = []
    # 单位净值
    DWJZ = []
    fund_info = response['Data']['LSJZList']
    for i in range(len(fund_info)):
        # FSRQ.append(datetime.datetime.strptime(fund_info[i]['FSRQ'], '%Y-%m-%d'))
        FSRQ.append(fund_info[i]['FSRQ'])
        DWJZ.append(fund_info[i]['DWJZ'])
    result_fsrq = FSRQ if len(FSRQ) > len(result_fsrq) else result_fsrq
    result[fund_code] = DWJZ
max_len = 0
for key in result:
    max_len = len(result[key]) if len(result[key]) > max_len else max_len
for key in result:
    result[key] += [None] * (max_len - len(result[key]))
result = pd.DataFrame(result)
result.index = result_fsrq
result.to_excel(file_path, encoding='ANSI')
