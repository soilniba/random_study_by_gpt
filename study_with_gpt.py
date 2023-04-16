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
from pydub import AudioSegment
from revChatGPT.V3 import Chatbot
from requests_toolbelt import MultipartEncoder
import azure.cognitiveservices.speech as speechsdk
from config import *

filename_ext = os.path.basename(__file__)
file_name, file_ext = os.path.splitext(filename_ext)
logger.add(f"{file_name}.log", format="{time} - {level} - {message}", rotation="10 MB", compression="zip")    # 添加日志文件
if not openai_api_key:
    logger.error('需要在config.py中设置openai_api_key')
    exit(1)
# temperature: float = 0.5,         控制结果的随机性，如果希望结果更有创意可以尝试 0.9，或者希望有固定结果可以尝试 0.0
# top_p: float = 1.0,               一个可用于代替 temperature 的参数，对应机器学习中 nucleus sampling（核采样），如果设置 0.1 意味着只考虑构成前 10% 概率质量的 tokens。 通常建议不要同时更改这两者。
chatbot = Chatbot(api_key=openai_api_key, engine=gpt_model, proxy=openai_proxy, temperature = 0.9)
p = psutil.Process()                                        # 获取当前进程的Process对象
p.nice(psutil.IDLE_PRIORITY_CLASS)                          # 设置进程为低优先级
script_dir = os.path.dirname(os.path.realpath(__file__))    # 获取脚本所在目录的路径
os.chdir(script_dir)                                        # 切换工作目录到脚本所在目录

Cookie = ''
user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36'
headers = {
    'User-Agent': user_agent, 
    'Connection': 'close',
    'Cookie': Cookie,
    'Accept-Encoding': 'gzip',
}

def search_bing_image(text, number):
    # 去除中文字符
    regex = re.compile('[^a-zA-Z0-9 ]+')
    query = regex.sub('', text)
    if len(query) < 5:
        query = text
    headers = {"Ocp-Apim-Subscription-Key": azure_api_key}
    url = f"https://api.bing.microsoft.com/v7.0/images/search?q={query}&count={number * 2 + 2}&imageType=Photo&size=Large" #多获取几张避免出现下载不了的图片
    response = requests.get(url, headers=headers)
    data = response.json()
    if response.status_code != 200:
        send_error_msg(f'搜索图片失败: {data}')
        return
    if "value" in data:
        return down_up_images(data, number)

def down_up_images(data, number):
    image_urls = [item["contentUrl"] for item in data["value"]]
    image_key_list = []
    image_base64_list = []
    image_url_list = []
    for url in image_urls:
        try:
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))
            img = img.convert("RGB")  # 转换为RGB模式
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            image_bytes = buffered.getvalue()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            image_md5 = hashlib.md5(image_bytes).hexdigest()
            image_base64_list.append({
                'base64': image_base64,
                'md5': image_md5,
            })
            image_url_list.append(url)
            if feishu_app_id and feishu_app_secret:
                if image_key := update_feishu_image(image_bytes):
                    image_key_list.append(image_key)
            if len(image_key_list) >= number:
                break
        except Exception as e:
            # send_error_msg(f"图片下载失败: {url}\n{e}")
            logger.error(f"图片下载失败: {url}\n{e}")
    return image_key_list, image_url_list, image_base64_list

feishu_token = None
def get_feishu_token():
    global feishu_token
    if not feishu_token:
        data = json.dumps({
            "app_id": feishu_app_id,
            "app_secret": feishu_app_secret,
        })
        response = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', headers=headers, data=data)
        responsejson = json.loads(response.text)
        feishu_token = responsejson.get('tenant_access_token')
    return feishu_token

def get_feishu_chats_id(chat_name):
    feishu_token = get_feishu_token()
    if not feishu_token:
        return
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {feishu_token}',
    }
    response = requests.get('https://open.feishu.cn/open-apis/im/v1/chats?user_id_type=open_id&page_size=50', headers=headers)
    responsejson = json.loads(response.text)
    # print(responsejson['data']['items'])
    if responsejson['code'] == 0:
        for item in responsejson['data']['items']:
            if chat_name in item['name']:
                logger.info(item['name'], item['chat_id'])
                return item['chat_id']
        send_error_msg(f'未找到群[{chat_name}]')
    else:
        send_error_msg('数据获取异常', responsejson['msg'])

