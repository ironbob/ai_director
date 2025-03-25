import random
import struct
from typing import List, Optional, Dict
from collections import UserString, defaultdict

from datetime import datetime
from enum import Enum
from typing import Dict, List
from pydantic import BaseModel

class MessageType(str, Enum):
    ENTER = "enter"
    FOLLOW = "follow"
    INTERACT = "interact"
    PURCHASE = "purchase"
    BUY = "buy"

class LiveEvent(BaseModel):
    type: MessageType      # 必须是指定的枚举值
    user_id: str           # 必须是字符串
    event_time: datetime   # 事件发生时间
    data: dict = {}        # 可选字段，默认为空字典

class InteractionResponseMessage:
    def __init__(self, event: LiveEvent, content:str):
        self.event = event
        self.content = content
class ResponseGenerator:
#    {
#     "welcome":[
#         "欢迎{users}来到直播间～点点关注不迷路！",
#         "欢迎{users},点击左上角点点关注",
#         "{users}新来的宝子点关注,今天福利多多，别急着走！今天咱们要讲好货。有想看的抠公屏上。"
        
#     ],
#     "follow":[
#         "感谢{users}的关注，比个心。",
#         "谢谢{users}的关注支持！"
#     ],
#     "warmup":[
#         "家人们有什么问题都可以打在公屏上，主播看到了会第一时间给大家答复的",
#         "姐妹们有什么问题都可以打在公屏上，主播看到了会第一时间给大家答复的"
#     ]
# } 
    def __init__(self, json_list:list):
        self.json_list = json_list
        self.templates = self.merge_json()

    def merge_json(self)->dict:
        merged_dict = {}
        for item in self.json_list:
            for key, value in item.items():
                if key not in merged_dict:
                    merged_dict[key] = value
                else:
                    merged_dict[key] += value
        return merged_dict

    # 关键词回复缓存 {keywords_str: (keys, responses)}
    _keyword_cache: Dict[str, tuple] = {}

    def generate_welcome(self, users: List[str]) -> str:
        """生成欢迎消息"""
        template = random.choice(self.templates["welcome"])
        user_list = self._format_users(users)
        return template.format(users=user_list)

    def generate_follow_thanks(self, followers: List[str]) -> str:
        """生成关注感谢"""
        template = random.choice(self.templates["follow"])
        user_list = self._format_users(followers)
        return template.format(users=user_list)

    def generate_warmup(self, templates: Optional[List[str]] = None) -> str:
        """生成暖场消息"""
        return random.choice(templates or self.WARMUP_TEMPLATES)

    def generate_interaction_response(self, events: List[LiveEvent], keyword_config: Optional[str] = None) -> List[InteractionResponseMessage]:
        """
        生成智能互动回复
        :param event: 包含用户ID和消息内容的交互事件
        :param keyword_config: 格式示例 "包邮|运费:包邮问题|{复述}，{users}，我们包邮|{users}放心拍"
        """
        
        if not keyword_config:
            return []

        # 解析关键词配置
        keys, responses = self._parse_keyword_config(keyword_config)
        ret = []
        users = [e.user_id for e in events]
        usersStr = self._format_users(users)
        # 遍历每个事件
        for event in event:
              # 匹配关键词
            query = event.data.get('text', '') #互动消息内容
            if any(key in query for key in keys):
                template = random.choice(responses)
                msg = InteractionResponseMessage(event=event, content=template.format(
                    复述=query,
                    users=usersStr
                ))
                ret.append(msg)
        return ret

    def _format_users(self, users: List[str]) -> str:
        """格式化用户列表"""
        if len(users) == 1:
            return users[0]
        return f"{'、'.join(users)}"

    def _parse_keyword_config(self, config_str: str) -> tuple:
        """解析关键词配置并缓存"""
        if config_str in self._keyword_cache:
            return self._keyword_cache[config_str]

        try:
            # 分割键和值部分
            key_part, response_part = config_str.split(':', 1)
            keys = [k.strip() for k in key_part.split('|')]
            responses = [r.strip() for r in response_part.split('|')]
            
            # 缓存解析结果
            self._keyword_cache[config_str] = (keys, responses)
            return keys, responses
        except Exception:
            return (), []