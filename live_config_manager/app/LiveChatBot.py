from datetime import datetime
from app import db
from flask import current_app
import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from app.models import BaseMessage, SimpleApp, MessageType
import uuid,random

class LiveChatBot:
    def __init__(self, app_id: str):
        self.app_id = app_id
        self.pending_messages: List[BaseMessage] = []
        self.message_history: List[BaseMessage] = []
        self.last_processed = datetime.now()
        self.unreplied_users = set()
        self.unreplied_messages = []
        
        # 配置
        app = SimpleApp.query.get_or_404(app_id)
        config_content = app.get_config_content() or {}
        
        # 解析配置
        self.welcome_reply: List[str] = config_content.get("welcome", [])
        self.follow_reply: List[str] = config_content.get("follow", [])
        self.warm_up_reply: List[str] = config_content.get("warmup", [])
        
        # 解析关键词回复
        self.keyword_responses: Dict[str, str] = {}
        self.buy_reply: List[str] = config_content.get("buy_reply", [])
        self.gift_reply: List[str] = config_content.get("gift_reply", [])

        for key_reply in config_content.get("key_reply", []):
            if ":" in key_reply:
                keyword, responses = key_reply.split(":", 1)
                # 处理多个可能的回复
                possible_responses = [r.strip() for r in responses.split("|") if r.strip()]
                if possible_responses:
                    self.keyword_responses[keyword.strip()] = possible_responses
        
        self.last_interaction: Optional[datetime] = None
        self.last_warm_up: Optional[datetime] = None
        
    def add_message(self, message: BaseMessage):
        self.pending_messages.append(message)
        
    def should_process(self) -> bool:
        return (datetime.now() - self.last_processed).total_seconds() >= 3
    
    def _get_recent_activity(self) -> List[str]:
        """获取最近活动用户，用于个性化回复"""
        recent_users = set()
        for msg in reversed(self.message_history[-10:]):
            recent_users.add(msg.username)
        return list(recent_users)
    
    def _batch_generate_response(self, messages: List[BaseMessage]) -> List[str]:
        """
        批量处理消息并生成回复，考虑消息合并和上下文关联
        返回响应消息列表
        """
        responses = []
        
        # 按消息类型分组处理
        msg_groups = defaultdict(list)
        for msg in messages:
            msg_groups[msg.type].append(msg)
        
        # 1. 处理用户进入消息 (合并用户)
        enter_users = [msg.username for msg in msg_groups.get(MessageType.USER_ENTER, [])]
        if enter_users:
            if len(enter_users) > 3:  # 如果超过3人，简化为"3位新朋友"的形式
                display_users = f"{len(enter_users)}位新朋友"
            else:
                display_users = "、".join(enter_users)
            
            if self.welcome_reply:
                template = random.choice(self.welcome_reply)
                responses.append(template.replace("{users}", display_users))
            else:
                responses.append(f"欢迎 {display_users} 来到直播间！")

        # 2. 处理关注消息 (合并用户)
        follow_users = [msg.username for msg in msg_groups.get(MessageType.USER_FOLLOW, [])]
        if follow_users:
            if len(follow_users) > 3:
                display_users = f"{len(follow_users)}位新朋友"
            else:
                display_users = "、".join(follow_users)
            
            if self.follow_reply:
                template = random.choice(self.follow_reply)
                responses.append(template.replace("{users}", display_users))
            else:
                responses.append(f"感谢 {display_users} 的关注！比心~")

        # 3. 处理用户发言 (每条都单独处理)
        for msg in msg_groups.get(MessageType.USER_MESSAGE, []):
            content = msg.data["content"].lower()
            replied = False
            
            # 关键词匹配
            for keyword, possible_responses in self.keyword_responses.items():
                if keyword.lower() in content:
                    response = random.choice(possible_responses)
                    # 处理特殊占位符
                    response = response.replace("{复述}", msg.data["content"])
                    response = response.replace("{users}", msg.username)
                    responses.append(response)
                    replied = True
                    break
            
            # 未匹配关键词的默认回复（可根据需要调整）
            if not replied:  
                #记录没有回复的用户信息
                if msg.username not in self.unreplied_users:
                    self.unreplied_users.add(msg.username)
                    self.unreplied_messages.append(msg)

        # 4. 处理送礼消息 (合并同类礼物)
        gift_users = [msg.username for msg in msg_groups.get(MessageType.USER_GIFT, [])]
        if gift_users:
            display_users = "、".join(follow_users[:3])
            if self.gift_reply:
                template = random.choice(self.gift_reply)
                responses.append(template.replace("{users}", display_users))
            

        # 5. 处理订单消息
        order_users = [msg.username for msg in msg_groups.get(MessageType.USER_ORDER, [])]
        if order_users:
            if len(order_users) > 3:
                display_users = f"{len(order_users)}"
            else:
                display_users = "、".join(order_users)
            
            product_names = list(set(
                msg.data["product_name"] for msg in msg_groups.get(MessageType.USER_ORDER, [])
            ))
            
            if len(product_names) == 1:
                responses.append(f"恭喜{display_users}下单{product_names[0]}！")
            else:
                responses.append(f"感谢{display_users}购买多款商品！")

        return responses
    
    def process_messages(self) -> List[str]:
        if not self.should_process() or not self.pending_messages:
            return []
        
        responses = []
        
        # 1. 检查暖场
        if self._should_warm_up():
            responses.append(self._get_warm_up())
            self.last_warm_up = datetime.now()
        
        # 2. 批量处理消息
        batch_responses = self._batch_generate_response(self.pending_messages)
        responses.extend(batch_responses)
        
        # 3. 更新状态
        self.message_history.extend(self.pending_messages)
        self.pending_messages.clear()
        self.last_processed = datetime.now()
        self.last_interaction = datetime.now() if batch_responses else self.last_interaction
    
        return responses
    
    def _should_warm_up(self) -> bool:
        """检查是否需要暖场"""
        if not self.warm_up_reply:
            return False
            
        since_last = (datetime.now() - (self.last_warm_up or datetime.min)).total_seconds()
        since_interaction = (datetime.now() - (self.last_interaction or datetime.min)).total_seconds()
        
        return since_last > 60 and since_interaction > 30
    
    def _get_warm_up(self) -> str:
        """获取暖场消息"""
        # 如果有多个暖场消息，轮换发送
        if len(self.warm_up_reply) > 1:
            msg = self.warm_up_reply.pop(0)
            self.warm_up_reply.append(msg)
            return msg
        return self.warm_up_reply[0]