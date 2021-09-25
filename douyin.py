import os, sys, requests
import json, re, hashlib, time
import configparser
from retrying import retry
from contextlib import closing
from requests_html import AsyncHTMLSession, HTMLSession
from local_file_adapter import LocalFileAdapter
from pprint import pprint
import time
import asyncio
from telethon.sync import TelegramClient, events

from TikTokApi import TikTokApi

api_id = ***
api_hash = '***'
bot_token = '***'
#api = TikTokApi.get_instance()

#!/usr/bin/env python
# encoding: utf-8


ini_text = '''
[设置]
#请用notepad++或者sublimeText编辑，并确保编码类型为GB2312
#用户主页链接可以在抖音用户主页分享-》复制链接，然后粘贴在此，多用户用,分隔（英文状态下的逗号）
用户主页列表=https://v.douyin.com/JWTACSX/,https://v.douyin.com/J76dSXL/,https://v.douyin.com/J76kbWF/
#所有作品保存的根目录
保存目录=./Download/
历史目录=./history/
#用于填充进度条长度，如果进度条过长或过短，可以调整该数值
进度块个数=50
'''
FREEZE_SIGNATURE = None

MOBIE_HEADERS = {
        'Pragma': 'no-cache',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.5',
        'Cache-Control': 'no-cache',
        'TE': 'Trailers',
        'DNT': '1',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/12.0 Mobile/15A372 Safari/604.1'
}

