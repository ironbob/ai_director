from datetime import datetime, timedelta
from collections import defaultdict
import threading
from xml.dom import ValidationErr
from schemas import MessageType,LiveEvent

class PlatformState:
    def __init__(self):
        self.last_activity = datetime.min
        self.last_messages = {
            'welcome': datetime.min,
            'follow': datetime.min,
            'purchase': datetime.min
        }
        self.pending_events = defaultdict(list)
        self.message_history = []

from collections import deque
from datetime import datetime, timedelta
import threading

class ProcessedMessage:
    def __init__(self, message, response=None):
        self.message = message
        self.response = response
        self.processed_at = datetime.now()

class EnhancedStateManager:
    def __init__(self):
        self._lock = threading.Lock()
        # 待处理消息队列 {platform: {event_type: deque}}
        self.pending_queues = defaultdict(lambda: defaultdict(deque))
        # 已处理历史记录 {platform: deque(maxlen=100)}
        self.history = defaultdict(lambda: deque(maxlen=100))
        
    def add_events(self, platform: str, events: list):
        """添加混合类型事件"""
        with self._lock:
            for event in events:
                try:
                    validated = LiveEvent(**event)
                    self.pending_queues[platform][validated.type].append(validated)
                except ValidationErr:
                    continue

    def get_messages_by_type(self,platform:str, event_type: MessageType, max_count=10) -> list:
        """获取指定类型的消息"""
        with self._lock:
            batch = defaultdict(list)
            while len(batch[event_type]) < max_count:
                if not self.pending_queues[platform][event_type]:
                    break
                batch[event_type].append(
                    self.pending_queues[platform][event_type].popleft()
                )
            return batch

    def get_mixed_batch(self, platform: str, max_per_type=5) -> dict:
        """获取混合类型批处理消息"""
        with self._lock:
            batch = defaultdict(list)
            for event_type in MessageType:
                while len(batch[event_type]) < max_per_type:
                    if not self.pending_queues[platform][event_type]:
                        break
                    batch[event_type].append(
                        self.pending_queues[platform][event_type].popleft()
                    )
            return batch
        
    def mark_processed(self, platform: str, messages: list, response: str):
        with self._lock:
            for msg in messages:
                self.history[platform].append(
                    ProcessedMessage(msg, response)
                )
                
    def get_recent_history(self, platform: str, minutes=10) -> list:
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [m for m in self.history[platform] 
                if m.processed_at > cutoff]