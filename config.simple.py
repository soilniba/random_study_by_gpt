# 企业微信群机器人的key，只包含最后一段，不包含前面的https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=
wx_robot_error = ''         #出现异常时发送消息的机器人，也是测试机器人，不填就记录到log中
wx_robot_study = ''         #发送消息的机器人，不填会使用error机器人，都不填则不发送

# 飞书群机器人的key，只包含最后一段，不包含前面的https://open.feishu.cn/open-apis/bot/v2/hook/
feishu_robot_error = ''     #出现异常时发送消息的机器人，也是测试机器人，不填就记录到log中
feishu_robot_study = ''     #发送消息的机器人，不填会使用error机器人，都不填则不发送

# 飞书企业应用机器人，不填没法发送图片和音频
feishu_app_id = ''
feishu_app_secret = ''
feishu_group_name = ''  # 群名称，不填没法发送音频，另外还需要上传文件权限

# worktool机器人，https://github.com/gallonyin/worktool
worktool_robot_key = '' # 机器人的key
worktool_robot_group_error = '' # 错误信息的群名
worktool_robot_group_study = '' # 学习信息的群名

# openai api相关信息
openai_api_key = ''         # openai的key，可以使用官方的或者第三方的
gpt_model = 'gpt-3.5-turbo' # 使用模型，推荐使用'gpt-4'，效果有明显提升
openai_proxy = ''           # 第三方api的服务器地址，使用官方api可以不填
azure_api_key = ''          # azure的api_key，设置了才会启用自动参考图搜索，在https://azure.microsoft.com/zh-cn/free/免费申请
knowledge_number = 2        # 每次发送几条知识，推荐两三条比较合适

# 提问prompt，可以根据自己的情况修改
system_prompt = '你现在是{}领域的专家,你的服务对象为30来岁有三五年工作经验的游戏策划,请在考虑他知识阅历经验的基础上提供服务,请避免太过浅显和太过常见的知识,最好是对他日后工作生活有所帮助的知识.'
user_prompt = '我希望了解一个{}中{}方面的知识点,请你为我提供一段5分钟左右的学习内容,以这个知识点的中英文名称作为开头(第一行只有中英文标题),介绍这个知识点并进行一些举例,讲解他的应用场景和优缺点,并为我提供一条扩展学习的文章(不需要链接)'

# azure文本转语音服务的key和地区，可以在https://azure.microsoft.com/zh-cn/free/免费申请
speech_key = ''
service_region = ''