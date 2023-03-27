import os
import re
import csv
import gzip
import json
import time
import openai
import urllib
import random
import string
import base64
import psutil
import hashlib
import datetime
import requests
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from requests_toolbelt import MultipartEncoder
from config import *
if not openai_api_key:
    print('需要在config.py中设置openai_api_key')
    exit(1)
openai.api_key = openai_api_key
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

def SearchBingImage(text, number):
    # 去除中文字符
    regex = re.compile(
        f'[{re.escape(string.punctuation + string.whitespace + string.digits)}]'
    )
    query = regex.sub('', text)
    if len(query) < 5:
        query = text
    headers = {"Ocp-Apim-Subscription-Key": azure_api_key}
    url = f"https://api.bing.microsoft.com/v7.0/images/search?q={query}&count={number * 2}" #多获取几张避免出现下载不了的图片
    response = requests.get(url, headers=headers)
    data = response.json()
    if "value" in data:
        return DownUpImages(data, number)

def DownUpImages(data, number):
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
                if image_key := UpdateFeishuImage(image_bytes):
                    image_key_list.append(image_key)
            if len(image_key_list) >= number:
                break
        except Exception as e:
            send_error_msg(f"图片下载失败: {url}\n{e}")
    return image_key_list, image_url_list, image_base64_list

def GetFeishuToken():
    data = json.dumps({
        "app_id": feishu_app_id,
        "app_secret": feishu_app_secret,
    })
    response = requests.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', headers=headers, data=data)
    responsejson = json.loads(response.text)
    return responsejson['tenant_access_token']

def UpdateFeishuImage(file):
    url = "https://open.feishu.cn/open-apis/im/v1/images"
    form = {'image_type': 'message',
            'image': (file)}
    multi_form = MultipartEncoder(form)
    headers = {'Authorization': f'Bearer {GetFeishuToken()}'}
    headers['Content-Type'] = multi_form.content_type
    response = requests.request("POST", url, headers=headers, data=multi_form)
    # print(response.headers['X-Tt-Logid'])  # for debug or oncall
    # print(response.content)  # Print Response
    responsejson = json.loads(response.text)
    if responsejson['code'] == 0:
        return responsejson['data']['image_key']
    else:
        send_error_msg('上传图片失败', response.text)

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
    print(text)

def send_message(text, answer_key, image_key_list, image_base64_list):
    # title = '🌻小葵花妈妈课堂开课啦：'
    search_href = f'https://www.google.com/search?q={answer_key}'
    text = re.sub('\n+', '\n', text or '')
    if feishu_robot_key := feishu_robot_study or feishu_robot_error:
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
            images = [
                {
                    "tag": "img",
                    "image_key": image_key,
                }
                for image_key in image_key_list
            ]
            feishu_msg["content"].append(images)
        send_feishu_robot(feishu_robot_key, feishu_msg)
    if wx_robot_key := wx_robot_study or wx_robot_error:
        # wx_msg = f'{title}\n{text}\n[搜索更多相关信息]({search_href})'
        wx_msg = f'{text}\n[搜索更多相关信息]({search_href})'
        send_wx_robot(wx_robot_key, wx_msg)
        for image_base64 in image_base64_list:
            send_wx_robot_image(wx_robot_key, image_base64)

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

    projects = []
    # 从可用项目中随机选出一个未被忽略的项目
    for _ in range(total_subcategories * 2):
        subcategories_key = random.choice(list(categories.keys()))
        subcategories_index = categories[subcategories_key]['index']
        if subcategories_index <= 0 or abs(subcategories_index_max - subcategories_index) >= total_subcategories * 0.6:
            # 为子类别分配一个index
            categories[subcategories_key]['index'] = subcategories_index_max + 1
            subcategories = categories[subcategories_key]['data']
            project_index_max = 0
            total_projects = 0
            for sub2categories_key in subcategories:
                sub2categories = subcategories[sub2categories_key]
                total_projects += len(sub2categories)
                for project_key in sub2categories:
                    # sub2categories[project_key] = 0
                    project_index = sub2categories[project_key]
                    if project_index > project_index_max:
                        project_index_max = project_index
            for _ in range(total_projects * 2):
                sub2categories_key = random.choice(list(subcategories.keys()))
                sub2categories = subcategories[sub2categories_key]
                project_key = random.choice(list(sub2categories.keys()))
                project_index = sub2categories[project_key]
                if project_index <= 0 or abs(project_index_max - project_index) >= total_projects * 0.6:
                    # 为项目分配一个index
                    sub2categories[project_key] = project_index_max + 1
                    projects.append({
                        'subcategorie': subcategories_key,
                        'sub2categorie': sub2categories_key,
                        'project': project_key,
                    })
                    break
        if projects:
            break

    # 将更新后的category.json写回文件
    with open("study_category_expand.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=4)

    return projects



def ask_gpt(project):
    # 设置要发送到API的提示语
    message = [
        {'role': 'system', 'content': f'你现在是{project["subcategorie"]}领域的专家,你的服务对象为30来岁有三五年工作经验的游戏策划,请在考虑他知识阅历经验的基础上提供服务,请避免太过浅显和太过常见的知识,最好是对他日后工作生活有所帮助的知识'},
        {'role': 'user', 'content': f'我希望了解一个{project["sub2categorie"]}中{project["project"]}方面的知识点,请你为我提供一段5分钟左右的学习内容,以这个知识点的中英文名称作为开头,介绍这个知识点并进行一些举例,讲解他的应用场景和优缺点,并为我提供一条扩展学习的文章(不需要链接)'},
    ]
    print(message)
    try:
        response = openai.ChatCompletion.create(
            model = gpt_model,  # 对话模型的名称
            messages = message,
            # max_tokens = 4096,  # 回复最大的字符数
            # temperature = 0.9,  # 值在[0,1]之间，越大表示回复越具有不确定性
            # top_p = 1,
            # frequency_penalty = 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            # presence_penalty = 0.0,  # [-2,2]之间，该值越大则更倾向于产生不同的内容
        )
        print(
            f"""[ChatGPT] reply={response.choices[0]['message']['content']}, total_tokens={response["usage"]["total_tokens"]}"""
        )
        return response.choices[0]['message']['content']
    except Exception as e:
        print(e)
        send_error_msg(f'openai api error:{e}')

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
        for project in random_project():
            print(project)
            for _ in range(10):
                if answer:= ask_gpt(project):
                    answer_key = answer.split('\n')[0]
                    if azure_api_key:
                        image_key_list, image_urls, image_base64_list = SearchBingImage(answer_key, 2)
                    send_message(answer, answer_key, image_key_list, image_base64_list)
                    project['answer'] = answer
                    project['images'] = image_urls
                    project['time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    save_to_csv(project)
                    break