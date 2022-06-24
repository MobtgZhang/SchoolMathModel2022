import copy
import os
import sys
import requests
import logging
import random
import time

import pandas as pd
from lxml import etree
from datetime import date, datetime, timedelta
from tqdm import tqdm

logger = logging.getLogger('src.spider')

from .util import get_user_config_list,str_to_time,update_user_config_file
from .user import User
from .parser import IndexParser,PageParser

class Spider:
    def __init__(self,config,result_dir=None):
        """Weibo类初始化"""
        self.result_dir = result_dir
        self.filter = config['filter']  # 取值范围为0、1,程序默认值为0,代表要爬取用户的全部微博,1代表只爬取用户的原创微博
        since_date = config['since_date']
        if isinstance(since_date, int):
            since_date = date.today() - timedelta(since_date)
        self.since_date = str(
            since_date)  # 起始时间，即爬取发布日期从该值到结束时间的微博，形式为yyyy-mm-dd
        self.end_date = config[
            'end_date']  # 结束时间，即爬取发布日期从起始时间到该值的微博，形式为yyyy-mm-dd，特殊值"now"代表现在
        random_wait_pages = config['random_wait_pages']
        self.random_wait_pages = [
            min(random_wait_pages),
            max(random_wait_pages)
        ]  # 随机等待频率，即每爬多少页暂停一次
        random_wait_seconds = config['random_wait_seconds']
        self.random_wait_seconds = [
            min(random_wait_seconds),
            max(random_wait_seconds)
        ]  # 随机等待时间，即每次暂停要sleep多少秒
        self.global_wait = config['global_wait']  # 配置全局等待时间，如每爬1000页等待3600秒等
        self.page_count = 0  # 统计每次全局等待后，爬取了多少页，若页数满足全局等待要求就进入下一次全局等待
        self.write_mode = config['write_mode']  # 结果信息保存类型，为list形式，可包含txt、csv、json三种类型
        self.file_download_timeout = config.get(
            'file_download_timeout',
            [5, 5, 10
             ])  # 控制文件下载“超时”时的操作，值是list形式，包含三个数字，依次分别是最大超时重试次数、最大连接时间和最大读取时间
        self.cookie = config['cookie']
        
        self.sqlite_config = config.get('sqlite_config')
        self.user_config_file_path = ''
        user_id_list = config['user_id_list']
        if not isinstance(user_id_list, list):
            if not os.path.isabs(user_id_list):
                user_id_list = os.getcwd() + os.sep + user_id_list
            if not os.path.isfile(user_id_list):
                logger.warning('不存在%s文件', user_id_list)
                sys.exit()
            self.user_config_file_path = user_id_list
        if isinstance(user_id_list, list):
            # 第一部分是处理dict类型的
            # 第二部分是其他类型,其他类型提供去重功能
            user_config_list = list(
                map(
                    lambda x: {
                        'user_uri': x['id'],
                        'since_date': x.get('since_date', self.since_date),
                        'end_date': x.get('end_date', self.end_date),
                    }, [
                        user_id for user_id in user_id_list
                        if isinstance(user_id, dict)
                    ])) + list(
                        map(
                            lambda x: {
                                'user_uri': x,
                                'since_date': self.since_date,
                                'end_date': self.end_date
                            },
                            set([
                                user_id for user_id in user_id_list
                                if not isinstance(user_id, dict)
                            ])))
        else:
            user_config_list = get_user_config_list(
                user_id_list, self.since_date)
            for user_config in user_config_list:
                user_config['end_date'] = self.end_date
        self.user_config_list = user_config_list  # 要爬取的微博用户的user_config列表
        self.user_config = {}  # 用户配置,包含用户id和since_date
        self.new_since_date = ''  # 完成某用户爬取后，自动生成对应用户新的since_date
        self.user = User()  # 存储爬取到的用户信息
        self.got_num = 0  # 存储爬取到的微博数
        self.weibo_id_list = []  # 存储爬取到的所有微博id
    def get_user_info(self, user_uri):
        """获取用户信息"""
        self.user = IndexParser(self.cookie, user_uri).get_user()
        self.page_count += 1
    def get_one_user(self, user_config):
        """获取一个用户的微博"""
        try:
            self.get_user_info(user_config['user_uri'])
            logger.info(self.user)
            logger.info('*' * 100)

            self.initialize_info(user_config)
            self.write_user(self.user)
            logger.info('*' * 100)

            for weibos in self.get_weibo_info():
                self.write_weibo(weibos)
                self.got_num += len(weibos)
            if not self.filter:
                logger.info(u'共爬取' + str(self.got_num) + u'条微博')
            else:
                logger.info(u'共爬取' + str(self.got_num) + u'条原创微博')
            logger.info(u'信息抓取完毕')
            logger.info('*' * 100)
        except Exception as e:
            logger.exception(e)
    def write_user(self, user):
        """将用户信息写入数据库"""
        for writer in self.writers:
            writer.write_user(user)
    def get_weibo_info(self):
        """获取微博信息"""
        try:
            since_date = str_to_time(
                self.user_config['since_date'])
            now = datetime.now()
            if since_date <= now:
                page_num = IndexParser(
                    self.cookie,
                    self.user_config['user_uri']).get_page_num()  # 获取微博总页数
                self.page_count += 1
                if self.page_count > 2 and (self.page_count +
                                            page_num) > self.global_wait[0][0]:
                    wait_seconds = int(
                        self.global_wait[0][1] *
                        min(1, self.page_count / self.global_wait[0][0]))
                    logger.info(u'即将进入全局等待时间，%d秒后程序继续执行' % wait_seconds)
                    for i in tqdm(range(wait_seconds)):
                        time.sleep(1)
                    self.page_count = 0
                    self.global_wait.append(self.global_wait.pop(0))
                page1 = 0
                random_pages = random.randint(*self.random_wait_pages)
                for page in tqdm(range(1, page_num + 1), desc='Progress'):
                    weibos, self.weibo_id_list, to_continue = PageParser(
                        self.cookie,
                        self.user_config, page, self.filter).get_one_page(
                            self.weibo_id_list)  # 获取第page页的全部微博
                    logger.info(
                        u'%s已获取%s(%s)的第%d页微博%s',
                        '-' * 30,
                        self.user.nickname,
                        self.user.id,
                        page,
                        '-' * 30,
                    )
                    self.page_count += 1
                    if weibos:
                        yield weibos
                    if not to_continue:
                        break

                    # 通过加入随机等待避免被限制。爬虫速度过快容易被系统限制(一段时间后限
                    # 制会自动解除)，加入随机等待模拟人的操作，可降低被系统限制的风险。默
                    # 认是每爬取1到5页随机等待6到10秒，如果仍然被限，可适当增加sleep时间
                    if (page - page1) % random_pages == 0 and page < page_num:
                        time.sleep(random.randint(*self.random_wait_seconds))
                        page1 = page
                        random_pages = random.randint(*self.random_wait_pages)

                    if self.page_count >= self.global_wait[0][0]:
                        logger.info(u'即将进入全局等待时间，%d秒后程序继续执行' %
                                    self.global_wait[0][1])
                        for i in tqdm(range(self.global_wait[0][1])):
                            time.sleep(1)
                        self.page_count = 0
                        self.global_wait.append(self.global_wait.pop(0))

                # 更新用户user_id_list.txt中的since_date
                if self.user_config_file_path:
                    update_user_config_file(
                        self.user_config_file_path,
                        self.user_config['user_uri'],
                        self.user.nickname,
                        self.new_since_date,
                    )
        except Exception as e:
            logger.exception(e)


    def initialize_info(self, user_config):
        """初始化爬虫信息"""
        self.got_num = 0
        self.user_config = user_config
        self.weibo_id_list = []
        if self.end_date == 'now':
            self.new_since_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        else:
            self.new_since_date = self.end_date
        self.writers = []
        if 'csv' in self.write_mode:
            from .writer import CsvWriter
            self.writers.append(CsvWriter(self._get_filepath('csv'), self.filter))
        
        if 'txt' in self.write_mode:
            from .writer import TxtWriter
            self.writers.append(TxtWriter(self._get_filepath('txt'), self.filter))

        if 'json' in self.write_mode:
            from .writer import JsonWriter
            self.writers.append(JsonWriter(self._get_filepath('json')))

        if 'sqlite' in self.write_mode:
            from .writer import SqliteWriter
            self.writers.append(SqliteWriter(self.sqlite_config))

    def _get_filepath(self, type):
        """获取结果文件路径"""
        try:
            if self.result_dir is None:
                self.result_dir = os.getcwd()
            file_dir = os.path.join(self.result_dir,'weibo')
            if not os.path.isdir(file_dir):
                os.makedirs(file_dir)
            file_path = os.path.join(file_dir,self.user.id+'.'+type)
            # file_path = file_dir + os.sep + self.user.id + '.' + type
            return file_path
        except Exception as e:
            logger.exception(e)
    def write_weibo(self, weibos):
        """将爬取到的信息写入文件或数据库"""
        for writer in self.writers:
            writer.write_weibo(weibos)
    def start(self):
        """运行爬虫"""
        try:
            if not self.user_config_list:
                logger.info(u'没有配置有效的user_id，请通过config.json或user_id_list.txt配置user_id')
                return
            user_count = 0
            user_count1 = random.randint(*self.random_wait_pages)
            random_users = random.randint(*self.random_wait_pages)
            time_out = pd.date_range(self.since_date,self.end_date,freq='MS')
            time_out = time_out.strftime('%F').values.tolist()
            time_list = [(time_out[k],time_out[k+1]) for k in range(len(time_out)-1)]
            time_index = 0
            user_config_list = copy.copy(self.user_config_list)
            random.shuffle(user_config_list)
            for user_config in user_config_list:
                if (user_count - user_count1) % random_users == 0:
                    time.sleep(random.randint(*self.random_wait_seconds))
                    user_count1 = user_count
                    random_users = random.randint(*self.random_wait_pages)
                user_count += 1
                # 修改日期
                user_config['since_date'] = time_list[time_index][0]
                user_config['end_date'] = time_list[time_index][1]
                time_index = (time_index+1)%len(time_list)
                self.get_one_user(user_config)
        except Exception as e:
            logger.exception(e)

