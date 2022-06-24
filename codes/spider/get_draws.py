import os
from unittest import result
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import datetime

def check(item):
    try:
        year,month,day = item.split('-')
        return True
    except:
        return False
def less_time(ta,tb):
    return datetime.datetime.strptime(ta,"%Y-%m-%d")<datetime.datetime.strptime(tb,"%Y-%m-%d")
def draw_time(time_list,title,save_fig_file,xtricks=range(0,365,30)):
    time_val = ["-".join(m[0].split('-')[1:]) for m in time_list]
    value_val = [m[1] for m in time_list]
    fig = plt.figure(figsize=(15,9))
    plt.plot(time_val,value_val)
    plt.xticks(xtricks)
    fig.autofmt_xdate()
    plt.tick_params(axis='both',which='major',labelsize=16)
    plt.title(title)
    plt.savefig(save_fig_file)
    plt.close()
def get_numbers(data_sep,result_dir):
    output = data_sep['发布时间'].map(lambda x:None if type(x)==float else x.split(' ')[0])
    statical_dict = dict()
    for item in output:
        if item is not None:
            if check(item):
                pass
            else:
                continue
            if item not in statical_dict:
                statical_dict[item] = 1
            else:
                statical_dict[item] += 1
    values = list(statical_dict.items())
    values = sorted(values,key=lambda x:datetime.datetime.strptime(x[0],"%Y-%m-%d"))
    time_list = [[] for _ in range(6)]
    for item in values:
        if less_time(item[0],'2022-06-01') and not less_time(item[0],'2022-01-01'):
            time_list[5].append(item)
        elif less_time(item[0],'2021-12-31') and not less_time(item[0],'2021-01-01'):
            time_list[4].append(item)
        elif less_time(item[0],'2020-12-31') and not less_time(item[0],'2020-01-01'):
            time_list[3].append(item)
        elif less_time(item[0],'2019-12-31') and not less_time(item[0],'2019-01-01'):
            time_list[2].append(item)
        elif less_time(item[0],'2018-12-31') and not less_time(item[0],'2018-01-01'):
            time_list[1].append(item)
        elif less_time(item[0],'2017-12-31') and not less_time(item[0],'2017-01-01'):
            time_list[0].append(item)
    year_list = ['2017','2018','2019','2020','2021','2022']
    for tp_t,year in zip(time_list,year_list):
        save_file_name = os.path.join(result_dir,'%s-numbers.png'%year)
        if year!='2022':
            title_name = '%s-01-01~%s-06-01'%(year,year)
            xtricks = range(0,365,30)
        else:
            title_name = '%s-01-01~%s-06-01'%(year,year)
            xtricks = range(0,160,30)
        draw_time(tp_t,title_name,save_file_name,xtricks=range(0,160,30))
def get_goods(data_sep,result_dir):
    good_list = data_sep['点赞数'].values
    # plt.rcParams['font.sans-serif']=['SimHei']
    # plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(9,6))
    plt.hist(good_list, # 绘图数据
        bins = [500,1000,2500,5000,10000,20000,30000,40000,50000], # 指定直方图的条形数为20个
        color = 'steelblue', # 指定填充色
        edgecolor = 'k', # 设置直方图边界颜色
        label = '直方图'
        )# 为直方图呈现标签
    plt.title('Distribution map of the overall number of likes')
    plt.ylabel('The number of people of likes')
    plt.xlabel('The number of likes')
    save_fig_file = os.path.join(result_dir,'goods_dis.png')
    plt.savefig(save_fig_file)
    plt.close()
def get_forwarders(data_sep,result_dir):
    forwarders_list = data_sep['转发数'].values
    # plt.rcParams['font.sans-serif']=['SimHei']
    # plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(9,6))
    plt.hist(forwarders_list, # 绘图数据
        bins = [100,250,500,750,1000,2500,5000,10000,20000], # 指定直方图的条形数为20个
        color = 'steelblue', # 指定填充色
        edgecolor = 'k', # 设置直方图边界颜色
        )# 为直方图呈现标签
    plt.title('Distribution map of the overall number of forwarders')
    plt.ylabel('The number of people of forwarders')
    plt.xlabel('The number of forwarders')
    save_file_name = os.path.join(result_dir,'forwarders_dis.png')
    plt.savefig(save_file_name)
    plt.close()
