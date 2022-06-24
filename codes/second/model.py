import os
import json
import datetime
import time
import numpy as np
from snownlp import SnowNLP
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm

def parse_to_int(sent):
    if sent == "None": return 0
    if type(sent)==int:return sent
    if sent[-1]=='万':
        sent = float(sent[:-1])*10000
    elif sent[-1]=='亿':
        sent = float(sent[:-1])*10000*10000
    return int(sent)
def cal_value(like_counts,follow_count,followers_count):
    ug = 1.5
    uf = 1.25
    uc = 0.5
    kc = 2000*2000
    val = ug*np.log(1+like_counts)+uf*np.log(1+followers_count)+uc*np.log(1+follow_count/(kc*follow_count**2+1))
    return val
def cal_goods(like_counts):
    ug = 1.5
    val = ug*np.log(1+like_counts)
    return val
def get_dataset(json_file_name):
    data_set = []
    with open(json_file_name,mode="r",encoding="utf-8") as rfp:
        for line in rfp:
            data_dict = json.loads(line.strip())
            user_id = data_dict['user_id']
            like_counts = data_dict['like_counts']
            like_counts = parse_to_int(like_counts)
            follow_count = data_dict['follow_count']
            follow_count = parse_to_int(follow_count)
            followers_count = data_dict['followers_count']
            followers_count = parse_to_int(followers_count)
            texts = data_dict['texts']
            std_create_times = data_dict['std_create_times']
            if texts.strip()=="":texts="\t\t\t\t"
            hot_val = cal_value(like_counts,follow_count,followers_count)
            sent_val = SnowNLP(texts).sentiments
            goods_val = cal_goods(like_counts)
            data_set.append([user_id,hot_val,sent_val,goods_val,std_create_times])
    return pd.DataFrame(data_set,columns=["user_id","hots_value","sentiment_value","goods_value","std_create_times"])
class KMeans:
    def __init__(self,num_k,epoches):
        self.num_k = num_k
        self.epoches = epoches
        self.centers = np.zeros((num_k,),dtype=np.float64)
        self.labels = None
        self.sentiments = np.zeros((num_k,),dtype=np.float64)
        self.goods = np.zeros((num_k,),dtype=np.float64)
    def fit(self,all_data_set):
        """
        data_set:(hot_rate)
        """
        data_set = all_data_set['hots_value'].values
        sentiment = all_data_set['sentiment_value'].values
        goods_value = all_data_set['goods_value'].values
        length = len(data_set)
        selected_index = np.random.permutation(length)[:self.num_k]
        self.centers = data_set[selected_index]
        for _ in range(self.epoches):
            data_val = data_set[np.newaxis,:]
            center_val = self.centers[np.newaxis,:].repeat(length,axis=0).T
            data_val = np.repeat(data_val,self.num_k,axis=0)
            dis = np.abs(center_val - data_val)
            self.labels = np.argmin(dis,axis=0)
            for idx in range(self.num_k):
                tmp_index = np.where(self.labels==idx)[0]
                center_out = data_set[tmp_index]
                sentiment_center = sentiment[tmp_index]
                goods_center = goods_value[tmp_index]
                self.centers[idx] = center_out.mean()
                self.sentiments[idx] = sentiment_center.mean()
                self.goods[idx] = goods_center.mean()
    def get_center(self,):
        return self.centers
    def get_label(self):
        return self.labels
    def get_sentiment(self):
        return self.sentiments
    def get_goods(self):
        return self.goods
