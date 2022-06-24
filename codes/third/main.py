import json
import os
import jieba
import numpy as np
import pandas as pd
from gaussianlda import GaussianLDAAliasTrainer
from gaussianlda.model import GaussianLDA
def main():
    load_csv_file = os.path.join("./data","hots1.csv")
    stopwords_file = os.path.join("./data","stopwords_zh.json")
    dataset = pd.read_csv(load_csv_file)
    word_dict = dict()
    docs_list = list(dataset['微博正文'].map(lambda x:list(jieba.cut(x))))
    for doc in docs_list:
        for word in doc:
            word_dict[word] = len(word_dict)
    with open(stopwords_file,mode="r",encoding="utf-8") as rfp:
        stop_words = json.load(rfp)
    corpus = [[word_dict[word] for word in doc if word not in stop_words] for doc in docs_list]
    # A small vocabulary as a list of words
    vocab = list(word_dict.keys())
    # A random embedding for each word
    # Really, you'd want to load something more useful!
    embeddings = np.random.random((len(word_dict)+1, 100))
    output_dir = "saved_model"
    if not os.path.exists(output_dir):
        # Prepare a trainer
        trainer = GaussianLDAAliasTrainer(corpus, embeddings, vocab, 2, 0.1, 0.1, save_path=output_dir)
        # Set training running
        trainer.sample(10)
    model = GaussianLDA.load(output_dir)
    iterations = 10
    for doc in docs_list:
        #print(doc)
        idx2words = list(word_dict.keys())
        topics = model.sample(doc,iterations)
        topics = [idx2words[idx] for idx in topics]
        print(topics)
if __name__ == "__main__":
    main()
    

