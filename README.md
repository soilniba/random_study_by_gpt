# 基于GPT生成的随机知识推送

<details align='left'>
    <summary>制作初衷（点击左边箭头展开）</summary>
    <br />
    <p align='left'>
    <img src='https://user-images.githubusercontent.com/22488208/229341032-0670d4d2-9adb-4998-ac57-76a417356f9e.png' width='800'/>
    <img src='https://user-images.githubusercontent.com/22488208/229341118-f6396f2f-054b-43c0-a7a8-d61782d2aaa8.png' width='800'/>
    <img src='https://user-images.githubusercontent.com/22488208/229341132-229ccd3a-1466-412b-9a53-0dbdbdd1bfb5.png' width='800'/>
    <img src='https://user-images.githubusercontent.com/22488208/229341371-6a194aea-f5e1-4b9d-bd92-b23e41ba6c14.png' width='800'/>
    </p>
</details>

<details align='left'>
    <summary>功能介绍</summary>
    <br />
    <p align='left'>
        定时往飞书、企业微信群里推送相关知识，<br />
        会随机优先选择最近未推送过的知识分类。<br />
        我设置的是在每天[9:45][11:45][13:45][15:45][17:45]这几个摸鱼时间进行推送
    <img src='https://user-images.githubusercontent.com/22488208/229341666-d9d1bd1f-5a81-4be1-b036-980b136f1fd7.png' width='800'/>
    <img src='https://user-images.githubusercontent.com/22488208/229341702-033c8162-fa91-4d86-84c4-d885b76b8053.png' width='800'/>
    <img src='https://user-images.githubusercontent.com/22488208/229341776-ab490359-fd2e-4a4f-ba57-dd4b9f17b74d.png' width='800'/>
    </p>
</details>

 <details align='left'>
    <summary>使用方法</summary>
    <br />
    <details align='left'>
        <summary>  安装python</summary>
        <img src='https://user-images.githubusercontent.com/22488208/229342373-4584b2d1-0c52-4ff2-928b-9c6e55ff1ec9.png' width='800'/>
    </details>
    <details align='left'>
        <summary>安装requirements.txt中的依赖库</summary>
        <img src='https://user-images.githubusercontent.com/22488208/229342052-7b0fbc44-03a3-4b76-b674-6d4a59e8bbfc.png' width='800'/>
    </details>
    <details align='left'>
        <summary>将config.simple.py改名为config.py并打开文件填入配置信息</summary>
        <img src='https://user-images.githubusercontent.com/22488208/229343261-7c280f7b-8ece-4c73-b20b-0775ecd9071a.png' width='800'/>
    </details>
    <details align='left'>
        <summary>手动执行study_with_gpt.py测试效果，或者在vscode中调试是否有异常</summary>
            GPT返回大段文本的时间较长，大概要一分钟左右，请耐心等待
        <img src='https://user-images.githubusercontent.com/22488208/229343838-88d873e6-9f53-425c-b44a-9f4ef5dfd42e.png' width='800'/>
        <img src='https://user-images.githubusercontent.com/22488208/229343974-e5862190-6bf6-4ade-8964-3012d228140b.png' width='800'/>
    </details>
    <details align='left'>
        <summary>设置计划任务执行脚本</summary>
            windows中使用pythonw.exe可以让脚本在后台执行<br />
        <img src='https://user-images.githubusercontent.com/22488208/229343362-0e5a7ce2-f3f4-4128-998e-db6e58e19cbe.png' width='800'/>
    </details>
</details>




