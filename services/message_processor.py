from datetime import datetime, timedelta
from config import Config
from services.state_manager import EnhancedStateManager
from services.response_generator import ResponseGenerator
from schemas import MessageType


class MixedMessageProcessor:
    def process_mixed_events(self,state:EnhancedStateManager, platform: str) -> list:
        responses = []
        batch = state.get_mixed_batch(platform)
        
        # 处理进入事件
        if batch.get(MessageType.ENTER):
            users = [e.user_id for e in batch[MessageType.ENTER]]
            responses.append(self._generate_welcome(users))
            
        # 处理关注事件
        if batch.get(MessageType.FOLLOW):
            followers = [e.user_id for e in batch[MessageType.FOLLOW]]
            responses.append(self._generate_follow_thanks(followers))
            
        # 处理其他类型...
        
        return responses

    def _generate_welcome(self, users: list) -> dict:
        return {
            "type": "welcome",
            "content": ResponseGenerator.generate_group_response(
                MessageType.ENTER, 
                users[:3]
            ),
            "target_users": users
        }