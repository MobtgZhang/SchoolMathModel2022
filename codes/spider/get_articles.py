#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import argparse
import json
import logging
import logging.config
import os
logging_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'logging.conf'
logging.config.fileConfig(logging_path)
logger = logging.getLogger('articles')

from src.util import validate_config
from src.spider import Spider
def check(args):
    config_file = os.path.join(args.data_dir,"config-articles.json")
    assert os.path.exists(config_file)
    if not os.path.exists(args.result_dir):
        os.mkdir(args.result_dir)
def main():
    parser = argparse.ArgumentParser("Spider for the weibo")
    parser.add_argument('--data-dir',default='./data',type=str)
    parser.add_argument('--result-dir',default='./result',type=str)
    args = parser.parse_args()
    config_file = os.path.join(args.data_dir,"config-articles.json")
    try:
        with open(config_file,mode='r',encoding='utf-8') as rfp:
            config = json.loads(rfp.read())
        validate_config(config)
        wb = Spider(config,args.result_dir)
        wb.start()  # 爬取微博信息
    except Exception as e:
        logger.exception(e)

if __name__ == '__main__':
    main()