def update_feishu_image(file):
    feishu_token = get_feishu_token()
    if not feishu_token:
        return
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    form = {'image_type': 'message',
            'image': (file)}
    multi_form = MultipartEncoder(form)
    headers = {
        'Authorization': f'Bearer {feishu_token}',
        'Content-Type': multi_form.content_type,
    }
    response = requests.request("POST", url, headers=headers, data=multi_form)
    # logger.debug(response.headers['X-Tt-Logid'])  # for debug or oncall
    # logger.debug(response.content)  # Response
    responsejson = json.loads(response.text)
    if responsejson['code'] == 0:
        return responsejson['data']['image_key']
    else:
        send_error_msg('上传图片失败', response.text)

def update_feishu_voice(voice_output_file_path, voice_duration):
    feishu_token = get_feishu_token()
    if not feishu_token:
        return
    with open(voice_output_file_path, 'rb') as file:
        bytes_data = file.read()
        form = {
            'file_type': 'opus',
            'file_name': 'voice.opus',
            'duration': str(int(voice_duration)),
            'file': ('voice.opus', io.BytesIO(bytes_data), 'audio/opus'),
        }
        multi_form = MultipartEncoder(form)
        headers = {
            'Authorization': f'Bearer {feishu_token}',
            'Content-Type': multi_form.content_type,
        }
        response = requests.request("POST", "https://open.feishu.cn/open-apis/im/v1/files", headers=headers, data=multi_form)
        logger.debug(response.headers['X-Tt-Logid'])  # for debug or oncall
        logger.debug(response.content)  # Response
        responsejson = json.loads(response.text)
        if responsejson['code'] == 0:
            return responsejson['data']['file_key']
        else:
            send_error_msg(f'上传音频失败：{response.text}')

# 将Ogg音频数据转换为mp3音频数据
def ogg_to_mp3(voice_output_file_path):
    # 将Ogg数据加载到AudioSegment对象中
    ogg_audio = AudioSegment.from_file(voice_output_file_path, format="ogg")
    # 将AudioSegment对象转换为mp3格式的音频数据
    mp3_audio = ogg_audio.export(format="mp3")
    # 返回mp3格式的音频数据
    return mp3_audio.read()

def upload_voice_file(voice_output_file_path, voice_duration):
    if not voice_file_server:
        return
    if mp3_data := ogg_to_mp3(voice_output_file_path):
        now = datetime.datetime.now() # 获取当前日期和时间
        date_time_str = now.strftime("%Y%m%d%H%M%S")
        filename = f'voice{date_time_str}'
        headers = {"filename": filename}
        files = {'file': (filename, mp3_data, 'audio/mp3')}
        response = requests.post(f'{voice_file_server}/upload', files=files, headers=headers)
        if response.status_code != 200:
            return send_error_msg(f'上传音频失败：{response.text}')
        return f'{voice_file_server}/read/{filename}.mp3'

def send_feishu_robot(feishu_robot_key, feishu_msg):
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": feishu_msg
            }
        }
    })
    response = requests.post(
        f'https://open.feishu.cn/open-apis/bot/v2/hook/{feishu_robot_key}',
        headers=headers,
        data=data,
    )
    return json.loads(response.text)


def send_feishu_robot_audio(chat_id, voice_key):
    feishu_token = get_feishu_token()
    if not feishu_token:
        return
    headers = {
        'Authorization': f'Bearer {feishu_token}',
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "receive_id": chat_id,
        "content": json.dumps({
            "file_key": voice_key,
        }),
        "msg_type": "audio"
    })
    response = requests.post(
        'https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id',
        headers = headers,
        data = data,
    )
    resp_json = json.loads(response.text)
    if resp_json.get('code') != 0:
        send_error_msg(resp_json)
    return resp_json

def send_worktool_robot(robot_key, robot_group_name, markdown_msg):
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://www.apifox.cn)',
        'Content-Type': 'application/json'
    }
    data = json.dumps({
        "socketType": 2,
        "list": [
            {
                "type": 203,
                "titleList": [
                    robot_group_name
                ],
                "receivedContent": markdown_msg
            }
        ]
    })
    response = requests.post(
        f'https://worktool.asrtts.cn/wework/sendRawMessage?robotId={robot_key}',
        headers=headers,
        data=data,
    )
    data = json.loads(response.text)
    if data.get('code') != 200:
        send_error_msg(f'企业微信机器人发送失败: {data}')
    logger.info(response.text)

