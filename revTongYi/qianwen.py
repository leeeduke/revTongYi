import typing
import json
import uuid
import logging

import requests

from fake_useragent import UserAgent

from . import errors


def gen_msg_id() -> str:
    """生成msgId"""
    # uuid无分隔符
    msg_id = uuid.uuid4().hex
    return msg_id


class Chatbot:
    """通义千问 Chatbot 对象"""

    api_base: str = "https://qianwen.aliyun.com"

    cookies: dict

    cookies_str: str

    userId: str
    """Current user id"""

    title: str
    """Title of current session"""

    sessionId: str = None
    """Current session id"""

    parentId: str = "0"
    """Parent msg id"""

    def __init__(
        self,
        cookies: dict=None,
        cookies_str: str="",
    ):
        if cookies and cookies_str:
            raise ValueError("cookies和cookies_str不能同时存在")
        

        if cookies:
            self.cookies = cookies
            self.cookies_str = ""
            for key in cookies:
                self.cookies_str += "{}={}; ".format(key, cookies[key])
        elif cookies_str:
            self.cookies_str = cookies_str

            spt = self.cookies_str.split(";")

            self.cookies = {}

            for it in spt:
                it = it.strip()
                if it:
                    equ_loc = it.find("=")
                    key = it[:equ_loc]
                    value = it[equ_loc+1:]
                    self.cookies[key] = value
        
        logging.debug(self.cookies)

        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "content-type": "application/json",
            "referer": "https://qianwen.aliyun.com/chat",
            "user-agent": UserAgent().chrome,
            "x-xsrf-token": self.cookies['XSRF-TOKEN'],
        }

    def create_session(self, firstQuery: str) -> dict:
        """创建会话并自动切换到该会话

        Args:
            firstQuery (str): 首次提问内容
        """
        data = {
            "firstQuery": firstQuery
        }

        resp = requests.post(
            url=self.api_base+"/addSession",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps(data),
            timeout=5
        )

        resp_json = resp.json()

        if 'success' in resp_json and resp_json['success']:
            self.sessionId = resp_json['data']['sessionId']
            self.userId = resp_json['data']['userId']
            self.title = resp_json['data']['summary']

            self.parentId = "0"

            logging.debug("created session: {}".format(resp_json))

            return resp_json
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp_json))
    
    def _stream_ask(
        self,
        prompt: str,
        open_search: bool = False,
        parentId: str="0",
        timeout: int = 17,
    ) -> typing.Generator[dict, None, None]:
        """流式回复

        Args:
            prompt (str): 提问内容
            open_search (bool, optional): 是否开启搜索. Defaults to False.
            parentId (str, optional): 父消息id. Defaults to "0".
            timeout (int, optional): 超时时间. Defaults to 17.
        """
        if parentId == "0":
            self.parentId = self.parentId

        resp = requests.post(
            url=self.api_base+"/conversation",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps({
                "action":"next",
                "msgId":gen_msg_id(),
                "parentMsgId":parentId,
                "contents":[
                    {
                        "contentType":"text",
                        "content":prompt
                    }
                ],
                "timeout":timeout,
                "openSearch":open_search,
                "sessionId":self.sessionId,
                "model":""
            }),
            timeout=timeout,
            stream=True
        )

        index = 0
        pending = ""
        result = {}

        for chunk in resp.iter_lines(decode_unicode=True):
            logging.debug("chunk: {}".format(chunk))
            if chunk:
                index += 1
                chunk = str(chunk).strip()

                pending += chunk

                if not chunk.endswith("}"):
                    # 不完整的chunk
                    continue
                else:
                    # chunk完整
                    try:
                        pending = pending.split("\n")[-1]
                        pending = pending[6:]

                        resp_json = json.loads(pending)

                        pending = ""

                        self.parentId = resp_json["msgId"]

                        result = resp_json

                        yield result
                    except Exception as e:
                        pass

    def _non_stream_ask(
        self,
        prompt: str,
        open_search: bool = False,
        parentId: str="0",
        timeout: int = 17,
    ) -> dict:
        """非流式回复

        Args:
            prompt (str): 提问内容
            open_search (bool, optional): 是否开启搜索. Defaults to False.
            parentId (str, optional): 父消息id. Defaults to "0".
            timeout (int, optional): 超时时间. Defaults to 17.
        """

        result = {}

        for resp in self._stream_ask(
            prompt,
            open_search,
            parentId,
            timeout
        ):
            result = resp

        return result

    def ask(
        self,
        prompt: str,
        parentId: str="0",
        open_search: bool = False,
        timeout: int = 17,
        stream: bool = False,
    ) -> typing.Union[typing.Generator[dict, None, None], dict]:
        """提问

        Args:
            prompt (str): 提问内容
            parentId (str, optional): 父消息id. Defaults to "0".
            open_search (bool, optional): 是否开启搜索. Defaults to False.
            timeout (int, optional): 超时时间. Defaults to 17.
            stream (bool, optional): 是否流式. Defaults to False.
        """

        # 检查session或新建
        if not self.sessionId:
            self.create_session(prompt)

        if stream:
            return self._stream_ask(
                prompt,
                open_search,
                parentId,
                timeout
            )
        else:
            return self._non_stream_ask(
                prompt,
                open_search,
                parentId,
                timeout
            )

    def list_session(self) -> list:
        resp = requests.post(
            url=self.api_base+"/querySessionList",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps({}),
            timeout=10
        )

        resp_json = resp.json()

        if 'success' in resp_json and resp_json['success']:
            return resp_json['data']
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp_json))

    def delete_session(self, sessionId: str) -> dict:
        resp = requests.post(
            url=self.api_base+"/deleteSession",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps({
                "sessionId": sessionId
            }),
            timeout=10
        )

        if 'success' in resp.json() and resp.json()['success']:
            return resp.json()
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp.json()))
    
    def update_session(self, sessionId: str, summary: str) -> dict:
        resp = requests.post(
            url=self.api_base+"/updateSession",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps({
                "sessionId": sessionId,
                "summary": summary
            }),
            timeout=10
        )

        if 'success' in resp.json() and resp.json()['success']:
            return resp.json()
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp.json()))
