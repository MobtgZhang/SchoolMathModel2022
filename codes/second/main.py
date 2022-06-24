# !/usr/bin/nev python
# -*-coding:utf8-*-
import random
from datetime import datetime
import json
import re
import os
from requests_html import HTMLSession
import pandas as pd
import urllib3                      # 解除警告
urllib3.disable_warnings()
session = HTMLSession()
from fake_useragent import UserAgent

class WBSpider(object):
    def __init__(self,weibo_id,cookie):
        self.weibo_id = weibo_id
        self.cookie = cookie
        self.all_data_dict = []
    def start(self):
        page_num = 1
        

        ua = UserAgent(use_cache_server=False)
        
        headers ={
            "referer": "https://m.weibo.cn/status/Kk9Ft0FIg?jumpfrom=weibocom",
            'cookie': self.cookie,
            'user-agent': ua.random #'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36'
        }
        # 构造起始地址
        start_url = f'https://m.weibo.cn/comments/hotflow?id={self.weibo_id}&mid={self.weibo_id}&max_id_type=0'
        """
                2.发送请求，获取响应：解析起始的url地址
                :return:
                """
        prox = ''
        response = session.get(start_url, proxies={'http': prox, 'https': prox}, headers=headers, verify=False)
        response = response.json()
        """提取翻页的max_id"""
        max_id = response['data']['max_id']
        """提取翻页的max_id_type"""
        max_id_type = response['data']['max_id_type']

        """构造GET请求参数"""
        data = {
            'id': weibo_id,
            'mid': weibo_id,
            'max_id': max_id,
            'max_id_type': max_id_type
        }
        """解析评论内容"""
        self.parse_response_data(response, page_num)
        page_num+=1
        headers ={
            "referer": "https://m.weibo.cn/status/Kk9Ft0FIg?jumpfrom=weibocom",
            'cookie': self.cookie,
            'user-agent': ua.random #'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36'
        }
        """参数传递，方法回调"""
        self.parse_page_func(data, weibo_id, headers, page_num)

    def parse_page_func(self, data, weibo_id, headers, page_num):
        """
        :return:
        """

        start_url = 'https://m.weibo.cn/comments/hotflow?'
        prox = ''
        response = session.get(start_url, proxies={'http': prox, 'https': prox}, headers=headers, params=data, verify=False).json()
        """提取翻页的max_id"""
        max_id = response['data']['max_id']
        """提取翻页的max_id_type"""
        max_id_type = response['data']['max_id_type']
        """构造GET请求参数"""
        data = {
            'id': weibo_id,
            'mid': weibo_id,
            'max_id': max_id,
            'max_id_type': max_id_type
        }
        """解析评论内容"""
        self.parse_response_data(response, page_num)
        page_num+=1
        """递归回调"""
        self.parse_page_func(data, weibo_id, headers, page_num)

    def parse_response_data(self, response, page_num):
        """
        从响应中提取评论内容
        :return:
        """
        """提取出评论大列表"""
        data_list = response['data']['data']
        for data_json_dict in data_list:
            # 提取评论内容
            try:
                texts_1 = data_json_dict['text']
                """需要sub替换掉标签内容"""
                # 需要替换的内容，替换之后的内容，替换对象
                alts = ''.join(re.findall(r'alt=(.*?) ', texts_1))
                texts = re.sub("<span.*?</span>", alts, texts_1)
                # 点赞量
                like_counts = str(data_json_dict['like_count'])
                # 评论时间   格林威治时间---需要转化为北京时间
                created_at = data_json_dict['created_at']
                std_transfer = '%a %b %d %H:%M:%S %z %Y'
                std_create_times = str(datetime.strptime(created_at, std_transfer))
                # 用户名
                screen_names = data_json_dict['user']['screen_name']
                # 用户id
                user_id = data_json_dict['user']['id']
                # 用户关注人数
                follow_count = data_json_dict['user']['follow_count']
                # 用户被关注人数
                followers_count = data_json_dict['user']['followers_count']
                # 是否关注发布者
                follow_me = data_json_dict['user']['follow_me']
                
                save_dict_state = {
                    "user_id":user_id,
                    "follow_me":follow_me,
                    "followers_count":followers_count,
                    "follow_count":follow_count,
                    "screen_names":screen_names,
                    "std_create_times":std_create_times,
                    "like_counts":like_counts,
                    "texts":texts
                }
                self.all_data_dict.append(save_dict_state)
            except Exception as e:
                print("Exception")
                exit()
        if page_num%20==0:
            print(f'*****第{page_num}页评论打印完成*****')
    def write_to_file(self,data_dict):
        save_file_name = os.path.join(self.result_dir,self.weibo_id + ".json")
        with open(save_file_name,mode="a",encoding='utf-8') as wfp:
            wfp.write(json.dumps(data_dict)+"\n")
    def get_value(self,):
        saved_data = {
            "weibo_id":self.weibo_id,
            "all_data_dict":self.all_data_dict
        }
        return saved_data
    def save_json(self,save_file_name):
        with open(save_file_name,mode="w",encoding="utf-8") as wfp:
            for data in self.all_data_dict:
                wfp.write(json.dumps(data)+"\n")
if __name__ == '__main__':
    cookie1 = "_T_WM=e318a7d0acead754584ffacda975c5d1; SUB=_2A25PoQcSDeRhGeNJ6VcU9SfIzzmIHXVtbalarDV6PUJbkdCOLWrYkW1NS_bDZZK18KilSkak3DK-hjr1r9Sy-SVM; SCF=AtUS8fdhIAL2DgBFhbQiJr7tjuI23OR1KvLDDxprTvokW3nBON9dDqmDnWsveIlJ7r63mCjncFoiQgt9DGxNvzQ.; SSOLoginState=1655011139"
    cookie2 = "_T_WM=ee958d2202f05bbb79e484711d3acfc4; SUB=_2A25PotiuDeRhGeBM7VAR8ijJzzuIHXVtbPjmrDV6PUJbktB-LRPlkW1NRNorpXUWnqRhkvzrIm0yy_pJFccFv0TF; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFWwwSPQexyx.U3RcoU.by95NHD95QceoqEehzcSKBNWs4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNSozceo5ESo-XS7tt; SSOLoginState=1655089406"
    cookies_list = [cookie1,cookie2]
    save_csv_file = os.path.join("./data","hots1.csv")
    all_dataset = pd.read_csv(save_csv_file)
    weibo_id_list = all_dataset['微博id'].values
    random.shuffle(weibo_id_list)
    save_json_file = "all_data.json"
    if not os.path.exists("./result"):
        os.mkdir("./result")
    idx = 0
    cookie = cookies_list[random.randint(0,1)]
    for weibo_id in weibo_id_list:
        print("处理微博 %s"%weibo_id)
        w = WBSpider(weibo_id,cookie)
        save_file_name = os.path.join("./result",weibo_id+".json")
        if not os.path.exists(save_file_name):
            try:
                w.start()
            except Exception as e:
                cookie = cookies_list[(idx+1)%2]
                print(e,"外部")
            finally:
                w.save_json(save_file_name)
            from tqdm import tqdm
            import time
            for _ in tqdm(range(300),desc="等待时间"):
                time.sleep(1)
                
