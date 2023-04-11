import os
import io
import re
import csv
import gzip
import json
import time
import urllib
import random
import string
import base64
import psutil
import hashlib
import datetime
import requests
from PIL import Image
from io import BytesIO
from loguru import logger
from revChatGPT.V3 import Chatbot
from requests_toolbelt import MultipartEncoder
import azure.cognitiveservices.speech as speechsdk
from config import *
p = psutil.Process()                                        # 获取当前进程的Process对象
p.nice(psutil.IDLE_PRIORITY_CLASS)                          # 设置进程为低优先级
script_dir = os.path.dirname(os.path.realpath(__file__))    # 获取脚本所在目录的路径
os.chdir(script_dir)                                        # 切换工作目录到脚本所在目录

feishu_token = ''
def GetFeishuToken():
    global feishu_token
    if not feishu_token:
        data = json.dumps({
            "app_id": feishu_app_id,
            "app_secret": feishu_app_secret,
        })
        response = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', data=data)
        responsejson = json.loads(response.text)
        feishu_token = responsejson['tenant_access_token']
    return feishu_token

def send_feishu_robot_audio(chat_id, voice_key):
    headers = {
        'Authorization': f'Bearer {GetFeishuToken()}',
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "receive_id": chat_id,
        "content": json.dumps({
            "file_key": voice_key,
        }),
        "msg_type": "audio"
    })
    # data = json.dumps({
    #     "receive_id": GetFeishuChatsID(),
    #     "content": json.dumps({
    #         "zh_cn": {"content": [
    #             [
    #                 {
    #                     "tag": "media",
    #                     "file_key": voice_key
    #                 },
    #             ]
    #         ]}
    #     }),
    #     "msg_type": "post",
    # })

    # data = json.dumps({
    #     "msg_type": "post",
    #     "content": {
    #         "post": {
    #             "zh_cn": {"content": [
    #                 [
    #                     {
    #                         "tag": "text",
    #                         "text": '测试消息'
    #                     },
    #                     # {
    #                     #     "tag": "media",
    #                     #     "file_key": "file_v2_0dcdd7d9-fib0-4432-a519-41d25aca542j",
    #                     #     "image_key": "img_7ea74629-9191-4176-998c-2e603c9c5e8g"
    #                     # },
    #                 ],
    #                 # [{
    #                 #     "tag": "emotion",
    #                 #     "emoji_type": "SMILE"
    #                 # }]
    #             ]}
    #         }
    #     }
    # })
    # response = requests.post(
    #     f'https://open.feishu.cn/open-apis/bot/v2/hook/{feishu_robot_key}',
    #     headers=headers,
    #     data=data,
    # )
    response = requests.post(
        'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
        headers = headers,
        data = data,
    )
    resp_json = json.loads(response.text)
    if resp_json.get('code') != 0:
        print(resp_json)
    return resp_json

def GetFeishuChatsID():
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {GetFeishuToken()}',
    }
    response = requests.get('https://open.feishu.cn/open-apis/im/v1/chats?user_id_type=open_id&page_size=50', headers=headers)
    responsejson = json.loads(response.text)
    # print(responsejson['data']['items'])
    if responsejson['code'] == 0:
        for item in responsejson['data']['items']:
            if '机器人测试' in item['name']:
                print(item['name'], item['chat_id'])
                return item['chat_id']
        print('未找到表情包群ID')
    else:
        print('数据获取异常', responsejson['msg'])

def UpdateFeishuVoice(voice_output_file_path, voice_duration):
    with open(voice_output_file_path, 'rb') as file:
        bytes_data = file.read()
        form = {
            'file_type': 'opus',
            'file_name': 'voice.opus',
            'duration': str(voice_duration),
            'file': ('voice.opus', io.BytesIO(bytes_data), 'audio/opus'),
        }
        multi_form = MultipartEncoder(form)
        headers = {'Authorization': f'Bearer {GetFeishuToken()}'}
        headers['Content-Type'] = multi_form.content_type
        response = requests.request("POST", "https://open.feishu.cn/open-apis/im/v1/files", headers=headers, data=multi_form)
        logger.debug(response.headers['X-Tt-Logid'])  # for debug or oncall
        logger.debug(response.content)  # Response
        responsejson = json.loads(response.text)
        if responsejson['code'] == 0:
            return responsejson['data']['file_key']
        else:
            print(f'上传音频失败：{response.text}')

voice_key = UpdateFeishuVoice('voice_output_tmp', 116462)
send_feishu_robot_audio(GetFeishuChatsID(), voice_key)

# GetFeishuChatsID()