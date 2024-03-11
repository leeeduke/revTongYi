import typing
import json
import uuid
import logging
import hashlib
import filetype

import requests

from fake_useragent import UserAgent

from . import errors


def gen_request_id() -> str:
    """生成requestId"""
    # uuid无分隔符
    request_id = uuid.uuid4().hex
    return request_id


class Chatbot:
    """通义千问 Chatbot 对象"""

    api_base: str = "https://qianwen.biz.aliyun.com/dialog"

    cookies: dict

    cookies_str: str

    userId: str
    """Current user id"""

    title: str
    """Title of current session"""

    sessionId: str = ""
    """Current session id"""

    parentId: str = "0"
    """Parent msg id"""

    def __init__(
            self,
            cookies: dict = None,
            cookies_str: str = "",
    ):
        self.sessionId = ""
        
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
                    value = it[equ_loc + 1:]
                    self.cookies[key] = value

        logging.debug(self.cookies)

        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "Content-Type": "application/json",
            "Origin": "https://tongyi.aliyun.com",
            "Referer": "https://tongyi.aliyun.com/",
            "User-Agent": UserAgent().chrome,
            "X-Platform": "pc_tongyi",
            "X-Xsrf-Token": self.cookies['XSRF-TOKEN'],
        }

    def _stream_ask(
            self,
            prompt: str,
            parentId: str = "0",
            timeout: int = 60,
            image: bytes = None
    ) -> typing.Generator[dict, None, None]:
        """流式回复

        Args:
            prompt (str): 提问内容
            parentId (str, optional): 父消息id. Defaults to "0".
            timeout (int, optional): 超时时间. Defaults to 60.
            image (bytes, optional): 图片二进制数据. Defaults to None.
        """
        if parentId == "0":
            self.parentId = self.parentId

        headers = self.headers.copy()

        headers['Accept'] = 'text/event-stream'

        data = {
                "action": "next",
                "contents": [
                    {
                        "contentType": "text",
                        "content": prompt,
                        "role": "user"
                    }
                ],
                "mode": "chat",
                "model": "",
                "requestId": gen_request_id(),
                "parentMsgId": parentId,
                "sessionId": self.sessionId,
                "sessionType": "text_chat" if not image else "image_chat",
                "userAction": "chat"
            }

        if image:
            image_link = self.upload_image(image)
            data["contents"].append({
                        "contentType": "image",
                        "content": image_link,
                        "role": "user"
                    })

        resp = requests.post(
            url=self.api_base + "/conversation",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps(data),
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

        logging.debug("done: {}".format(result))

    def _non_stream_ask(
            self,
            prompt: str,
            parentId: str = "0",
            timeout: int = 60,
            image: bytes = None
    ) -> dict:
        """非流式回复

        Args:
            prompt (str): 提问内容
            parentId (str, optional): 父消息id. Defaults to "0".
            timeout (int, optional): 超时时间. Defaults to 60.
            image (bytes, optional): 图片二进制数据. Defaults to None.
        """

        result = {}

        for resp in self._stream_ask(
                prompt,
                parentId,
                timeout,
                image
        ):
            result = resp

        return result

    def ask(
            self,
            prompt: str,
            parentId: str = "0",
            timeout: int = 60,
            stream: bool = False,
            image: bytes = None
    ) -> typing.Union[typing.Generator[dict, None, None], dict]:
        """提问

        Args:
            prompt (str): 提问内容
            parentId (str, optional): 父消息id. Defaults to "0".
            timeout (int, optional): 超时时间. Defaults to 60.
            stream (bool, optional): 是否流式. Defaults to False.
            image (bytes, optional): 图片二进制数据. Defaults to None.
        """

        # 检查session或新建
        # if not self.sessionId:
        #     self.create_session(prompt)

        if stream:
            return self._stream_ask(
                prompt,
                parentId,
                timeout,
                image
            )
        else:
            return self._non_stream_ask(
                prompt,
                parentId,
                timeout,
                image
            )

    def list_session(self) -> list:
        resp = requests.post(
            url=self.api_base + "/querySessionList",
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
            url=self.api_base + "/deleteSession",
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
            url=self.api_base + "/updateSession",
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

    def get_session_history(self, sessionId: str) -> dict:
        resp = requests.post(
            url=self.api_base + "/chat/list",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps({
                "sessionId": sessionId
            })
        )
        if 'success' in resp.json() and resp.json()['success']:
            return resp.json()
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp.json()))

    def _get_upload_token(self) -> dict:
        resp = requests.post(
            url=self.api_base + "/uploadToken",
            headers=self.headers,
            cookies=self.cookies,
            data=json.dumps({})
        )
        if 'success' in resp.json() and resp.json()['success']:
            return resp.json()
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp.json()))

    def _get_download_link(self, upload_token: dict, file_name: str) -> str:
        resp = requests.post(
            url=self.api_base + "/downloadLink",
            headers=self.headers,
            cookies=self.cookies,
            data=json.dumps({
                "dir": upload_token["data"]["dir"],
                "fileKey": file_name,
                "fileType": "image"
            })
        )
        if 'success' in resp.json() and resp.json()['success']:
            return resp.json()["data"]["url"]
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp.json()))

    def upload_image(self, image: bytes) -> str:
        # 类型及名称
        file_type = filetype.guess_mime(image)
        if "image/" not in file_type:
            raise errors.TongYiProtocolError("invalid file")
        file_name = "image-" + hashlib.md5(image).hexdigest() + "." + file_type[6:]

        # 获取上传链接
        upload_token = self._get_upload_token()

        # 上传
        headers = self.headers.copy()
        headers.pop("Content-Type")
        resp = requests.post(
            url=upload_token["data"]["host"] + "/",
            data=None,
            files={
                "OSSAccessKeyId": (None, upload_token["data"]["accessId"]),
                "policy": (None, upload_token["data"]["policy"]),
                "signature": (None, upload_token["data"]["signature"]),
                "key": (None, upload_token["data"]["dir"] + file_name),
                "dir": (None, upload_token["data"]["dir"]),
                "success_action_status": (None, "200"),
                "file": (file_name, image, file_type)
            },
            headers=headers,
            cookies=self.cookies
        )

        if resp.status_code == 200:
            # 获取下载链接
            return self._get_download_link(upload_token, file_name)
        else:
            raise errors.TongYiProtocolError(f"unexpected response: {resp.status_code}")