class WeiBoFollower:
    def __init__(self,config,result_dir = None,data_dir =None):
        self.check(config)
        self.cookie = config['cookie']
        user_id_list = config['user_id_list']

        if result_dir is None:
            self.result_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0],"result")
        else:
            self.result_dir = result_dir
        if data_dir is None:
            self.result_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0],"data")
        else:
            self.data_dir = data_dir
        if not os.path.exists(self.result_dir):
            os.makedirs(self.result_dir)
        if not isinstance(user_id_list, list):
            user_id_list = self.get_user_list(user_id_list)
        self.user_id_list = user_id_list  # get the list of weibo user_id
        self.user_id = ''
        self.follow_list = []  # here store all the user_ids and names in the list
    def check(self,config):
        """
        check configure wether right or not
        """
        user_id_list = config['user_id_list']
        if (not isinstance(user_id_list,list)) and (not user_id_list.endswith('.txt')):
            sys.exit(u'The value of user_id_list should be type of list or the file path end with "txt".')
        if not isinstance(user_id_list, list):
            if not os.path.isfile(user_id_list):
                sys.exit(u'There doesn\'t exists the file %s' % user_id_list)
    def get_user_list(self,user_id_file):
        """
        get the weibo user id numbers from user_id_file
        """
        with open(user_id_file,mode="r",encoding="utf-8") as rfp:
            lines = rfp.read().splitlines()
            lines = [line.strip() for line in lines]
            user_id_list = []
            for line in lines:
                info = line.split(' ')
                if len(info) > 0 and info[0].isdigit():
                    user_id = info[0]
                    user_name = info[1]
                    if user_id not in user_id_list:
                        user_id_list.append({
                            "user_id":user_id,
                            "user_name":user_name
                        })
        return user_id_list
    def deal_html(self,url):
        try:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36'
            headers = {
                'User_Agent': user_agent,
                'Cookie': self.cookie,
                'Connection': 'close'
            }
            html = requests.get(url, headers=headers).content
            selector = etree.HTML(html)
            return selector
        except Exception as e:
            logger.exception(e)
    def get_page_num(self):
        """获取关注列表页数"""
        url = "https://weibo.cn/%s/follow" % self.user_id
        selector = self.deal_html(url)
        if selector.xpath("//input[@name='mp']") == []:
            page_num = 1
        else:
            page_num = (int)(
                selector.xpath("//input[@name='mp']")[0].attrib['value'])
        return page_num
    def get_one_page(self,page):
        """获取第page页的user_id"""
        logger.info(u'%s第%d页%s' % ('-' * 30, page, '-' * 30))
        url = 'https://weibo.cn/%s/follow?page=%d' % (self.user_id, page)
        selector = self.deal_html(url)
        table_list = selector.xpath('//table')
        if (page == 1 and len(table_list) == 0):
            logger.error(u'cookie无效或提供的user_id无效')
        else:
            for t in table_list:
                im = t.xpath('.//a/@href')[-1]
                uri = im.split('uid=')[-1].split('&')[0].split('/')[-1]
                nickname = t.xpath('.//a/text()')[0]
                if {'uri': uri, 'nickname': nickname} not in self.follow_list:
                    self.follow_list.append({'uri': uri, 'nickname': nickname})
                    logger.info(u'%s %s' % (nickname, uri))
    def get_follow_list(self):
        """
        get the following list for user_id
        """
        page_num = self.get_page_num()
        logger.info(u'用户关注页数：' + str(page_num))
        page1 = 0
        random_pages = random.randint(1, 5)
        for page in tqdm(range(1, page_num + 1), desc=u'关注列表爬取进度'):
            self.get_one_page(page)

            if page - page1 == random_pages and page < page_num:
                # time.sleep(random.randint(6, 10))
                page1 = page
                random_pages = random.randint(1, 5)
    def initialize_info(self,user_id):
        self.user_id = user_id
        self.follow_list = []
    def load_txt(self,file_name):
        all_user_id_dict = {}
        with open(file_name,mode="r",encoding="utf-8") as rfp:
            for line in rfp:
                data_values = line.strip().split(' ')
                all_user_id_dict[data_values[0]] = data_values[1]
        return all_user_id_dict
    def write_to_txt(self,):
        user_id_list_file = os.path.join(self.data_dir,'user_id_list.txt')
        if os.path.exists(user_id_list_file):
            user_id_dict = self.load_txt(user_id_list_file)
        else:
            user_id_dict = None
        save_user_file = os.path.join(self.result_dir,'search_user_id_list.txt')
        with open(save_user_file, 'ab') as f:
            for user in self.user_id_list:
                if type(user) == dict:
                    if user_id_dict is not None:
                        if user['user_id'] not in user_id_dict:
                            f.write((user['user_id'] + ' ' + user['user_name'] + '\n').encode(
                                sys.stdout.encoding))
                    else:
                        f.write((user['user_id'] + ' ' + user['user_name'] + '\n').encode(
                                    sys.stdout.encoding))
                            
            for user in self.follow_list:
                if user_id_dict is not None:
                    if user['uri'] not in user_id_dict:
                        f.write((user['uri'] + ' ' + user['nickname'] + '\n').encode(
                            sys.stdout.encoding))
                else:
                    f.write((user['uri'] + ' ' + user['nickname'] + '\n').encode(
                            sys.stdout.encoding))
    def start(self,):
        """
        run the code
        """
        try:
            for user_config in self.user_id_list:
                if type(user_config) == dict:
                    user_id = user_config['user_id']
                else:
                    user_id = user_config
                self.initialize_info(user_id)
                logger.info('*' * 100)
                self.get_follow_list()  # 爬取微博信息
                self.write_to_txt()
                logger.info(u'信息抓取完毕')
                logger.info('*' * 100)
        except Exception as e:
            logger.exception(e)