def get_comments(data_sep,result_dir):
    comments_list = data_sep['评论数'].values
    # plt.rcParams['font.sans-serif']=['SimHei']
    # plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(9,6))
    plt.hist(comments_list, # 绘图数据
        bins = [100,250,500,750,1000,2500,5000,10000,20000], # 指定直方图的条形数为20个
        color = 'steelblue', # 指定填充色
        edgecolor = 'k', # 设置直方图边界颜色
        )# 为直方图呈现标签
    plt.title('Distribution map of the overall number of comments')
    plt.ylabel('The number of people of comments')
    plt.xlabel('The number of comments')
    save_file_name = os.path.join(result_dir,'comments_dis.png')
    plt.savefig(save_file_name)
    plt.close()
def get_hots_dis(data_sep,result_dir):
    comments_list = data_sep['评论数'].values
    goods_list = data_sep['点赞数'].values
    transfer_list = data_sep['转发数'].values
    comments_list = np.log(comments_list+1)
    goods_list = np.log(goods_list+1)
    transfer_list = np.log(transfer_list+1)
    wt = 1.0
    wg = 0.5
    wc = 1.5
    value_list = np.log(comments_list+1)*wc+np.log(goods_list+1)*wg+np.log(transfer_list+1)*wt

    # plt.rcParams['font.sans-serif']=['SimHei']
    # plt.rcParams['axes.unicode_minus'] = False
    plt.figure(figsize=(9,6))
    plt.hist(value_list, # 绘图数据
        bins = [1,1.5,2,2.5,3,3.5,4,5,6,7,8,10], # 指定直方图的条形数为20个
        color = 'steelblue', # 指定填充色
        edgecolor = 'k', # 设置直方图边界颜色
        )# 为直方图呈现标签
    plt.title('Distribution map of the overall number of hots rate')
    plt.ylabel('The number of people of hots rate')
    plt.xlabel('The number of hots rate')
    save_file_name = os.path.join(result_dir,'hots_dis.png')
    plt.savefig(save_file_name)
    plt.close()
def get_hots_along_time(data_sep,result_dir):
    comments_list = data_sep['评论数'].values
    goods_list = data_sep['点赞数'].values
    transfer_list = data_sep['转发数'].values
    time_list = data_sep['发布时间']
    comments_list = np.log(comments_list+1)
    goods_list = np.log(goods_list+1)
    transfer_list = np.log(transfer_list+1)
    wt = 1.0
    wg = 0.5
    wc = 1.5
    value_list = np.log(comments_list+1)*wc+np.log(goods_list+1)*wg+np.log(transfer_list+1)*wt
    statical_dict = dict()
    for t_tp,val in zip(time_list,value_list):
        if t_tp is not None:
            if check(t_tp):
                pass
            else:
                continue
            if t_tp in statical_dict and val>=5.0:
                statical_dict[t_tp] += val
            else:
                statical_dict[t_tp] = 0.0
    values = list(statical_dict.items())
    values = sorted(values,key=lambda x:datetime.datetime.strptime(x[0],"%Y-%m-%d"))
    time_list = [[] for _ in range(6)]
    for item in values:
        if less_time(item[0],'2022-06-01') and not less_time(item[0],'2022-01-01'):
            time_list[5].append(item)
        elif less_time(item[0],'2021-12-31') and not less_time(item[0],'2021-01-01'):
            time_list[4].append(item)
        elif less_time(item[0],'2020-12-31') and not less_time(item[0],'2020-01-01'):
            time_list[3].append(item)
        elif less_time(item[0],'2019-12-31') and not less_time(item[0],'2019-01-01'):
            time_list[2].append(item)
        elif less_time(item[0],'2018-12-31') and not less_time(item[0],'2018-01-01'):
            time_list[1].append(item)
        elif less_time(item[0],'2017-12-31') and not less_time(item[0],'2017-01-01'):
            time_list[0].append(item)
    year_list = ['2017','2018','2019','2020','2021','2022']
    for tp_t,year in zip(time_list,year_list):
        save_file_name = os.path.join(result_dir,'%s-hots.png'%year)
        if year!='2022':
            title_name = '%s-01-01~%s-06-01'%(year,year)
            xtricks = range(0,365,30)
        else:
            title_name = '%s-01-01~%s-06-01'%(year,year)
            xtricks = range(0,160,30)
        draw_time(tp_t,title_name,save_file_name,xtricks)
def main():
    
    filen_name = "all_data.csv"
    result_dir = os.path.join("./result","pictures")
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    output = pd.read_csv(filen_name)
    data_sep = output[['微博id','发布时间','点赞数','转发数','评论数']]
    get_numbers(data_sep,result_dir)
    get_goods(data_sep,result_dir)
    get_forwarders(data_sep,result_dir)
    get_comments(data_sep,result_dir)
    get_hots_dis(data_sep,result_dir)
    get_hots_along_time(data_sep,result_dir)
if __name__ == "__main__":
    main()

