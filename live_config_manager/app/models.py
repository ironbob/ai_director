from datetime import datetime
from app import db
from flask import current_app
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

class SimpleApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True)
    app_name = db.Column(db.String(100), nullable=False)
    config_filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_config_content(self):
        if not self.config_filename:
            return None
        try:
            with open(os.path.join(current_app.config['UPLOAD_FOLDER'], self.config_filename), 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError):
            return None

class MessageType(Enum):
    USER_ENTER = "user_enter"     # 用户进入
    USER_FOLLOW = "user_follow"   # 用户关注
    USER_MESSAGE = "user_message" # 用户发言
    USER_GIFT = "user_gift"       # 用户送礼
    USER_ORDER = "user_order"     # 用户下单

@dataclass
class BaseMessage:
    message_id: str
    type: MessageType
    username: str
    timestamp: datetime
    data: dict

    def to_dict(self):
        return asdict(self)

@dataclass
class UserEnterMessage(BaseMessage):
    def __init__(self, username: str):
        super().__init__(
            message_id=str(uuid.uuid4()),
            type=MessageType.USER_ENTER,
            username=username,
            timestamp=datetime.now(),
            data={}
        )

@dataclass
class UserFollowMessage(BaseMessage):
    def __init__(self, username: str):
        super().__init__(
            message_id=str(uuid.uuid4()),
            type=MessageType.USER_FOLLOW,
            username=username,
            timestamp=datetime.now(),
            data={}
        )

@dataclass
class UserMessage(BaseMessage):
    def __init__(self, username: str, content: str):
        super().__init__(
            message_id=str(uuid.uuid4()),
            type=MessageType.USER_MESSAGE,
            username=username,
            timestamp=datetime.now(),
            data={"content": content}
        )

@dataclass
class UserGiftMessage(BaseMessage):
    def __init__(self, username: str, gift_name: str):
        super().__init__(
            message_id=str(uuid.uuid4()),
            type=MessageType.USER_GIFT,
            username=username,
            timestamp=datetime.now(),
            data={
                "gift_name": gift_name,
            }
        )

@dataclass
class UserOrderMessage(BaseMessage):
    def __init__(self, username: str, product_name: str):
        super().__init__(
            message_id=str(uuid.uuid4()),
            type=MessageType.USER_ORDER,
            username=username,
            timestamp=datetime.now(),
            data={
                "product_name": product_name,
            }
        )