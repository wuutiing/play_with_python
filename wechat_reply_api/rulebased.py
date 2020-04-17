'''
@author    : wuutiing@outlook.com
@date      : 2020-04-01
@comments  : 

'''

import yaml
import re
import importlib


RULE_CONFIG_PATH = '/var/www/flask_api/rules.yml'


class RuleProcessor:
    def __init__(self, config_path):
        self._config_path = config_path
        self._config = yaml.load(open(self._config_path, encoding='utf-8'), yaml.Loader)
        self.__callables = []
        self.__make()
    def __make(self):
        for rule in sorted(self._config.values(),key=lambda x: x.get('prior')):
            if rule['prior'] < 0:
                continue
            if rule['action'] == 'REPLY':
                self.__callables.append(self.__reply_factory(rule))
            elif rule['action'] == 'CALL':
                self.__callables.append(self.__call_factory(rule))
    def __reply_factory(self, rule):
        math_type = rule['matchtype']
        reply_type = rule['replytype']
        pattern = rule['pattern']
        reply = rule['reply']
        if math_type == 'REG':
            def _w(msg):
                txt = msg.content
                fileds = re.findall(r'\{(.+?)\}', reply)
                reg = re.compile(pattern)
                # if m := reg.match(txt)
                m = reg.match(txt)
                if m is not None:
                    kws = {'source': msg.source, 'target': msg.target, 
                        'content': msg.content, 'id': msg.id,
                        'create_time': msg.create_time}
                    field_values = {i:m.group(i) for i in fileds}
                    kws.update(field_values)
                    return reply_type, reply.format(**kws)
        elif math_type == 'STRICT':
            def _w(msg):
                txt = msg.content
                if txt == pattern:return reply_type,reply
        return _w
    def __call_factory(self, rule):
        match_type = rule['matchtype']
        reply_type = rule['replytype']
        pattern = rule['pattern']
        modulename, funcname = rule['handler'].rsplit('.', 1)
        func = getattr(importlib.import_module(modulename), funcname)
        params = rule['params'].split(',') if rule["params"] else []
        if match_type == 'REG':
            def _w(msg):
                txt = msg.content
                reg = re.compile(pattern)
                # if m := reg.match(txt)
                m = reg.match(txt)
                if m is not None:
                    kws = {'source': msg.source, 'target': msg.target, 
                        'content': msg.content, 'id': msg.id,
                        'create_time': msg.create_time}
                    param_values = {}
                    for i in params:
                        try:param_values[i] = m.group(i)
                        except:pass
                    kws.update(param_values)
                    return reply_type, func(**kws)
        elif match_type == 'STRICT':
            def _w(msg):
                txt = msg.content
                if txt == pattern: return reply_type,func()
        return _w
    def __call__(self, txt, *args):
        for cab in self.__callables:
            res = cab(txt)
            if res:
                return res


rulebasedrobot = RuleProcessor(RULE_CONFIG_PATH)


def test():
    class MSG:
        source = 'source-test' # str
        target = 'target-test' # str
        content = '' # str
        id = 123456 #bigint
        create_time = '2020-01-03 18:00:00' #unix时间戳
    msg = MSG()
    for i in ['hello?', '早上好。', '你好！',
            'who are you？', '你是谁',
            '今天北京天气怎么样',
            '帮助', '说明',
            '我是谁',
            '我是+测试账户。',
            '我是谁',
            '互动+我的内容',
            '你会吃饭吗？', 'can you speak english better than i?',
            '聊会天呗',
            '']:
        print(f'【input】{i}')
        msg.content = i
        t, r = rulebasedrobot(msg)
        print(f'【{t}】{r}\n')
