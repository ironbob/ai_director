from datetime import datetime, timedelta
from config import Config
from services.state_manager import EnhancedStateManager
from services.response_generator import ResponseGenerator
from schemas import MessageType,LiveEvent


class MixedMessageProcessor:
    def process_mixed_events(self,state:EnhancedStateManager, platform: str) -> list:
        responses = []
        #处理交互事件
        interaction_events = state.get_messages_by_type(platform,MessageType.INTERACTION,max_count=1)
        if interaction_events:
            state.remove_events_by_type(platform,MessageType.INTERACTION,interaction_events)
            responses.append(self._generate_interaction_response(interaction_events))
            state.mark_processed(platform,interaction_events)

        # 处理进入事件
        enter_events = state.get_messages_by_type(platform,MessageType.ENTER,max_count=5)
        if enter_events:
            state.remove_events_by_type(platform,MessageType.ENTER,enter_events)
            users = [e.user_id for e in enter_events]
            responses.append(self._generate_welcome(users))
            state.mark_processed(platform,enter_events)
            
        # 处理关注事件
        follow_events = state.get_messages_by_type(platform,MessageType.FOLLOW,max_count=5)
        if follow_events:
            state.remove_events_by_type(platform,MessageType.FOLLOW,follow_events)
            followers = [e.user_id for e in follow_events]
            responses.append(self._generate_follow_thanks(followers))
            state.mark_processed(platform,follow_events)
            
        
        return responses
    

    #感谢关注回复
    def _generate_follow_thanks(self,followers:list) -> dict:
        return {
            "type":"follow_thanks",
            "content":ResponseGenerator.generate_follow_thanks(followers)
        }
    
    #交互回复
    def _generate_interaction_response(self,events:list) -> dict:
        return {
            "type":"interaction",
            "content":ResponseGenerator.generate_interaction_response(events)
        }

    #欢迎回复
    def _generate_welcome(self, users: list) -> dict:
        return {
            "type": "welcome",
            "content": ResponseGenerator.generate_group_response(
                MessageType.ENTER, 
                users[:3]
            ),
            "target_users": users
        }