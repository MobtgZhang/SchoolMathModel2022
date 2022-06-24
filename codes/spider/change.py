import pandas as pd

dataset = pd.read_csv("all_data_utf8-modify.csv")
dataset.to_csv("all_data_gbk-modify.csv",encoding="gbk",errors='ignore',index=None)
