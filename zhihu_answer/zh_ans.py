# -*- coding: utf-8 -*-
# User : monkey  
# Date : 2021/9/15 4:24 下午
# Name : zh_ans.py
import re

import requests
import pymysql
import emoji


class Zhihu(object):
    """知乎问答答案抓取"""

    def __init__(self):
        self.conn = pymysql.connect(user='root', password='root', host='localhost', port=3306, database='demo', charset='utf8mb4')
        self.cursor = self.conn.cursor()
        self._headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'}

    def __del__(self):
        self.conn.close()

    def run(self, ans_id):
        url = 'https://www.zhihu.com/api/v4/questions/{}/answers'.format(ans_id)
        for page in range(10):
            params = {
                'limit': 20,
                'offset': page * 20,
                'platform': 'desktop',
                'sort_by': 'default',
                'include': 'data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,attachment,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,is_labeled,paid_info,paid_info_content,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp,is_recognized;data[*].mark_infos[*].url;data[*].author.follower_count,vip_info,badge[*].topics;data[*].settings.table_of_content.enabled'
            }

            response = requests.get(url, headers=self._headers, params=params).json()['data']
            for info in response:
                answers_id = info['id']
                account_name = info['author']['name']
                headline = info['author']['headline']
                follower_count = info['author']['follower_count']
                gender = info['author']['gender']
                user_type = info['author']['user_type']
                home_url = 'https://www.zhihu.com/people/{}'.format(info['author']['url_token'])
                comment_count = info['comment_count']
                content = emoji.demojize(re.sub('<.*?>', '', info['content']))
                created_time = info['created_time']
                question_id = info['question']['id']
                question_title = info['question']['title']
                answers_url = 'https://www.zhihu.com/question/{}/answer/{}'.format(question_id, answers_id)
                voteup_count = info['voteup_count']
                sql = "INSERT INTO zhihu_answers (" \
                      "answers_id, account_name, headline, follower_count, gender, user_type, home_url, comment_count, content," \
                      "created_time, question_id, question_title, answers_url, voteup_count) values (" \
                      "'{}','{}','{}',{},{},'{}','{}',{},'{}',{},'{}','{}','{}',{})".format(
                    answers_id, account_name, headline, follower_count, gender, user_type, home_url, comment_count, content,
                    created_time, question_id, question_title, answers_url, voteup_count)
                self.cursor.execute(sql)
                self.conn.commit()
                print(page, account_name, answers_url)


if __name__ == '__main__':
    s = Zhihu()
    s.run('26402088')

