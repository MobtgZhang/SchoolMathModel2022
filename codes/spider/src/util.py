import os
import sys
import logging
import hashlib
import json
import codecs
from datetime import datetime
import requests
from lxml import etree

logger = logging.getLogger('src.util')


def handle_garbled(info):
    """处理乱码"""
    try:
        info = (info.xpath('string(.)').replace(u'\u200b', '').encode(
            sys.stdout.encoding, 'ignore').decode(sys.stdout.encoding))
        return info
    except Exception as e:
        logger.exception(e)
        return u'无'

def str_to_time(text):
    """将字符串转换成时间类型"""
    if ':' in text:
        result = datetime.strptime(text, '%Y-%m-%d %H:%M')
    else:
        result = datetime.strptime(text, '%Y-%m-%d')
    return result
def string_to_int(string):
    """字符串转换为整数"""
    if len(string) == 0:
        logger.warning("string to int, the input string is empty!")
        return 0
    if isinstance(string, int):
        return string
    elif string.endswith(u'万+'):
        string = string[:-2] + '0000'
    elif string.endswith(u'万'):
        string = float(string[:-1]) * 10000
    elif string.endswith(u'亿'):
        string = float(string[:-1]) * 100000000
    return int(string)
def hash_url(url):
    return hashlib.sha224(url.encode('utf8')).hexdigest()
def handle_html(cookie, url):
    """处理html"""
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
        headers = {'User_Agent': user_agent, 'Cookie': cookie}
        resp = requests.get(url, headers=headers)
        selector = etree.HTML(resp.content)
        return selector
    except Exception as e:
        logger.exception(e)

def _is_date(date_str):
    """判断日期格式是否正确"""
    try:
        if ':' in date_str:
            datetime.strptime(date_str, '%Y-%m-%d %H:%M')
        else:
            datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False
def validate_config(config):
    """验证配置是否正确"""

    # 验证filter、pic_download、video_download
    argument_list = ['filter']
    for argument in argument_list:
        if config[argument] != 0 and config[argument] != 1:
            logger.warning(u'%s值应为0或1,请重新输入', config[argument])
            sys.exit()

    # 验证since_date
    since_date = config['since_date']
    if (not _is_date(str(since_date))) and (not isinstance(since_date, int)):
        logger.warning(u'since_date值应为yyyy-mm-dd形式或整数,请重新输入')
        sys.exit()

    # 验证end_date
    end_date = str(config['end_date'])
    if (not _is_date(end_date)) and (end_date != 'now'):
        logger.warning(u'end_date值应为yyyy-mm-dd形式或"now",请重新输入')
        sys.exit()

    # 验证random_wait_pages
    random_wait_pages = config['random_wait_pages']
    if not isinstance(random_wait_pages, list):
        logger.warning(u'random_wait_pages参数值应为list类型,请重新输入')
        sys.exit()
    if (not isinstance(min(random_wait_pages), int)) or (not isinstance(
            max(random_wait_pages), int)):
        logger.warning(u'random_wait_pages列表中的值应为整数类型,请重新输入')
        sys.exit()
    if min(random_wait_pages) < 1:
        logger.warning(u'random_wait_pages列表中的值应大于0,请重新输入')
        sys.exit()

    # 验证random_wait_seconds
    random_wait_seconds = config['random_wait_seconds']
    if not isinstance(random_wait_seconds, list):
        logger.warning(u'random_wait_seconds参数值应为list类型,请重新输入')
        sys.exit()
    if (not isinstance(min(random_wait_seconds), int)) or (not isinstance(
            max(random_wait_seconds), int)):
        logger.warning(u'random_wait_seconds列表中的值应为整数类型,请重新输入')
        sys.exit()
    if min(random_wait_seconds) < 1:
        logger.warning(u'random_wait_seconds列表中的值应大于0,请重新输入')
        sys.exit()

    # 验证global_wait
    global_wait = config['global_wait']
    if not isinstance(global_wait, list):
        logger.warning(u'global_wait参数值应为list类型,请重新输入')
        sys.exit()
    for g in global_wait:
        if not isinstance(g, list):
            logger.warning(u'global_wait参数内的值应为长度为2的list类型,请重新输入')
            sys.exit()
        if len(g) != 2:
            logger.warning(u'global_wait参数内的list长度应为2,请重新输入')
            sys.exit()
        for i in g:
            if (not isinstance(i, int)) or i < 1:
                logger.warning(u'global_wait列表中的值应为大于0的整数,请重新输入')
                sys.exit()

    # 验证write_mode
    write_mode = ['txt', 'csv', 'json','sqlite']
    if not isinstance(config['write_mode'], list):
        logger.warning(u'write_mode值应为list类型')
        sys.exit()
    for mode in config['write_mode']:
        if mode not in write_mode:
            logger.warning(
                u'%s为无效模式，请从txt、csv、json、sqlite中挑选一个或多个作为write_mode',
                mode)
            sys.exit()

    # 验证user_id_list
    user_id_list = config['user_id_list']
    if (not isinstance(user_id_list,
                       list)) and (not user_id_list.endswith('.txt')):
        logger.warning(u'user_id_list值应为list类型或txt文件路径')
        sys.exit()
    if not isinstance(user_id_list, list):
        if not os.path.isfile(user_id_list):
            logger.warning(u'不存在%s文件', user_id_list)
            sys.exit()
