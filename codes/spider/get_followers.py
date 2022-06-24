import os
import json
import argparse
from src.spider import WeiBoFollower
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir',type=str,default='./data')
    parser.add_argument('--result-dir',type=str,default='./result')
    args = parser.parse_args()
    config_file = os.path.join(args.data_dir,"config-followers.json")
    with open(config_file,mode="r",encoding="utf-8") as rfp:
        config = json.loads(rfp.read())
    wb = WeiBoFollower(config,args.result_dir,args.data_dir)
    wb.start()
if __name__ == "__main__":
    main()

