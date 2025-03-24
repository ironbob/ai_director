from flask import Flask, request, jsonify
from flask_sock import Sock
from services.schemas import MessageType
from services.state_manager import EnhancedStateManager
from services.message_processor import EnhancedMessageProcessor
import threading
import json

app = Flask(__name__)
sock = Sock(app)
connections = defaultdict(set)
state = EnhancedStateManager()


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


if __name__ == '__main__':
    scheduler = SchedulerService(app)
    scheduler.scheduler.start()
    app.run(port=5000,isDebug=True)