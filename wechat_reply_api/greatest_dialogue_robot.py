'''
@author    : wuutiing@outlook.com
@date      : 2020-03-27
@comments  : 

'''


import re
import time

from dbutil import query
from articles import LATEST_HELP_ARTICLE


TEXT, ARTICLE  = 0, 1


class Pipeline:
    def __init__(self, *cabs):
        self.__callables = []
        for cab in cabs:
            self.__callables.append(cab)
    def __call__(self, txt, **kws):
        txt = txt.lower()
        for cab in self.__callables:
            result = cab(txt, **kws)
            if result:
                return result
    def add_callable(self, cab):
        self.__callables.append(cab)


default_pipeline = Pipeline()

def regist_pipeline(func):
    default_pipeline.add_callable(func)
    return func

@regist_pipeline
def help_interact(txt, **kws):
    if txt in ('互动','help','互动说明','互动帮助'):
        return ARTICLE, LATEST_HELP_ARTICLE

@regist_pipeline
def process_whoami(txt, **kws):
    if txt in ('我是谁', '我的名字'):
        source = kws.get('source', '')
        sql = f'''select regist_name from logeduser where expired=0 and openid='{source}';'''
        info = query(sql)
        if len(info) > 0:
            return TEXT, '我猜你是：{}'.format(info[0][0])
        else:
            return TEXT, '我还不知道，你可以回复\n“我是+<你的微信号或昵称>”\n来让我记住。'

@regist_pipeline
def register_user(txt, **kws):
    if re.match('^我是[\+＋](.+)',txt):
        return TEXT, '收到，你是：{}'.format(re.match('^我是[\+＋](.+)',txt).group(1))

@regist_pipeline
def collect_interact_info(txt, **kws):
    if re.match('^互动[\+＋](.+)',txt):
        return TEXT, '互动收到，你的留言是：{}。谢谢'.format(re.match('^互动[\+＋](.+)',txt).group(1))

@regist_pipeline
def process_whoareyou(txt, **kws):
    if re.findall('(who are you|你是谁|庭哥|wuting|吴庭)',txt):
        return TEXT, '叫我小吴就好'

@regist_pipeline
def process_hello(txt, **kws):
    if re.sub(',|\.|。|，','',txt) in '你好 早上好 晚上好 中午好 hello hi'.split():
        return TEXT, re.sub(',|\.|。|，','',txt)

@regist_pipeline
def the_greatest_ai_reply(txt, **kws):
    return_aux_lookup = {'are': 'am', 'should': 'shall', 'could': 'can'}
    return_pron_lookup = {'i': 'you', 'my': 'your', 'mine': 'yours', 'us': 'you', 'ours': 'yours', 'our': 'your',
        'me': 'you', 'you': 'i', 'yours': 'mine', 'your': 'my', '你': '我', '我': '你'}
    if re.match('你(.+)吗[？\?]+?$', txt):
        content = re.match(r'你(.+)吗[？\?]+?$', txt).group(1)
        content = re.sub('(你|我)', lambda x:return_pron_lookup[x.group(1)], content)
        return TEXT, '我{}!'.format(content)
    elif re.match(r'(are|can|will|should|could) you (.+?)[？\?]+?$', txt):
        aux, content = re.match(r'(are|can|will|should|could) you (.+?)[？\?]+?$', txt).groups()
        content = content+' '
        content = re.sub(' (you|your|yours|me|i|us|my|mine|our|ours) ', lambda x:' '+return_pron_lookup[x.group(1)]+' ', content)
        return TEXT, 'I {} {}!'.format(return_aux_lookup.get(aux, aux), content)




import requests
import json

@regist_pipeline
def tulinghandler(txt, **kws):
    url = 'http://openapi.tuling123.com/openapi/api/v2'
    source = kws.get('source', 'd')
    data = {'reqType': 0,
 'perception': {'inputText': {'text': txt}},
 'userInfo': {'apiKey': 'fb87c0a691a74afda72380890467c1c1',
'userId': source}}
    res = requests.post(url, json=data)
    if res.status_code == 200:
        content = json.loads(res.content)
        try:
            resp = content['results'][0]['values']['text']
            return TEXT, resp
        except:
            return
    else:
        return

@regist_pipeline
def cant_handle_reply(txt, **kws):
    return TEXT, '不要为难我。'

if __name__ == '__main__':
    test_set = [
        '互动帮助',
        'help',
        '我是+李邦德',
        '我是谁',
        '互动+我的答案',
        'who are you?',
        '你是谁',
        '你好',
        'can you speak english, better than i do?',
        '你会说英文吗，说的比我好吗？',
        '哈哈'
    ]
    for txt in test_set:
        print(txt)
        print('\t', default_pipeline(txt))
