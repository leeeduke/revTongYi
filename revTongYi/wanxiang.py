# 通义万相
import typing
import json
import uuid
import time
import logging

import requests
from fake_useragent import UserAgent

from . import errors


class Imagebot:

    api_base: str = "https://wanx.aliyun.com/wanx"

    cookies: dict

    cookies_str: str

    def __init__(
        self,
        cookies: dict=None,
        cookies_str: str=""
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
            "referer": "https://wanx.aliyun.com/creation",
            "user-agent": UserAgent().chrome,
            "x-xsrf-token": self.cookies['XSRF-TOKEN'],
        }
    
    def generate_image(
        self,
        prompt: str,
        resolution="1024*1024",
        style="<auto>",
        total_timeout=120
    ) -> list:
        """生成图片
        
        Args:
            prompt (str): 图片描述
            resolution (str, optional): 分辨率. Defaults to "1024*1024", 支持："1280*720", "720*1280"
            style (str, optional): 样式. Defaults to "<auto>", 支持："<watercolor>", "<oil painting>", "<chinese painting>", "<flat illustration>", "<anime>", "<sketch>", "<3d cartoon>"
        """
        resp = requests.post(
            url=self.api_base+"/imageGen",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps({
                "taskType":"text_to_image",
                "taskInput":{
                    "prompt":prompt,
                    "style":style,
                    "resolution":resolution
                }
            }),
            timeout=10
        )

        resp_json = resp.json()

        if 'success' in resp_json and resp_json['success']:
            pass
        else:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp_json))
        
        taskId = resp_json['data']

        resp = requests.post(
            url=self.api_base+"/task/list",
            cookies=self.cookies,
            headers=self.headers,
            data=json.dumps({"taskTypes":["image_variation","style_transfer","text_to_image"]}),
            timeout=10
        )

        if 'success' not in resp.json() or not resp.json()['success']:
            raise errors.TongYiProtocolError("unexpected response: {}".format(resp.json()))
        
        id = resp.json()['data'][0]['id']

        now = int(time.time())
        # 检查结果
        while True:
            if int(time.time()) - now > total_timeout:
                raise TimeoutError

            resp = requests.post(
                url=self.api_base+"/taskResult",
                cookies=self.cookies,
                headers=self.headers,
                data=json.dumps({
                    "id": id,
                    "taskId": taskId
                }),
                timeout=10
            )

            logging.debug("check result: {}".format(resp.json()))

            if 'success' in resp.json() and resp.json()['success']:
                resp_json = resp.json()

                if resp_json['data']['status'] == 2:
                    return resp_json['data']['taskResult']

            time.sleep(1)
