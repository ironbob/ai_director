from apscheduler.schedulers.background import BackgroundScheduler
from services.message_processor import MixedMessageProcessor
from config import Config
from state_manager import EnhancedStateManager
import json

class EnhancedScheduler:
    def __init__(self,state:EnhancedStateManager,connections):
        self.connections = connections
        self.state = state

    def _process_messages(self):
        for platform in Config.PLATFORMS:
            processor = MixedMessageProcessor()
            responses = processor.process_mixed_events(self.state, platform)
            
            for resp in responses:
                # 记录处理历史
                self.state.mark_processed(
                    platform=platform,
                    event_type=resp['type'],
                    users=resp['target_users'],
                    response=resp['content']
                )
                
                # 推送消息
                self.broadcast(platform, {
                    'event_type': resp['type'],
                    'message': resp['content']
                })

    def broadcast(self,platform,type, message):
        for ws in self.connections[platform]:
            ws.send(json.dumps(message))