import sys
import os
import json

import revTongYi
from revTongYi import qianwen

cookies_dict = {}

with open("cookies.json") as f:
    l = json.loads(f.read())

    for i in l:
        cookies_dict[i['name']] = i['value']

chatbot = qianwen.Chatbot(
    cookies=cookies_dict
)

print("========= ask =========")
resp = chatbot.ask(
    prompt="你好, 我是Rock",
)

print(resp)

assert resp.contents
print("========= multi round =========")

sessionId = resp.sessionId
msgId = resp.msgId

resp = chatbot.ask(
    prompt="我是谁？",
    parentId=msgId,
    sessionId=sessionId
)

print(resp)

assert 'Rock' in resp.contents[0].content

print("========= get session history =========")

resp = chatbot.get_session_history(sessionId)

print(resp)

print("========= list session =========")
resp = chatbot.list_session()

print(resp)
assert sessionId in [
    d['sessionId'] for d in resp
]

print("========= update session =========")

resp = chatbot.update_session(
    sessionId=sessionId,
    summary="我是Rock"
)

print(resp)

resp = chatbot.list_session()

for d in resp:
    if d['sessionId'] == sessionId:
        assert d['summary'] == "我是Rock"
        break
else:
    assert False

print("========= delete session =========")

resp = chatbot.delete_session(sessionId)

print(resp)

resp = chatbot.list_session()

assert sessionId not in [
    d['sessionId'] for d in resp
]

print("========= end =========")