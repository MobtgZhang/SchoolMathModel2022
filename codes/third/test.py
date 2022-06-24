import json
import gensim
from gensim import corpora
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')  # To ignore all warnings that arise here to enhance clarity
import jieba
 
from gensim.models.coherencemodel import CoherenceModel
from gensim.models.ldamodel import LdaModel
def main():
    load_csv_file = "./data/hots.csv"
    data_set=[]  #建立存储分词的列表
    dataset = pd.read_csv(load_csv_file)
    dataset['微博正文'] = dataset['微博正文'].map(lambda x:" ".join(list(jieba.cut(x))))
    load_stopwords = "./data/stopwords_zh.json"
    with open(load_stopwords,mode="r",encoding="utf-8") as rfp:
        word_dict = json.load(rfp)
    data_set = list(dataset['微博正文'].map(lambda x:[w for w in x.split() if w not in word_dict]))
    
    num_topics = 30
    dictionary = corpora.Dictionary(data_set)  # 构建词典
    corpus = [dictionary.doc2bow(text) for text in data_set]  #表示为第几个单词出现了几次
    ldamodel = LdaModel(corpus, num_topics=num_topics, id2word = dictionary, passes=30,random_state = 1)   #分为10个主题
    result = ldamodel.print_topics(num_topics=num_topics, num_words=8) #每个主题输出15个单词
    result_list = [item[1] for item in result]
    idx = 1
    with open("save.csv",mode="w",encoding="utf-8") as wfp:
        for item in result_list:
            output = item.split("+")
            lines = []
            for word in output:
                prob,word = word.split("*")
                lines.append(prob)
                lines.append(word)
            line = "话题%d,"%idx +",".join(lines)
            idx+= 1
            wfp.write(line+"\n")
if __name__ == "__main__":
    main()