def draw_cluster():
    num_k = 4
    epoches = 20
    result_dir = "./result"
    color_list = ['blue','green','pink','red']
    result_pictures_dir = os.path.join(result_dir,"pictures")
    result_comments_dir = os.path.join(result_dir,"comments")
    if not os.path.exists(result_pictures_dir):
        os.makedirs(result_pictures_dir)
    for file_name in tqdm(os.listdir(result_comments_dir),desc="processing"):
        raw_file_name = os.path.join(result_comments_dir,file_name)
        save_file_name = os.path.join(result_pictures_dir,file_name.split('.')[0]+".jpg")
        if os.path.exists(save_file_name):
            continue
        dataset = get_dataset(raw_file_name)
        model = KMeans(num_k,epoches)
        model.fit(dataset)
        centers = model.get_center()
        labels = model.get_label()
        sentiments = model.get_sentiment()
        goods = model.get_goods()
        std_create_times = dataset['std_create_times'].values
        sentiment_value = dataset['sentiment_value'].values
        hots_value = dataset['hots_value'].values
        goods_value = dataset['goods_value'].values
        plt.figure(figsize=(9,6))
        for col_idx,st_v,gd_v in zip(labels,hots_value,goods_value):
            plt.scatter(gd_v,st_v,c=color_list[col_idx])
        for color,st_v,gd_v in zip(color_list,centers,goods):
            plt.scatter(gd_v,st_v,c=color,linewidths=2,marker='o',s=160,alpha=0.6,label="%0.1f"%st_v)
        plt.legend()
        plt.title("The cluster result")
        plt.xlabel("Hots value")
        plt.ylabel("Goods value")
        plt.savefig(save_file_name)
        plt.close()
def draw_time(time_list,title,save_fig_file,xtricks=range(0,365,30),color='blue'):
    time_val = [m[0] for m in time_list]
    value_val = [m[1] for m in time_list]
    fig = plt.figure(figsize=(15,9))
    print(color)
    plt.plot(time_val,value_val,c=color)
    plt.xticks(xtricks)
    fig.autofmt_xdate()
    plt.tick_params(axis='both',which='major',labelsize=16)
    plt.title(title)
    plt.savefig(save_fig_file)
    plt.close()
def draw_sentiment():
    result_dir = "./result"
    result_pictures_dir = os.path.join(result_dir,"pictures")
    result_comments_dir = os.path.join(result_dir,"comments")
    result_times_dir = os.path.join(result_dir,"times")
    if not os.path.exists(result_times_dir):
        os.makedirs(result_times_dir)
    for file_name in tqdm(os.listdir(result_comments_dir),desc="processing"):
        raw_file_name = os.path.join(result_comments_dir,file_name)
        save_file_name = os.path.join(result_pictures_dir,file_name.split('.')[0]+".jpg")
        dataset = get_dataset(raw_file_name)
        std_create_times = dataset['std_create_times'].values
        sentiment_value = (dataset['sentiment_value'].values-0.5)*2
        time_list = list(map(lambda x:x.split('+')[0],std_create_times))
        all_dataset = list(zip(time_list,sentiment_value))
        all_dataset = sorted(all_dataset,key=lambda x:datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S'))
        
        max_time = max([datetime.datetime.strptime(item[0], '%Y-%m-%d %H:%M:%S') for item in all_dataset])
        min_time = min([datetime.datetime.strptime(item[0], '%Y-%m-%d %H:%M:%S') for item in all_dataset])
        delta_time = (max_time-min_time).days
        
        save_fig_file = os.path.join(result_times_dir,file_name.split('.')[0]+'.png')
        draw_time(all_dataset,title="Topic sentiment along with time",save_fig_file=save_fig_file,xtricks=range(0,len(all_dataset),100))
def draw_time_with_hots():
    result_dir = "./result"
    result_figures_dir = os.path.join(result_dir,"figures")
    result_comments_dir = os.path.join(result_dir,"comments")
    if not os.path.exists(result_figures_dir):
        os.makedirs(result_figures_dir)
    color_list = ['blue','green','purple','red']
    idx = 0
    for file_name in tqdm(os.listdir(result_comments_dir),desc="processing"):
        raw_file_name = os.path.join(result_comments_dir,file_name)
        save_file_name = os.path.join(result_figures_dir,file_name.split('.')[0]+".jpg")
        if os.path.exists(save_file_name):
            continue
        dataset = get_dataset(raw_file_name)
        data_set = dataset[['hots_value','std_create_times']]
        data_dict = {}
        for ht_v,st_v in zip(data_set['hots_value'].values,data_set['std_create_times'].values):
            data_dict[st_v.split('+')[0]] = ht_v
        all_dataset = list(zip(data_dict.keys(),data_dict.values()))
        
        draw_time(all_dataset,title="Topic sentiment along with time",save_fig_file=save_file_name,xtricks=range(0,len(all_dataset),100),
                  color=color_list[idx])
        idx = (idx+1)%len(color_list)
def main():
    draw_time_with_hots()
    # draw_cluster()
    # draw_sentiment()
if __name__ == "__main__":
    main()


