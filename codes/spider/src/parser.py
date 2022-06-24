import re
import sys
import logging
import time
import random
from datetime import date, datetime, timedelta

logger = logging.getLogger('parser')

from .user import User
from .weibo import Weibo
from .util import handle_html,string_to_int,str_to_time
from .util import handle_garbled
from .util import to_video_download_url


class Parser:
    def __init__(self, cookie):
        self.cookie = cookie
        self.url = ''
        self.selector = None

class InfoParser(Parser):
    def __init__(self, cookie, user_id):
        self.cookie = cookie
        self.url = 'https://weibo.cn/%s/info' % (user_id)
        self.selector = handle_html(self.cookie, self.url)

    def extract_user_info(self):
        """提取用户信息"""
        try:
            user = User()
            nickname = self.selector.xpath('//title/text()')[0]
            nickname = nickname[:-3]
            if nickname == u'登录 - 新' or nickname == u'新浪':
                logger.warning(u'cookie错误或已过期,请按照README中方法重新获取')
                sys.exit()
            user.nickname = nickname

            basic_info = self.selector.xpath("//div[@class='c'][3]/text()")
            zh_list = [u'性别', u'地区', u'生日', u'简介', u'认证', u'达人']
            en_list = [
                'gender', 'location', 'birthday', 'description',
                'verified_reason', 'talent'
            ]
            for i in basic_info:
                if i.split(':', 1)[0] in zh_list:
                    setattr(user, en_list[zh_list.index(i.split(':', 1)[0])],
                            i.split(':', 1)[1].replace('\u3000', ''))
			
            experienced = self.selector.xpath("//div[@class='tip'][2]/text()") 
            if experienced and experienced[0] == u'学习经历':
                user.education = self.selector.xpath(
                    "//div[@class='c'][4]/text()")[0][1:].replace(
                        u'\xa0', u' ')
                if self.selector.xpath(
                        "//div[@class='tip'][3]/text()")[0] == u'工作经历':
                    user.work = self.selector.xpath(
                        "//div[@class='c'][5]/text()")[0][1:].replace(
                            u'\xa0', u' ')
            elif experienced and experienced[0] == u'工作经历':
                user.work = self.selector.xpath(
                    "//div[@class='c'][4]/text()")[0][1:].replace(
                        u'\xa0', u' ')
            return user
        except Exception as e:
            logger.exception(e)

class IndexParser(Parser):
    def __init__(self, cookie, user_uri):
        self.cookie = cookie
        self.user_uri = user_uri
        self.url = 'https://weibo.cn/%s' % (user_uri)
        self.selector = handle_html(self.cookie, self.url)

    def _get_user_id(self):
        """获取用户id，使用者输入的user_id不一定是正确的，可能是个性域名等，需要获取真正的user_id"""
        user_id = self.user_uri
        url_list = self.selector.xpath("//div[@class='u']//a")
        for url in url_list:
            if (url.xpath('string(.)')) == u'资料':
                if url.xpath('@href') and url.xpath('@href')[0].endswith(
                        '/info'):
                    link = url.xpath('@href')[0]
                    user_id = link[1:-5]
                    break
        return user_id

    def get_user(self):
        """获取用户信息、微博数、关注数、粉丝数"""
        try:
            user_id = self._get_user_id()
            self.user = InfoParser(self.cookie,
                                   user_id).extract_user_info()  # 获取用户信息
            self.user.id = user_id

            user_info = self.selector.xpath("//div[@class='tip2']/*/text()")
            self.user.weibo_num = string_to_int(user_info[0][3:-1])
            self.user.following = string_to_int(user_info[1][3:-1])
            self.user.followers = string_to_int(user_info[2][3:-1])
            return self.user
        except Exception as e:
            logger.exception(e)

    def get_page_num(self):
        """获取微博总页数"""
        try:
            if self.selector.xpath("//input[@name='mp']") == []:
                page_num = 1
            else:
                page_num = (int)(self.selector.xpath("//input[@name='mp']")
                                 [0].attrib['value'])
            return page_num
        except Exception as e:
            logger.exception(e)

