'''
@author    : wuutiing@outlook.com
@date      : 2020-03-13
@comments  : 
# requirements
requests
bs4
pandas

'''

import os
import json
import time
import random
import requests
from queue import Queue, Empty
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import pandas as pd


topic_list_pattern = 'https://www.mobile01.com/topiclist.php?f={topic_id}&sort=topictime&p={page}'
post_content_pattern = 'https://www.mobile01.com/topicdetail.php?f={topic_id}&t={post_id}&p={page}'

USERAGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
    "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
    "Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
    "Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
]

def get_topics():
    '''映射记录在topic_list.txt，现在这边只爬三个主题'''
    return {'638': '時事>台灣新聞', '780': '時事>國際新聞', '781': '時事>兩岸新聞'}

def get_content(url):
    headers = {'User-Agent': random.choice(USERAGENTS)}
    try:
        res = requests.get(url, headers=headers)
    except:
        time.sleep(4)
        res = requests.get(url, headers=headers)
    bs = BeautifulSoup(res.content)
    return bs

def query_list(topic_id, lastdate):
    '''获取所有发布日期大于等于指定日期的帖子链接
    '''
    if os.path.exists('logs/done.csv'):
        done = pd.read_csv('logs/done.csv', header=None, dtype={0: str}, sep='\t')
    else:
        done = pd.DataFrame(columns=[0,1])
    done_dict = done.groupby(0).max()[1].to_dict()
    shall_break = False
    page = 1
    while True:
        time.sleep(1+random.random()) # 睡眠2s以示尊重
        page_content = get_content(topic_list_pattern.format(topic_id=topic_id, page=page))
        table = page_content.find('div', 'l-listTable__tbody')
        posts = table.findAll('div', 'l-listTable__tr', recursive=False)
        for post in posts:
            title, create, _update, resp = post.findAll('div', recursive=False)
            id_ = title.find('a').get('href').split('t=')[-1]
            name = title.text.strip()
            create_date = create.find('div', 'o-fNotes').text.strip()[:10]
            try:
                resp_cnt = int(resp.text.strip())
            except:
                resp_cnt = 0
            if create_date < lastdate:
                shall_break = True
                break
            if (id_ not in done_dict) or (id_ in done_dict and resp_cnt>done_dict[id_]):
                print(f'  assign post: {id_} to worker')
                yield (id_, name, create_date, resp_cnt)
            else:
                print(f'    post: {id_} has been crawled and not updated yet')
        if shall_break:
            break
        page += 1

def serialize_dialogue(page_content):
    dialogues = {}
    dials = page_content.findAll('div', 'l-articlePage')
    for dial in dials:
        try:
            author_id = dial.find('div', 'l-articlePage__author').find('a').get('href').split('id=')[-1]
            author_name = dial.find('div', 'l-articlePage__author').find('a').text.strip()
            content_div = dial.find('div', 'l-articlePage__publish')
            if content_div.find('blockquote'):
                content_div.find('blockquote').replaceWith('') # 删除引用
            content_id = content_div.find('article').get('id')
            content = content_div.find('article').text.strip()
            timesp, ordersp = content_div.find_all('span', 'o-fNotes')[-2:]
            time = timesp.text.strip()
            order = int(ordersp.text.strip().replace('#', ''))
            dialogues[order] = {
                'author_id': author_id,
                'author_name': author_name,
                'content_id': content_id,
                'content': content,
                'time': time,
            }
        except:
            pass
    return dialogues

def query_post_and_save(topic_id, post_info, donequeue):
    post_id, name, create_date, resp_cnt = post_info
    print(' '*4+'running '+post_content_pattern.format(topic_id=topic_id, page=1, post_id=post_id))
    dialogues = {}
    page_content = get_content(
        post_content_pattern.format(topic_id=topic_id, page=1, post_id=post_id))
    tmp = page_content.find('ul', 'l-pagination')
    if tmp is None:
        allpage = 1
    else:
        allpage = int(tmp.findAll('li')[-1].text)
    dialogues.update(serialize_dialogue(page_content))
    for page in range(2, allpage+1):
        page_content = get_content(
            post_content_pattern.format(topic_id=topic_id, page=page, post_id=post_id))
        dialogues.update(serialize_dialogue(page_content))
    tosave = {
        'topic_id': topic_id,
        'post_id': post_id,
        'name': name,
        'create_date': create_date,
        'resp_cnt': resp_cnt,
        'dialogues': dialogues
    }
    with open(f'datas/{topic_id}_{post_id}.json', 'w') as f:
        json.dump(tosave, f, ensure_ascii=False)
    donequeue.put((post_id, resp_cnt))
    

def main(lastdate='2020-01-01'):
    topics = get_topics()
    worker = ThreadPoolExecutor(max_workers=5)
    q = Queue()
    print('>>> assign started.')
    for topic_id, topic_name in topics.items():
        print(f'starting assign topic: {topic_name}')
        for post_info in query_list(topic_id, lastdate):
            worker.submit(query_post_and_save, topic_id, post_info, q)
    print('>>> assign finished.')
    f = open('logs/done.csv', 'a')
    while True:
        try:
            post = q.get(timeout=30)
            f.write(f'{post[0]}\t{post[1]}\n')
            f.flush()
        except Empty:
            print('30s timeout, should press ctrl+c to stop')
        except Exception:
            raise
        
if __name__ == '__main__':
    main()
        
# query_post_and_save(topic_id='37', post_info=('1641668','','','1'), donequeue=Queue())
