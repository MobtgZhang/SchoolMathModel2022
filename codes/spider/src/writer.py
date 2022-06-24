import os
import json
import codecs
import csv
import sys
import copy
import logging

from abc import ABC, abstractmethod

logger = logging.getLogger('src.writer')



class Writer(ABC):
    def __init__(self):
        """根据需要，初始化结果路径、初始化表头、初始化数据库等"""
        pass

    @abstractmethod
    def write_weibo(self, weibo):
        """给定微博信息，写入对应文本或数据库"""
        pass

    @abstractmethod
    def write_user(self, user):
        """给定用户信息，写入对应文本或数据库"""
        pass


class CsvWriter(Writer):
    def __init__(self, file_path, filter):
        self.file_path = file_path

        self.result_headers = [('微博id', 'id'), ('微博正文', 'content'),
                               ('头条文章url', 'article_url'),
                               ('原始图片url', 'original_pictures'),
                               ('微博视频url', 'video_url'),
                               ('发布位置', 'publish_place'),
                               ('发布时间', 'publish_time'),
                               ('发布工具', 'publish_tool'), ('点赞数', 'up_num'),
                               ('转发数', 'retweet_num'), ('评论数', 'comment_num')]
        if not filter:
            self.result_headers.insert(4, ('被转发微博原始图片url', 'retweet_pictures'))
            self.result_headers.insert(5, ('是否为原创微博', 'original'))
        try:
            with open(self.file_path, 'a', encoding='utf-8-sig',
                      newline='') as f:
                writer = csv.writer(f)
                writer.writerows([[kv[0] for kv in self.result_headers]])
        except Exception as e:
            logger.exception(e)

    def write_user(self, user):
        self.user = user

    def write_weibo(self, weibos):
        """将爬取的信息写入csv文件"""
        try:
            result_data = [[w.__dict__[kv[1]] for kv in self.result_headers]
                           for w in weibos]
            with open(self.file_path, 'a', encoding='utf-8-sig',
                      newline='') as f:
                writer = csv.writer(f)
                writer.writerows(result_data)
            logger.info(u'%d条微博写入csv文件完毕，保存路径：%s', len(weibos), self.file_path)
        except Exception as e:
            logger.exception(e)

class TxtWriter(Writer):
    def __init__(self, file_path, filter):
        self.file_path = file_path

        self.user_header = u'用户信息'
        self.user_desc = [('nickname', '用户昵称'), ('id', '用户id'),
                          ('weibo_num', '微博数'), ('following', '关注数'),
                          ('followers', '粉丝数')]

        if filter:
            self.weibo_header = u'原创微博内容'
        else:
            self.weibo_header = u'微博内容'
        self.weibo_desc = [('publish_place', '微博位置'), ('publish_time', '发布时间'),
                           ('up_num', '点赞数'), ('retweet_num', '转发数'),
                           ('comment_num', '评论数'), ('publish_tool', '发布工具')]

    def write_user(self, user):
        self.user = user
        user_info = '\n'.join(
            [v + '：' + str(self.user.__dict__[k]) for k, v in self.user_desc])

        with open(self.file_path, 'ab') as f:
            f.write((self.user_header + '：\n' + user_info + '\n\n').encode(
                sys.stdout.encoding))
        logger.info(u'%s信息写入txt文件完毕，保存路径：%s', self.user.nickname,
                    self.file_path)

    def write_weibo(self, weibo):
        """将爬取的信息写入txt文件"""

        weibo_header = ''
        if self.weibo_header:
            weibo_header = self.weibo_header + '：\n'
            self.weibo_header = ''

        try:
            temp_result = []
            for w in weibo:
                temp_result.append(w.__dict__['content'] + '\n' + '\n'.join(
                    [v + '：' + str(w.__dict__[k])
                     for k, v in self.weibo_desc]))
            result = '\n\n'.join(temp_result) + '\n\n'

            with open(self.file_path, 'ab') as f:
                f.write((weibo_header + result).encode(sys.stdout.encoding))
            logger.info(u'%d条微博写入txt文件完毕，保存路径：%s', len(weibo), self.file_path)
        except Exception as e:
            logger.exception(e)