class CommentParser(Parser):
    def __init__(self, cookie, weibo_id):
        self.cookie = cookie
        self.url = 'https://weibo.cn/comment/' + weibo_id
        self.selector = handle_html(self.cookie, self.url)

    def get_long_weibo(self):
        """获取长原创微博"""
        try:
            for i in range(5):
                self.selector = handle_html(self.cookie, self.url)
                if self.selector is not None:
                    info = self.selector.xpath("//div[@class='c']")[1]
                    wb_content = handle_garbled(info)
                    wb_time = info.xpath("//span[@class='ct']/text()")[0]
                    weibo_content = wb_content[wb_content.find(':') +
                                               1:wb_content.rfind(wb_time)]
                    if weibo_content is not None:
                        return weibo_content
                time.sleep(random.randint(6, 10))
        except Exception:
            logger.exception(u'网络出错')

    def get_long_retweet(self):
        """获取长转发微博"""
        try:
            wb_content = self.get_long_weibo()
            weibo_content = wb_content[:wb_content.rfind(u'原文转发')]
            return weibo_content
        except Exception as e:
            logger.exception(e)

    def get_video_page_url(self):
        """获取微博视频页面的链接"""
        video_url = ''
        try:
            self.selector = handle_html(self.cookie, self.url)
            if self.selector is not None:
                # 来自微博视频号的格式与普通格式不一致，不加 span 层级
                links = self.selector.xpath("body/div[@class='c' and @id][1]/div//a")
                for a in links:
                    if 'm.weibo.cn/s/video/show?object_id=' in a.xpath(
                            '@href')[0]:
                        video_url = a.xpath('@href')[0]
                        break
        except Exception:
            logger.exception(u'网络出错')

        return video_url
class MblogPicAllParser(Parser):
    def __init__(self, cookie, weibo_id):
        self.cookie = cookie
        self.url = 'https://weibo.cn/mblog/picAll/' + weibo_id + '?rl=1'
        self.selector = handle_html(self.cookie, self.url)

    def extract_preview_picture_list(self):
        return self.selector.xpath('//img/@src')
