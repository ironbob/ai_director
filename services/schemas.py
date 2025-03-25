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