class WeiboUsers:
    def __init__(self,config,result_dir = None,data_dir =None):
        self.check(config)
        self.cookie = config['cookie']
        user_id_list = config['user_id_list']

        if result_dir is None:
            self.result_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0],"result")
        else:
            self.result_dir = result_dir
        if data_dir is None:
            self.result_dir = os.path.join(os.path.split(os.path.realpath(__file__))[0],"data")
        else:
            self.data_dir = data_dir
        if not os.path.exists(self.result_dir):
            os.makedirs(self.result_dir)
        if not isinstance(user_id_list, list):
            user_id_list = self.get_user_list(user_id_list)
        self.user_id_list = user_id_list  # get the list of weibo user_id
        self.user_id = ''
        self.users_list = []  # here store all the user infos
    def get_user_list(self,user_id_file):
        """
        get the weibo user id numbers from user_id_file
        """
        with open(user_id_file,mode="r",encoding="utf-8") as rfp:
            lines = rfp.read().splitlines()
            lines = [line.strip() for line in lines]
            user_id_list = []
            for line in lines:
                info = line.split(' ')
                if len(info) > 0 and info[0].isdigit():
                    user_id = info[0]
                    user_name = info[1]
                    if user_id not in user_id_list:
                        user_id_list.append({
                            "user_id":user_id,
                            "user_name":user_name
                        })
        return user_id_list
    def start(self,):
        pass
