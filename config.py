import os
from datetime import timedelta

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key")
    MESSAGE_INTERVALS = {
        'welcome': timedelta(seconds=30),
        'follow': timedelta(seconds=60),
        'purchase': timedelta(seconds=120)
    }
    WARMUP_TIMEOUT = timedelta(minutes=5)
    PLATFORMS = ['wechat','douyin', 'kuaishou', 'taobao']