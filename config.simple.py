wx_robot_error = ''
wx_robot_study = ''

feishu_robot_error = ''
feishu_robot_study = ''

feishu_app_id = ''
feishu_app_secret = ''

openai_api_key = ''
gpt_model = 'gpt-3.5-turbo' # 'gpt-4','gpt-3.5-turbo'
openai_proxy = ''
azure_api_key = ''          # azure的api_key，设置了才会启用自动参考图搜索
knowledge_number = 2        # 一次发送几条知识

system_prompt = '你现在是{}领域的专家,你的服务对象为30来岁有三五年工作经验的游戏策划,请在考虑他知识阅历经验的基础上提供服务,请避免太过浅显和太过常见的知识,最好是对他日后工作生活有所帮助的知识.'
user_prompt = '我希望了解一个{}中{}方面的知识点,请你为我提供一段5分钟左右的学习内容,以这个知识点的中英文名称作为开头(第一行只有中英文标题),介绍这个知识点并进行一些举例,讲解他的应用场景和优缺点,并为我提供一条扩展学习的文章(不需要链接)'