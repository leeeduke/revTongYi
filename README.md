# revTongYi

> 原作者 `xw5xr6` 已销号跑路，现接手维护

[![PyPi](https://img.shields.io/pypi/v/revTongYi.svg)](https://pypi.python.org/pypi/revTongYi)
[![Downloads](https://static.pepy.tech/badge/revTongYi)](https://pypi.python.org/pypi/revTongYi)

阿里通义千问、通义万相 Python逆向API

> **近期更改**
> 
> ### 2024/03/11
> - 添加识图功能。
> - 响应数据格式有变动，请尽快适配。

```bash
pip install revTongYi --upgrade
```

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

### 连续对话

返回值中有个`msgId`，下一次调用`ask`时以`parentId`传入这个值，即可继续对话。

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
