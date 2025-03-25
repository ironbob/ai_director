from xml.etree.ElementTree import fromstring
from flask import Flask, request, jsonify
from flask_sock import Sock
from services.response_generator import ResponseGenerator,LiveEvent,MessageType
from services.state_manager import MultiPlatformStateManager, ResponseMessage
import threading
import json
from config import Config
from typing import List

app = Flask(__name__)
sock = Sock(app)
connections = defaultdict(set)
state = MultiPlatformStateManager()


@app.route('/event', methods=['POST'])
def handle_event():
    data = request.json
    try:
        # 验证数据格式
        platform = data['platform']
        events = data['events']
        
        # 添加事件到处理队列
        state.add_events(platform, events)
        
        return jsonify(
            success=True,
            received=len(events),
            accepted=sum(len(q) for q in state.pending_queues[platform].values())
        )
    except KeyError:
        return jsonify(success=False, error="Invalid request format"), 400


@sock.route('/ws/<platform>')
def ws_connection(ws, platform):
    connections[platform].add(ws)
    try:
        while True:
            ws.receive()  # 保持连接
    finally:
        connections[platform].remove(ws)

def broadcast(platform, message):
    for ws in connections[platform]:
        ws.send(json.dumps(message))

class MixedMessageProcessor:
    def process_mixed_events(self,state:MultiPlatformStateManager, platform: str) -> List[ResponseMessage]:
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
        responseMsgs = ResponseGenerator.generate_interaction_response(events)
        return {
            "type":"interaction",
            "messages": "\n".join(responseMsgs)
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

class SchedulerService:
    def __init__(self,state:MultiPlatformStateManager,connections):
        self.connections = connections
        self.state = state

    def _process_messages(self):
        for platform in Config.PLATFORMS:
            processor = MixedMessageProcessor()
            responses = processor.process_mixed_events(self.state, platform)
            
            # 推送消息
            self.broadcast(platform, {
                'event_type': resp['type'],
                'message': resp['content']
            })

    def broadcast(self,platform,type, message):
        for ws in self.connections[platform]:
            ws.send(json.dumps(message))

if __name__ == '__main__':
    scheduler = SchedulerService(app)
    scheduler.scheduler.start()
    app.run(port=5000,isDebug=True)