def send_worktool_robot_file(robot_key, robot_group_name, markdown_msg, file_url, type):
    if not file_url:
        send_worktool_robot(robot_key, robot_group_name, markdown_msg)
        return
    filename = os.path.basename(urllib.parse.urlparse(file_url).path)
    # filetype = os.path.splitext(filename)[1]
    # if filetype in ['.png', '.jpg', '.jpeg']:
    headers = {
        'User-Agent': 'Apifox/1.0.0 (https://www.apifox.cn)',
        'Content-Type': 'application/json'
    }
    data = json.dumps({
    "socketType": 2,
    "list": [
        {
            "type": 218,
            "titleList": [
                robot_group_name
            ],
            "objectName": filename,
            "fileUrl": file_url,
            "fileType": type,
            "extraText": markdown_msg
        }
    ]
    })
    response = requests.post(
        f'https://worktool.asrtts.cn/wework/sendRawMessage?robotId={robot_key}',
        headers=headers,
        data=data,
    )
    data = json.loads(response.text)
    if data.get('code') != 200:
        send_error_msg(f'企业微信机器人发送失败: {data}')
    logger.info(response.text)
    return

def send_wx_robot(wx_robot_key, markdown_msg):
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "msgtype": "markdown", 
        "markdown": { "content": markdown_msg },
    })
    response = requests.post(
        f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={wx_robot_key}',
        headers=headers,
        data=data,
    )

def send_wx_robot_image(wx_robot_key, image_data):
    headers = {
        'Content-Type': 'application/json',
    }
    data = json.dumps({
        "msgtype": "image",
        "image": image_data
    })
    response = requests.post(
        f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={wx_robot_key}',
        headers=headers,
        data=data,
    )

def send_error_msg(text):
    if feishu_robot_error:
        text_msg = text
        feishu_msg = {"content": []}
        feishu_msg["content"].append([
            {
                "tag": "text",
                "text": text_msg
            },
        ])
        send_feishu_robot(feishu_robot_error, feishu_msg)
    if wx_robot_error:
        send_wx_robot(wx_robot_error, text)
    if worktool_robot_key and worktool_robot_group_error:
        send_worktool_robot(worktool_robot_key, worktool_robot_group_error, text)
    logger.error(text)

def send_message(text, answer_key, image_key_list, image_urls, image_base64_list, voice_key, voice_http_url):
    # title = '🌻小葵花妈妈课堂开课啦：'
    search_href = f'https://www.bing.com/search?q={answer_key}'
    text = re.sub('\n+', '\n', text or '')
    if feishu_robot_key := feishu_robot_study:
        feishu_msg = {"content": []}
        # feishu_msg["title"] = title
        feishu_msg["content"].append([
            {
                "tag": "text",
                "text": text
            },
        ])
        feishu_msg["content"].append([
            {
                "tag": "a",
                "text": '搜索更多相关信息',
                "href": search_href
            },
        ])
        if image_key_list:
            feishu_msg["content"].append([
                {
                    "tag": "img",
                    "image_key": image_key,
                }
                for image_key in image_key_list
            ])
        if voice_key:
            send_feishu_robot_audio(get_feishu_chats_id(feishu_group_name), voice_key)
        send_feishu_robot(feishu_robot_key, feishu_msg)
    if wx_robot_key := wx_robot_study:
        # wx_msg = f'{title}\n{text}\n[搜索更多相关信息]({search_href})'
        wx_msg = f'{text}\n[搜索更多相关信息]({search_href})'
        send_wx_robot(wx_robot_key, wx_msg)
        for image_base64 in image_base64_list:
            send_wx_robot_image(wx_robot_key, image_base64)
    if worktool_robot_key:
        if worktool_robot_group_name := worktool_robot_group_study:
            # search_href = urllib.parse.quote(search_href, safe=':/?&=')
            # worktool_msg = f'{text}\n了解更多:{search_href}'
            send_worktool_robot_file(worktool_robot_key, worktool_robot_group_name, None, image_urls[0], 'image')
            send_worktool_robot_file(worktool_robot_key, worktool_robot_group_name, text, voice_http_url, 'audio')

