"""
响应模版
"""


class ChatContent:
    """
    对话内容模版
    """
    content: str
    contentType: str
    id: str
    role: str
    status: str

    def __init__(self, content: dict):
        self.__dict__ = content

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)


class QianWenChatResponse:
    """
    对话响应模版
    """
    contentType: str
    contents: list[ChatContent] | None
    msgStatus: str
    msgId: str
    parentMsgId: str
    sessionId: str

    def __init__(self, response: dict):
        packaged_response = {
            "contentType": response["contentType"],
            "contents": [ChatContent(content) for content in response["contents"]] if response.get(
                "contents") else None,
            "msgStatus": response["msgStatus"],
            "msgId": response["msgId"],
            "parentMsgId": response["parentMsgId"],
            "sessionId": response["sessionId"]
        }
        self.__dict__ = packaged_response

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)


class HistoryResponse:
    """
    历史记录响应模版
    """
    sessionId: str
    msgId: str
    msgStatus: str
    parentMsgId: str
    contentType: str
    contents: list[ChatContent] | None
    senderType: str
    createTime: int

    def __init__(self, response: dict):
        packaged_response = {
            "sessionId": response["sessionId"],
            "msgId": response["msgId"],
            "msgStatus": response["msgStatus"],
            "parentMsgId": response["parentMsgId"],
            "contentType": response["contentType"],
            "contents": [ChatContent(content) for content in response["contents"]] if response.get(
                "contents") else None,
            "senderType": response["senderType"],
            "createTime": response["createTime"]
        }
        self.__dict__ = packaged_response

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)


class OrdinaryResponse:
    def __init__(self, response: dict):
        self.__dict__ = response

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self)