def get_user_config_list(file_name, default_since_date):
    """获取文件中的微博id信息"""
    with open(file_name, 'rb') as f:
        try:
            lines = f.read().splitlines()
            lines = [line.decode('utf-8-sig') for line in lines]
        except UnicodeDecodeError:
            logger.error(u'%s文件应为utf-8编码，请先将文件编码转为utf-8再运行程序', file_name)
            sys.exit()
        user_config_list = []
        for line in lines:
            info = line.split(' ')
            if len(info) > 0 and info[0].isdigit():
                user_config = {}
                user_config['user_uri'] = info[0]
                if len(info) > 2 and _is_date(info[2]):
                    if len(info) > 3 and _is_date(info[2] + ' ' + info[3]):
                        user_config['since_date'] = info[2] + ' ' + info[3]
                    else:
                        user_config['since_date'] = info[2]
                else:
                    user_config['since_date'] = default_since_date
                if user_config not in user_config_list:
                    user_config_list.append(user_config)
    return user_config_list

def to_video_download_url(cookie, video_page_url):
    if video_page_url == '':
        return ''

    video_object_url = video_page_url.replace('m.weibo.cn/s/video/show',
                                              'm.weibo.cn/s/video/object')
    try:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
        headers = {'User_Agent': user_agent, 'Cookie': cookie}
        wb_info = requests.get(video_object_url, headers=headers).json()
        video_url = wb_info['data']['object']['stream'].get('hd_url')
        if not video_url:
            video_url = wb_info['data']['object']['stream']['url']
            if not video_url:  # 说明该视频为直播
                video_url = ''
    except json.decoder.JSONDecodeError:
        logger.warning(u'当前账号没有浏览该视频的权限')

    return video_url

def update_user_config_file(user_config_file_path, user_uri, nickname,
                            start_time):
    """更新用户配置文件"""
    if not user_config_file_path:
        user_config_file_path = os.getcwd() + os.sep + 'user_id_list.txt'
    with open(user_config_file_path, 'rb') as f:
        lines = f.read().splitlines()
        lines = [line.decode('utf-8-sig') for line in lines]
        for i, line in enumerate(lines):
            info = line.split(' ')
            if len(info) > 0:
                if user_uri == info[0]:
                    if len(info) == 1:
                        info.append(nickname)
                        info.append(start_time)
                    if len(info) == 2:
                        info.append(start_time)
                    if len(info) > 3 and _is_date(info[2] + ' ' + info[3]):
                        del info[3]
                    if len(info) > 2:
                        info[2] = start_time
                    lines[i] = ' '.join(info)
                    break
    with codecs.open(user_config_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