def random_project():
    with open("study_category_expand.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    total_subcategories = len(categories)
    subcategories_index_max = 0
    for subcategories_key in categories.keys():
        subcategories = categories[subcategories_key]['data']
        # categories[subcategories_key]['index'] = 0
        subcategories_index = categories[subcategories_key]['index']
        if subcategories_index > subcategories_index_max:
            subcategories_index_max = subcategories_index

    # 随机选出一个未使用的大类
    for _ in range(total_subcategories * 2):
        subcategories_key = random.choice(list(categories.keys()))
        subcategories_index = categories[subcategories_key]['index']
        if subcategories_index <= 0 or abs(subcategories_index_max - subcategories_index) >= total_subcategories * 0.6:
            categories[subcategories_key]['index'] = subcategories_index_max + 1
            subcategories = categories[subcategories_key]['data']
            sub2categories_key, project_key = random_subcategorie(subcategories)

            # 将更新后的category.json写回文件
            with open("study_category_expand.json", "w", encoding="utf-8") as f:
                json.dump(categories, f, ensure_ascii=False, indent=4)
            return {
                'subcategorie': subcategories_key,
                'sub2categorie': sub2categories_key,
                'project': project_key,
            }

def random_subcategorie(subcategories):
    project_index_max = 0
    total_projects = 0
    # 先遍历一遍project总数和最大index
    for sub2categories_key in subcategories:
        sub2categories = subcategories[sub2categories_key]
        total_projects += len(sub2categories)
        for project_key in sub2categories:
            # sub2categories[project_key] = 0
            project_index = sub2categories[project_key]
            if project_index > project_index_max:
                project_index_max = project_index
    # 再选一个最近未使用的项目
    for _ in range(total_projects * 2):
        sub2categories_key = random.choice(list(subcategories.keys()))
        sub2categories = subcategories[sub2categories_key]
        project_key = random.choice(list(sub2categories.keys()))
        project_index = sub2categories[project_key]
        if project_index <= 0 or abs(project_index_max - project_index) >= total_projects * 0.6:
            sub2categories[project_key] = project_index_max + 1
            return sub2categories_key, project_key

def ask_gpt(project):
    # 设置要发送到API的提示语
    system_prompt_splice = system_prompt.format(project["subcategorie"])
    user_prompt_splice = user_prompt.format(project["sub2categorie"], project["project"])
    message = [
        {'role': 'system', 'content': system_prompt_splice},
        {'role': 'user', 'content': user_prompt_splice},
    ]
    logger.info(message)
    try:
        chatbot.reset(system_prompt=system_prompt_splice)
        reply = chatbot.ask(user_prompt_splice)
        tokens = chatbot.get_token_count()
        logger.info(f"[ChatGPT] reply={reply}, total_tokens={tokens}")
        return reply
    except Exception as e:
        send_error_msg(f'openai api error:{e}')

def text_to_voice(text):
    # 设置语音合成的配置
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    # 注意：语音设置不会覆盖输入 SSML 中的语音元素。
    ssml_format = random.choice(ssml_templete)
    logger.info(f'随机音色{ssml_format}')
    ssml_text = ssml_format.format(text)

    # 设置输出格式为 Ogg48Khz16BitMonoOpus
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat['Ogg48Khz16BitMonoOpus'])

    # 将音频输出配置设置为内存流，而不是文件
    voice_output_file_path = 'voice_output_tmp'
    audio_config = speechsdk.audio.AudioOutputConfig(filename=voice_output_file_path)

    # 使用语音合成器将文本合成为音频流
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_synthesizer.speak_ssml_async(ssml_text).get()

    # 检查合成结果
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        # 获取音频持续时间
        duration = result.audio_duration.total_seconds() * 1000
        logger.info(
            f"成功合成文本 [{text[:10]}] 的语音。音频时长为 {duration} 毫秒"
        )
        return voice_output_file_path, duration
    elif result.reason == speechsdk.ResultReason.Canceled:
        # 如果合成被取消，则记录错误信息
        cancellation_details = result.cancellation_details
        send_error_msg(f"语音合成被取消：{cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            send_error_msg(f"错误详情：{cancellation_details.error_details}")

def save_to_csv(project):
    filename = 'study_answer_save.csv'

    # 如果文件不存在，则创建一个新的空文件
    if not os.path.exists(filename):
        with open(filename, 'w+', newline='', encoding='utf-8') as f:
            pass

    # 打开CSV文件，使用追加模式
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['time', 'subcategorie', 'sub2categorie', 'project', 'answer', 'images'])
        # 如果文件是空的，则先写入表头
        if os.path.getsize(filename) == 0:
            writer.writeheader()
        writer.writerow(project)  # 追加数据

if __name__ == '__main__':
    for _ in range(knowledge_number):
        project = random_project()
        logger.info(project)
        for _ in range(5):
            if answer:= ask_gpt(project):
                answer_key = answer.split('\n')[0]
                voice_key = None
                voice_http_url = None
                if azure_api_key:
                    image_key_list, image_urls, image_base64_list = search_bing_image(answer_key, 2) or (None, [], None)
                if speech_key and service_region:
                    voice_output_file_path, voice_duration = text_to_voice(answer) or (None, None)
                    if voice_output_file_path and voice_duration:
                        voice_key = update_feishu_voice(voice_output_file_path, voice_duration)
                        voice_http_url = upload_voice_file(voice_output_file_path, voice_duration)
                send_message(answer, answer_key, image_key_list, image_urls, image_base64_list, voice_key, voice_http_url)
                project['answer'] = answer
                project['images'] = image_urls
                project['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                save_to_csv(project)
                break
            time.sleep(10)