class SqliteWriter(Writer):
    def __init__(self, sqlite_config):
        self.sqlite_config = sqlite_config

    def _sqlite_create(self, connection, sql):
        """创建sqlite数据库或表"""
        try:
            cursor = connection.cursor()
            cursor.execute(sql)
        finally:
            connection.close()

    def _sqlite_create_table(self, sql):
        """创建sqlite表"""
        import sqlite3
        connection = sqlite3.connect(self.sqlite_config)
        self._sqlite_create(connection, sql)

    def _sqlite_insert(self, table, data_list):
        """向sqlite表插入或更新数据"""
        import sqlite3
        if len(data_list) > 0:
            # We use this to filter out unset values.
            data_list = [{k: v
                          for k, v in data.items() if v is not None}
                         for data in data_list]

            keys = ', '.join(data_list[0].keys())
            values = ', '.join(['?'] * len(data_list[0]))
            connection = sqlite3.connect(self.sqlite_config)
            cursor = connection.cursor()
            sql = """INSERT OR REPLACE INTO {table}({keys}) VALUES ({values})""".format(
                table=table, keys=keys, values=values)
            try:
                cursor.executemany(
                    sql, [tuple(data.values()) for data in data_list])
                connection.commit()
            except Exception as e:
                connection.rollback()
                logger.exception(e)
            finally:
                connection.close()

    def write_weibo(self, weibos):
        """将爬取的微博信息写入sqlite数据库"""
        # 创建'weibo'表
        create_table = """
                CREATE TABLE IF NOT EXISTS weibo (
                id varchar(10) NOT NULL,
                user_id varchar(12),
                content varchar(2000),
                article_url varchar(200),
                original_pictures varchar(3000),
                retweet_pictures varchar(3000),
                original BOOLEAN NOT NULL DEFAULT 1,
                video_url varchar(300),
                publish_place varchar(100),
                publish_time DATETIME NOT NULL,
                publish_tool varchar(30),
                up_num INT NOT NULL,
                retweet_num INT NOT NULL,
                comment_num INT NOT NULL,
                PRIMARY KEY (id)
                )"""
        self._sqlite_create_table(create_table)
        # 在'weibo'表中插入或更新微博数据
        weibo_list = []
        info_list = copy.deepcopy(weibos)
        for weibo in info_list:
            weibo.user_id = self.user.id
            weibo_list.append(weibo.__dict__)
        self._sqlite_insert('weibo', weibo_list)
        logger.info(u'%d条微博写入sqlite数据库完毕', len(weibos))

    def write_user(self, user):
        """将爬取的用户信息写入sqlite数据库"""
        self.user = user

        # 创建'user'表
        create_table = """
                CREATE TABLE IF NOT EXISTS user (
                id varchar(20) NOT NULL,
                nickname varchar(30),
                gender varchar(10),
                location varchar(200),
                birthday varchar(40),
                description varchar(400),
                verified_reason varchar(140),
                talent varchar(200),
                education varchar(200),
                work varchar(200),
                weibo_num INT,
                following INT,
                followers INT,
                PRIMARY KEY (id)
                )"""
        self._sqlite_create_table(create_table)
        self._sqlite_insert('user', [user.__dict__])
        logger.info(u'%s信息写入sqlite数据库完毕', user.nickname)
class JsonWriter(Writer):
    def __init__(self, file_path):
        self.file_path = file_path

    def write_user(self, user):
        self.user = user

    def _update_json_data(self, data, weibo_info):
        """更新要写入json结果文件中的数据，已经存在于json中的信息更新为最新值，不存在的信息添加到data中"""
        data['user'] = self.user.__dict__
        if data.get('weibo'):
            is_new = 1  # 待写入微博是否全部为新微博，即待写入微博与json中的数据不重复
            for old in data['weibo']:
                if weibo_info[-1]['id'] == old['id']:
                    is_new = 0
                    break
            if is_new == 0:
                for new in weibo_info:
                    flag = 1
                    for i, old in enumerate(data['weibo']):
                        if new['id'] == old['id']:
                            data['weibo'][i] = new
                            flag = 0
                            break
                    if flag:
                        data['weibo'].append(new)
            else:
                data['weibo'] += weibo_info
        else:
            data['weibo'] = weibo_info
        return data

    def write_weibo(self, weibos):
        """将爬到的信息写入json文件"""
        data = {}
        if os.path.isfile(self.file_path):
            with codecs.open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data = self._update_json_data(data, [w.__dict__ for w in weibos])
        with codecs.open(self.file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))
        logger.info(u'%d条微博写入json文件完毕，保存路径：%s', len(weibos), self.file_path)
