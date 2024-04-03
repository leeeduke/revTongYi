# revTongYi

> 原作者 `xw5xr6` 已销号跑路，现接手维护

[![PyPi](https://img.shields.io/pypi/v/revTongYi.svg)](https://pypi.python.org/pypi/revTongYi)
[![Downloads](https://static.pepy.tech/badge/revTongYi)](https://pypi.python.org/pypi/revTongYi)

阿里通义千问、通义万相 Python逆向API

> **近期更改**
>
> ### 2024/04/03
>  - 修改sessionId判断，优化报错
>
> ### 2024/03/29
> - 以对象封装响应数据，方便使用 
>
> ### 2024/03/11
> - 添加识图功能。
> - 响应数据格式有变动，请尽快适配。

```bash
pip install revTongYi --upgrade
```

> 以下接口的返回值均可在源码或方法的 Type Hints 里查看

## 通义千问 - AI对话

```python
# 非流式模式
import revTongYi.qianwen as qwen

question = "人工智能将对人类社会发展产生什么影响？"

chatbot = qwen.Chatbot(
    cookies=<cookies_dict>  # 以dict形式提供cookies
)
# chatbot = qwen.Chatbot(
#     cookies_str=<cookies_str>  # 您也可以使用字符串形式提供cookies，cookies字符串可以从浏览器的请求头中获取
# )

print(chatbot.ask(prompt=question))
```

```python
# 流式模式
import revTongYi.qianwen as qwen

question = "人工智能将对人类社会发展产生什么影响？"

chatbot = qwen.Chatbot(
    cookies=<cookies_dict>  # 以dict形式提供cookies
)

for resp in chatbot.ask(prompt=question, stream=True):
    print(resp)
```

### 识图对话

```python
# 获取图片二进制的示例
import requests
image_bytes = requests.get("https://avatars.githubusercontent.com/u/152763253").content

chatbot.ask(
    prompt="这是什么？",
    image=image_bytes  # 传入图片的二进制数据，会自动上传给千问
)
```

### 连续对话

返回值中有`msgId`和`sessionId`，下一次调用`ask`时以`parentId`和`sessionId`传入这两个值，即可继续对话。

### 新建对话

调用`ask`时不传入`sessionId`参数或传入空字符串即可。

### 列出会话列表

```python
sessions = chatbot.list_session()
```

### 删除指定会话

```python
chatbot.delete_session(sessionId=<session_id>)
```

### 修改会话标题

```python
chatbot.update_session(sessionId=<session_id>, summary=<new_title>)
```

### 获取会话历史记录

```python
history = chatbot.get_session_history(sessionId=<session_id>)
```


### CLI模式

1. 安装 [Chrome/Edge](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) 或 [Firefox](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/) 上的Cookies Editor插件
2. 前往 https://qianwen.aliyun.com/ 并登录
3. 打开此插件，点击`Export`->`Export as JSON`，将复制的Cookies内容保存到文件`cookies.json`

```bash
python -m revTongYi.__init__
```

## 通义万相 - AI图片生成

```python
import revTongYi.wanxiang as wanx

imagebot = wanx.Imagebot(
    cookies=<cookies_dict>  # 以dict形式提供cookies
)

print(imagebot.generate(prompt="草原"))
# 生成四张图片，downloadUrl为图片下载链接
```