class PageParser(Parser):
    empty_count = 0

    def __init__(self, cookie, user_config, page, filter):
        self.cookie = cookie
        if hasattr(PageParser,
                   'user_uri') and self.user_uri != user_config['user_uri']:
            PageParser.empty_count = 0
        self.user_uri = user_config['user_uri']
        self.since_date = user_config['since_date']
        self.end_date = user_config['end_date']
        self.page = page
        self.url = 'https://weibo.cn/%s?page=%d' % (self.user_uri, page)
        if self.end_date != 'now':
            since_date = self.since_date.split(' ')[0].split('-')
            end_date = self.end_date.split(' ')[0].split('-')
            for date in [since_date, end_date]:
                for i in [1, 2]:
                    if len(date[i]) == 1:
                        date[i] = '0' + date[i]
            starttime = ''.join(since_date)
            endtime = ''.join(end_date)
            self.url = 'https://weibo.cn/%s/profile?starttime=%s&endtime=%s&advancedfilter=1&page=%d' % (
                self.user_uri, starttime, endtime, page)
        self.selector = ''
        self.to_continue = True
        is_exist = ''
        for i in range(3):
            self.selector = handle_html(self.cookie, self.url)
            info = self.selector.xpath("//div[@class='c']")
            if info is None or len(info) == 0:
                continue
            is_exist = info[0].xpath("div/span[@class='ctt']")
            if is_exist:
                PageParser.empty_count = 0
                break
        if not is_exist:
            PageParser.empty_count += 1
        if PageParser.empty_count > 2:
            self.to_continue = False
            PageParser.empty_count = 0
        self.filter = filter

    def get_one_page(self, weibo_id_list):
        """获取第page页的全部微博"""
        try:
            info = self.selector.xpath("//div[@class='c']")
            is_exist = info[0].xpath("div/span[@class='ctt']")
            weibos = []
            if is_exist:
                since_date = str_to_time(self.since_date)
                for i in range(0, len(info) - 1):
                    weibo = self.get_one_weibo(info[i])
                    if weibo:
                        if weibo.id in weibo_id_list:
                            continue
                        publish_time = str_to_time(
                            weibo.publish_time)

                        if publish_time < since_date:
                            if self.is_pinned_weibo(info[i]):
                                continue
                            else:
                                return weibos, weibo_id_list, False
                        logger.info(weibo)
                        logger.info('-' * 100)
                        weibos.append(weibo)
                        weibo_id_list.append(weibo.id)
            return weibos, weibo_id_list, self.to_continue
        except Exception as e:
            logger.exception(e)

    def is_original(self, info):
        """判断微博是否为原创微博"""
        is_original = info.xpath("div/span[@class='cmt']")
        if len(is_original) > 3:
            return False
        else:
            return True

    def get_original_weibo(self, info, weibo_id):
        """获取原创微博"""
        try:
            weibo_content = handle_garbled(info)
            weibo_content = weibo_content[:weibo_content.rfind(u'赞')]
            a_text = info.xpath('div//a/text()')
            if u'全文' in a_text:
                wb_content = CommentParser(self.cookie,
                                           weibo_id).get_long_weibo()
                if wb_content:
                    weibo_content = wb_content
            return weibo_content
        except Exception as e:
            logger.exception(e)

    def get_retweet(self, info, weibo_id):
        """获取转发微博"""
        try:
            weibo_content = handle_garbled(info)
            weibo_content = weibo_content[weibo_content.find(':') +
                                          1:weibo_content.rfind(u'赞')]
            weibo_content = weibo_content[:weibo_content.rfind(u'赞')]
            a_text = info.xpath('div//a/text()')
            if u'全文' in a_text:
                wb_content = CommentParser(self.cookie,
                                           weibo_id).get_long_retweet()
                if wb_content:
                    weibo_content = wb_content
            retweet_reason = handle_garbled(info.xpath('div')[-1])
            retweet_reason = retweet_reason[:retweet_reason.rindex(u'赞')]
            original_user = info.xpath("div/span[@class='cmt']/a/text()")
            if original_user:
                original_user = original_user[0]
                weibo_content = (retweet_reason + '\n' + u'原始用户: ' +
                                 original_user + '\n' + u'转发内容: ' +
                                 weibo_content)
            else:
                weibo_content = (retweet_reason + '\n' + u'转发内容: ' +
                                 weibo_content)
            return weibo_content
        except Exception as e:
            logger.exception(e)

    def get_weibo_content(self, info, is_original):
        """获取微博内容"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            if is_original:
                weibo_content = self.get_original_weibo(info, weibo_id)
            else:
                weibo_content = self.get_retweet(info, weibo_id)
            return weibo_content
        except Exception as e:
            logger.exception(e)

    def get_article_url(self, info):
        """获取微博头条文章的url"""
        article_url = ''
        text = handle_garbled(info)
        if text.startswith(u'发布了头条文章'):
            url = info.xpath('.//a/@href')
            if url and url[0].startswith('https://weibo.cn/sinaurl'):
                article_url = url[0]
        return article_url

    def get_publish_place(self, info):
        """获取微博发布位置"""
        try:
            div_first = info.xpath('div')[0]
            a_list = div_first.xpath('a')
            publish_place = u'无'
            for a in a_list:
                if ('place.weibo.com' in a.xpath('@href')[0]
                        and a.xpath('text()')[0] == u'显示地图'):
                    weibo_a = div_first.xpath("span[@class='ctt']/a")
                    if len(weibo_a) >= 1:
                        publish_place = weibo_a[-1]
                        if (u'视频' == div_first.xpath(
                                "span[@class='ctt']/a/text()")[-1][-2:]):
                            if len(weibo_a) >= 2:
                                publish_place = weibo_a[-2]
                            else:
                                publish_place = u'无'
                        publish_place = handle_garbled(publish_place)
                        break
            return publish_place
        except Exception as e:
            logger.exception(e)

    def get_publish_time(self, info):
        """获取微博发布时间"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = handle_garbled(str_time[0])
            publish_time = str_time.split(u'来自')[0]
            if u'刚刚' in publish_time:
                publish_time = datetime.now().strftime('%Y-%m-%d %H:%M')
            elif u'分钟' in publish_time:
                minute = publish_time[:publish_time.find(u'分钟')]
                minute = timedelta(minutes=int(minute))
                publish_time = (datetime.now() -
                                minute).strftime('%Y-%m-%d %H:%M')
            elif u'今天' in publish_time:
                today = datetime.now().strftime('%Y-%m-%d')
                time = publish_time[3:]
                publish_time = today + ' ' + time
                if len(publish_time) > 16:
                    publish_time = publish_time[:16]
            elif u'月' in publish_time:
                year = datetime.now().strftime('%Y')
                month = publish_time[0:2]
                day = publish_time[3:5]
                time = publish_time[7:12]
                publish_time = year + '-' + month + '-' + day + ' ' + time
            else:
                publish_time = publish_time[:16]
            return publish_time
        except Exception as e:
            logger.exception(e)

    def get_publish_tool(self, info):
        """获取微博发布工具"""
        try:
            str_time = info.xpath("div/span[@class='ct']")
            str_time = handle_garbled(str_time[0])
            if len(str_time.split(u'来自')) > 1:
                publish_tool = str_time.split(u'来自')[1]
            else:
                publish_tool = u'无'
            return publish_tool
        except Exception as e:
            logger.exception(e)

    def get_weibo_footer(self, info):
        """获取微博点赞数、转发数、评论数"""
        try:
            footer = {}
            pattern = r'\d+'
            str_footer = info.xpath('div')[-1]
            str_footer = handle_garbled(str_footer)
            str_footer = str_footer[str_footer.rfind(u'赞'):]
            weibo_footer = re.findall(pattern, str_footer, re.M)

            up_num = int(weibo_footer[0])
            footer['up_num'] = up_num

            retweet_num = int(weibo_footer[1])
            footer['retweet_num'] = retweet_num

            comment_num = int(weibo_footer[2])
            footer['comment_num'] = comment_num
            return footer
        except Exception as e:
            logger.exception(e)

    def get_picture_urls(self, info, is_original):
        """获取微博原始图片url"""
        try:
            weibo_id = info.xpath('@id')[0][2:]
            picture_urls = {}
            if is_original:
                original_pictures = self.extract_picture_urls(info, weibo_id)
                picture_urls['original_pictures'] = original_pictures
                if not self.filter:
                    picture_urls['retweet_pictures'] = u'无'
            else:
                retweet_url = info.xpath("div/a[@class='cc']/@href")[0]
                retweet_id = retweet_url.split('/')[-1].split('?')[0]
                retweet_pictures = self.extract_picture_urls(info, retweet_id)
                picture_urls['retweet_pictures'] = retweet_pictures
                a_list = info.xpath('div[last()]/a/@href')
                original_picture = u'无'
                for a in a_list:
                    if a.endswith(('.gif', '.jpeg', '.jpg', '.png')):
                        original_picture = a
                        break
                picture_urls['original_pictures'] = original_picture
            return picture_urls
        except Exception as e:
            logger.exception(e)

    def get_video_url(self, info):
        """获取微博视频url"""
        video_url = u'无'

        weibo_id = info.xpath('@id')[0][2:]
        try:
            video_page_url = ''
            a_text = info.xpath('./div[1]//a/text()')
            if u'全文' in a_text:
                video_page_url = CommentParser(self.cookie,
                                               weibo_id).get_video_page_url()
            else:
                # 来自微博视频号的格式与普通格式不一致，不加 span 层级
                a_list = info.xpath('./div[1]//a')
                for a in a_list:
                    if 'm.weibo.cn/s/video/show?object_id=' in a.xpath(
                            '@href')[0]:
                        video_page_url = a.xpath('@href')[0]
                        break

            if video_page_url != '':
                video_url = to_video_download_url(self.cookie, video_page_url)
        except Exception as e:
            logger.exception(e)

        return video_url

    def is_pinned_weibo(self, info):
        """判断微博是否为置顶微博"""
        kt = info.xpath(".//span[@class='kt']/text()")
        if kt and kt[0] == u'置顶':
            return True
        else:
            return False

    def get_one_weibo(self, info):
        """获取一条微博的全部信息"""
        try:
            weibo = Weibo()
            is_original = self.is_original(info)
            weibo.original = is_original  # 是否原创微博
            if (not self.filter) or is_original:
                weibo.id = info.xpath('@id')[0][2:]
                weibo.content = self.get_weibo_content(info,
                                                       is_original)  # 微博内容
                weibo.article_url = self.get_article_url(info)  # 头条文章url
                picture_urls = self.get_picture_urls(info, is_original)
                weibo.original_pictures = picture_urls[
                    'original_pictures']  # 原创图片url
                if not self.filter:
                    weibo.retweet_pictures = picture_urls[
                        'retweet_pictures']  # 转发图片url
                weibo.video_url = self.get_video_url(info)  # 微博视频url
                weibo.publish_place = self.get_publish_place(info)  # 微博发布位置
                weibo.publish_time = self.get_publish_time(info)  # 微博发布时间
                weibo.publish_tool = self.get_publish_tool(info)  # 微博发布工具
                footer = self.get_weibo_footer(info)
                weibo.up_num = footer['up_num']  # 微博点赞数
                weibo.retweet_num = footer['retweet_num']  # 转发数
                weibo.comment_num = footer['comment_num']  # 评论数
            else:
                weibo = None
                logger.info(u'正在过滤转发微博')
            return weibo
        except Exception as e:
            logger.exception(e)

    def extract_picture_urls(self, info, weibo_id):
        """提取微博原始图片url"""
        try:
            a_list = info.xpath('div/a/@href')
            first_pic = 'https://weibo.cn/mblog/pic/' + weibo_id
            all_pic = 'https://weibo.cn/mblog/picAll/' + weibo_id
            picture_urls = u'无'
            if first_pic in ''.join(a_list):
                if all_pic in ''.join(a_list):
                    preview_picture_list = MblogPicAllParser(
                        self.cookie, weibo_id).extract_preview_picture_list()
                    picture_list = [
                        p.replace('/thumb180/', '/large/')
                        for p in preview_picture_list
                    ]
                    picture_urls = ','.join(picture_list)
                else:
                    if info.xpath('.//img/@src'):
                        for link in info.xpath('div/a'):
                            if len(link.xpath('@href')) > 0:
                                if first_pic in link.xpath('@href')[0]:
                                    if len(link.xpath('img/@src')) > 0:
                                        preview_picture = link.xpath(
                                            'img/@src')[0]
                                        picture_urls = preview_picture.replace(
                                            '/wap180/', '/large/')
                                        break
                    else:
                        logger.warning(
                            u'爬虫微博可能被设置成了"不显示图片"，请前往'
                            u'"https://weibo.cn/account/customize/pic"，修改为"显示"'
                        )
                        sys.exit()
            return picture_urls
        except Exception as e:
            logger.exception(e)
            return u'无'

