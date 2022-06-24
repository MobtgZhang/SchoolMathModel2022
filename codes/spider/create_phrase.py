import copy
import numpy as np
import pandas as pd
from pyhanlp import HanLP
def main():
    file_name = "all_data.csv"
    dataset = pd.read_csv(file_name)
    dataset = dataset[['微博id','微博正文','发布时间','点赞数','转发数','评论数']]
    wc = 1.5
    wt = 1.0
    wg = 0.5
    length = 5
    dataset['热度值'] =  np.log(dataset['评论数']+1)*wc + np.log(dataset['点赞数']+1)*wg+ np.log(dataset['转发数']+1)*wt
    filter_dataset = copy.copy(dataset[dataset['热度值']>=30.0])
    filter_dataset['关键短语'] = filter_dataset['微博正文'].map(lambda x:"#SPLIT#".join(HanLP.extractPhrase(x,length)))
    filter_dataset.to_csv("hots.csv",index=None)
    filter_dataset.to_excel("hots.xlsx",index=None)
    print(len(fil))
if __name__ == "__main__":
    main()
    
    