class DouYin:

    def __init__(self):
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'upgrade-insecure-requests': '1',
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        }
        self.config = configparser.ConfigParser()
        self.shared_list = []
        self.history = []
        self.save_path = './Download/'
        self.history_path = './history/'
        self.block_count = 50
        self.current_download_name = ''
        

    def read_config(self):
        if not os.path.exists('设置.ini'):
            print('配置文件不存在，创建默认的配置文件')
            with open('设置.ini', 'a+') as f:
                f.write(ini_text)
            print('创建默认配置文件完成')
        try:
            self.config.read('设置.ini')
            value = self.config.get('设置', '用户主页列表')
            if not value:
                input('-用户主页列表为空，请先配置再重试，按任意键继续')
                exit(0)
            self.shared_list = value.split(',')
            #print('---配置的用户列表为:')
            #for url in self.shared_list:
            #    print(url)
            value = self.config.get('设置', '保存目录')
            if value:
                self.save_path = value
            print('---保存的目录为:' + self.save_path)
            value = self.config.get('设置', '历史目录')
            if value:
                self.history_path = value
            print('---历史目录为:' + self.history_path)
            value = self.config.get('设置', '进度块个数')
            if value:
                self.block_count = int(value)
        except:
            input('读取配置文件失败，请确保配置正确，编码是否为GB2312，请使用SublimeText或NotePad++编辑，按任意键继续')
            exit(0)

    def hello(self):
        print("*" * 50)
        print(' ' * 15 + '抖音下载小助手')
        print(' ' * 5 + '作者: HuangSK  Date: 2021-01-21 13:14')
        print("*" * 50)
        return self

    def remove(self):
        if os.path.exists(self.current_download_name):
            os.remove(self.current_download_name)
 
    def get_signature(self,user_id):
        """获取所需的签名信息
        
        @oaram: user_id
        @return: signature
        """
        
        with HTMLSession() as session:    
            signature_url = 'file:///' + os.getcwd() + os.sep +'signature.html?user_id=' + str(user_id)
            session.mount("file:///", LocalFileAdapter())
            r = session.get(signature_url)
            r.html.arender()
            sign = r.html.find('#signature', first=True)
            r.close()
            return sign.text

        #with AsyncHTMLSession() as session:    
        #    signature_url = 'file:///' + os.getcwd() + os.sep +'signature.html?user_id=' + str(user_id)
        #    session.mount("file:///", LocalFileAdapter())
        #    r = await session.get(signature_url)
        #    await r.html.arender()
        #    sign = r.html.find('#signature', first=True)
        #    r.close()
        #    return sign.text

    def get_video_urls(self, sec_uid, max_cursor,user_id,flg):
        if flg==0:
            user_url_prefix = 'https://www.iesdouyin.com/web/api/v2/aweme/post/?sec_uid={0}&max_cursor={1}&count=50&aid=1128&_signature={2}'
            global FREEZE_SIGNATURE
            signature = self.get_signature(user_id)
            i = 0
            result = []
            has_more = True
            while result == [] and has_more:
                i = i + 1
                sys.stdout.write('---解析视频链接中 正在第 {} 次尝试...\r'.format(str(i)))
                sys.stdout.flush()

                user_url = user_url_prefix.format(sec_uid, max_cursor,signature)
                response = self.get_request(user_url)
                html = json.loads(response.content.decode())
                if  'aweme_list' in html and html['aweme_list'] != []:
                    max_cursor = html['max_cursor']
                    has_more = bool(html['has_more'])
                    result = html['aweme_list']
                elif  'aweme_list' in html:
                    max_cursor = html['max_cursor']
                    has_more = bool(html['has_more'])
    
            nickname = None
            video_list = []
            for item in result:
                if nickname is None:
                    nickname = item['author']['unique_id']+'-['+re.sub(r'[\\/:*?"<>|\r\n]+', '', item['author']['nickname'])+']' if item['author']['unique_id'] else item['author']['short_id']+'-['+re.sub(r'[\\/:*?"<>|\r\n]+', '', item['author']['nickname'])+']'
                    #nickname_old = item['author']['nickname'] if re.sub(r'[\/:*?"<>|]', '', item['author']['nickname']) else None
                if 'video' in item and item['aweme_type'] == 4:
                    video_list.append({
                        'desc': re.sub(r'[\\/:*?"<>|\r\n]+', '', item['desc']) if item['desc'] else '无标题' + item['aweme_id'],
                        'url': item['video']['play_addr']['url_list'][0],
                        'aweme_id': item['aweme_id']
                    })
            return nickname, video_list, max_cursor, has_more
        elif flg==1:
            result=api.user_posts(user_id, sec_uid, count=30, cursor=0)
            nickname = None
            video_list = []
            for item in result:
                if nickname is None:
                    nickname = item['author']['uniqueId']+'-['+re.sub(r'[\\/:*?"<>|\r\n]+', '', item['author']['nickname'])+']' if item['author']['uniqueId'] else item['author']['id']+'-['+re.sub(r'[\\/:*?"<>|\r\n]+', '', item['author']['nickname'])+']'
                    #nickname_old = item['author']['nickname'] if re.sub(r'[\/:*?"<>|]', '', item['author']['nickname']) else None
                if 'video' in item :
                    video_list.append({
                        'desc': re.sub(r'[\\/:*?"<>|\r\n]+', '', item['desc']) if item['desc'] else '无标题' + item['id'],
                        'url': item['video']['play_addr'],
                        'aweme_id': item['id']
                    })
            return nickname, video_list, max_cursor, False

        
 

    #下载视频
    def video_downloader(self, video_url, video_name):
        size = 0
        video_url = video_url.replace('aweme.snssdk.com', 'api.amemv.com')
        requests.adapters.DEFAULT_RETRIES = 5
        with closing(requests.get(video_url, headers=self.headers, stream=True)) as response:
            chunk_size = 1024
            content_size = int(response.headers['content-length'])
            if response.status_code == 200:
                text = '----[文件大小]:%0.2f MB' % (content_size / chunk_size / 1024)
                self.current_download_name = video_name
                with open(video_name, 'wb') as file:
                    for data in response.iter_content(chunk_size=chunk_size):
                        file.write(data)
                        size += len(data)
                        file.flush()
                        done = int(self.block_count * size / content_size)
                        sys.stdout.write('%s [下载进度]:%s%s %.2f%%\r' % (text, '█' * done, ' ' * (self.block_count - done), float(size / content_size * 100)))
                        sys.stdout.flush()
                try:
                    os.rename(video_name, video_name+'.mp4')
                except FileExistsError:
                    os.remove(video_name)
                

 
    @retry(stop_max_attempt_number=3)
    def get_request(self, url, params=None):
        if params is None:
            params = {}
        response = requests.get(url, params=params, headers=self.headers, timeout=10)
        assert response.status_code == 200
        return response
 
    @retry(stop_max_attempt_number=3)
    def post_request(self, url, data=None):
        if data is None:
            data = {}
        response = requests.post(url, data=data, headers=self.headers, timeout=10)
        assert response.status_code == 200
        return response

    def get_user_info(self, url):
        if "v.douyin.com"  in url or "www.iesdouyin.com" in url:
            rsp = self.get_request(url)
            sec_uid = re.search(r'sec_uid=.*?\&', rsp.url).group(0)
            user_id = re.findall(r'/share/user/(\d+)', rsp.url)[0]
            return sec_uid[8:-1],user_id,0
        elif "tiktok.com"  in url:
            rsp = self.get_request(url)
            sec_uid = re.search(r'sec_uid=.*?\&', rsp.url).group(0)
            #user_id = re.findall(r'/share/user/(\d+)', rsp.url)[0]
            user_id = re.search(r'&user_id=.*?\&', rsp.url).group(0)
            return sec_uid[8:-1],user_id[9:-1],1

    def get_history(self,user_id):
        history = []
        history_dir = os.path.join(self.history_path, user_id)
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

 #       if os.path.exists(history_dir):
 #           os.remove(history_dir+'/history.txt')
        with open(history_dir+'/history.txt', 'a+') as f:
            f.seek(0)
            lines = f.readlines()
            for line in lines:
                history.append(line.strip())
            

        return history

    def save_history(self,user_id, title):
        history_dir = os.path.join(self.history_path, user_id)
        with open(history_dir+'/history.txt', 'a+') as f:
            f.write(title.strip() + '\n')
    
    #存取用户信息，因为抖音id和用户名都是可变的
    def save_history_user_info(self, nickname,user_id):
        history_dir = os.path.join(self.history_path, user_id)
        with open(history_dir+'/'+nickname+'.txt', 'a+') as f:
            f.seek(0)
    
    def run(self):
        self.read_config()

        #answer = input('是否确认下载上述链接中的视频? Y/n:')
        #if answer != 'Y' and answer != 'y':
        #    input('取消下载, 按任意键退出')
        #    exit(0)

        ##def handle(msg):
        ##    pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')    # 匹配模式
        ##    url=re.findall(pattern,msg['text'])[0]
        ##    print('正在解析下载 ' + url)
        ##    self.get_video_by_url(url)
        ##MessageLoop(bot, handle).run_as_thread()
        ##while 1:
        ##    time.sleep(10)
        
        #
        client = TelegramClient('boiio', api_id, api_hash).start(bot_token=bot_token)
        @client.on(events.NewMessage)
        async def my_event_handler(event):
            pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')    # 匹配模式
            url=re.findall(pattern,event.message.message)[0]
            print('正在解析下载 ' + url)
            self.get_video_by_url(url)
        client.run_until_disconnected()

        #for url in self.shared_list:
        #    print('正在解析下载 ' + url)
        #    self.get_video_by_url(url)

    def get_video_by_url(self, url):
        max_cursor = 0
        has_more = True
        total_count = 0
        #flg 0是抖音，1是Tiktok
        sec_uid , user_id ,flg= self.get_user_info(url)
        if not sec_uid:
            print('获取sec_uid失败')
            return
        print('---获取sec_uid成功: ' + sec_uid)
 
        
        self.history = self.get_history(user_id)
        print('---uid={0}的用户历史下载共 {1} 个视频'.format(user_id,len(self.history)))

        i = 0

        while has_more:
            nickname, video_list, max_cursor, has_more =self.get_video_urls(sec_uid, max_cursor,user_id,flg)

            i=i+1

            if i==1:
                self.save_history_user_info(nickname,user_id)

            if video_list :
                nickname_dir = os.path.join(self.save_path, nickname)
        
                if not os.path.exists(nickname_dir):
                    os.makedirs(nickname_dir)

                page_count = len(video_list)
                total_count = total_count + page_count
                print('---视频下载中 本页共有{0}个作品 累计{1}个作品 翻页标识:{2} 是否还有更多内容:{3}\r'
                    .format(page_count, total_count, max_cursor, has_more))

                for num in range(page_count):
                    title = video_list[num]['desc']+video_list[num]['aweme_id']
                    title = title.replace('@抖音小助手', '').replace('@抖音小助手', '').strip()
                    print('---正在解析第{0}/{1}个视频链接 [{2}]，请稍后...'.format(num + 1, page_count, title))
        
                    video_path = os.path.join(nickname_dir, title)
                    history_name = nickname + '\\' + title
                    aweme_id = video_list[num]['aweme_id']
                    if aweme_id in self.history:
                        print('---{0} -- 已下载...'.format(history_name))
                        has_more = False
                    else:
                        self.video_downloader(video_list[num]['url'], video_path)
                        self.history.append(aweme_id)
                        self.save_history(user_id,aweme_id)
                    print('\n')
                print('---本页视频下载完成...\r')

 
if __name__ == "__main__":
    app = DouYin()
    try:
        app.hello().run()
    except KeyboardInterrupt:
        app.remove()
        input('\r\n终止下载，按任意键退出。。。')
        exit(0)
