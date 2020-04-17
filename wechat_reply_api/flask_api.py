
'''
@author    : wuutiing@outlook.com
@date      : 2020-03-27
@comments  :

'''
import sys
import os
import json
import yaml

from flask_wechatpy import Wechat, wechat_required, oauth
from wechatpy.replies import TextReply, ArticlesReply, create_reply
from flask import Flask, request, session

# from greatest_dialogue_robot import default_pipeline
from rulebased import rulebasedrobot
from dbutil import insert_message, insert_response


config = yaml.load(open('/var/www/flask_api/config.yml'), yaml.Loader)

app = Flask('wechat_reply_api')

app.config['WECHAT_APPID']  = config['WECHAT_APPID']
app.config['WECHAT_SECRET'] = config['WECHAT_SECRET']
app.config['WECHAT_TOKEN']  = config['WECHAT_TOKEN']
app.config['DEBUG']         = config['DEBUG'] # True
# app.config['WECHAT_AES_KEY']= config['WECHAT_AES_KEY']

app.secret_key = config['SECRET_KEY']

wechat = Wechat(app)

@app.route('/api/clear')
def clear():
    if 'wechat_user_id' in session:
        session.pop('wechat_user_id')
    return "ok"


@app.route('/api', methods=['GET', 'POST'])
@wechat_required
def wechat_handler():
    msg = request.wechat_msg
    _uuid = insert_message(msg)
    if msg.type == 'event' and msg.event == 'subscribe':
        reply = TextReply(content='感谢关注！', message=msg)
    elif msg.type == 'text':
        reply_type, reply_txt_or_article = rulebasedrobot(msg)
        if reply_type == 0:
            reply = TextReply(content=reply_txt_or_article, message=msg)
        elif reply_type == 1:
            reply = ArticlesReply(message=msg)
            reply.add_article(reply_txt_or_article)
    elif msg.type == 'image':
        reply = TextReply(content='别这样，你的图片会被我保存的。', message=msg)
    else:
        reply = TextReply(content='仅支持文本、图片消息。', message=msg)
    insert_response(reply, _uuid)
    return reply


@app.route('/api/access_token')
def access_token():
    return "{}".format(wechat.access_token)


# http://localhost/api/get_resp?signature=0d25baea48105d602e08edc88e41c5dba6ab6c91&timestamp=1584876595&nonce=1265369564&echostr=3621918155347062079

if __name__ == '__main__':
    app.run('0.0.0.0', port=80)
