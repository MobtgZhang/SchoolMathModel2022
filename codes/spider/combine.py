import os
import pandas as pd
def main():
    data_dir = os.path.join('result','weibo-ext')
    file_name = os.path.join('result','search_user_id_list-raw.txt')
    all_data_dict = {}
    with open(file_name,mode='r',encoding='utf-8') as rfp:
        for line in rfp:
            out = line.strip().split(' ')
            user_id = out[0]
            user_name = out[1]
            all_data_dict[user_id] = user_name
    all_dataset = []
    for filename in os.listdir(data_dir):
        root_file_name = os.path.join(data_dir,filename)
        user_id = filename.split('.')[0]
        user_name = all_data_dict[user_id]
        data = pd.read_csv(root_file_name) 
        data['发布用户id'] = user_id
        data['用户名'] = user_name
        all_dataset.append(data)
    output_dataset = pd.concat(all_dataset)
    output_dataset.drop_duplicates(subset=['微博id'], keep='first',inplace=True)
    output_dataset.to_csv('all_data.csv',index=None)
    print(len(output_dataset))
if __name__ == "__main__":
    main()

