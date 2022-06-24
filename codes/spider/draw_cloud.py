import json
import os
import wordcloud
import imageio
import pandas as pd
from pyhanlp import HanLP
import string

def main():
    stop_words_file = os.path.join("./data","stopwords_zh.json")
    with open(stop_words_file,mode="r",encoding='utf-8') as rfp:
        word_dict = set(json.load(rfp))
    word_dict.add('http')
    word_dict.add('cn')
    for letter in string.ascii_letters:
        word_dict.add(letter)
    result_dir = os.path.join('./result','pictures')
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    font_file = os.path.join("./result",'msyh.ttc')
    dataset_file = "hots.csv"
    dataset = pd.read_csv(dataset_file)
    sep_data = dataset[['微博id','微博正文','发布时间']]
    sep_data['微博正文'] = sep_data['微博正文'].map(lambda x:" ".join([term.word for term in HanLP.segment(x)]))
    year_list = ['2017','2018','2019','2020','2021','2022']
    for year in year_list:
        temp_data = sep_data[sep_data['发布时间'].map(lambda x:x.split('-')[0])==year]
        all_text = "\t".join(temp_data['微博正文'].values)
        w = wordcloud.WordCloud(height=800, width=1600, font_path=font_file, background_color='white', stopwords=word_dict)
        w.generate(all_text)
        save_fig_file = os.path.join(result_dir,"%s-word-cloud.png"%year)
        w.to_file(save_fig_file)
        print("Saved file:%s"%save_fig_file)
if __name__ == "__main__":
    main()
    

    