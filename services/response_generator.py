from datetime import datetime
import random
from config import Config
from schemas import MessageType

class ResponseGenerator:
    WELCOME_TEMPLATES = [
        "欢迎新来的{users}～点个关注不迷路哦！",
        "热烈欢迎{users}加入直播间！喜欢主播的点点关注呀~",
        "看到{users}进来了，开心！关注主播获取最新福利！"
    ]
    
    FOLLOW_TEMPLATES = [
        "感谢{users}的关注，爱你们哟～",
        "{users}的关注收到啦！比心❤️",
        "谢谢{users}的关注支持！"
    ]
    
    PURCHASE_TEMPLATES = [
        "恭喜{users}下单成功！马上安排发货～",
        "感谢{users}的支持！买它买它！",
        "{users}的手速太快啦！已秒杀成功！"
    ]
    
    WARMUP_TEMPLATES = [
        "家人们有什么问题都可以打在公屏上哦～",
        "新来的宝宝点个关注，马上抽奖啦！",
        "有没有想了解的产品？扣1我详细讲解！"
    ]

    @classmethod
    def generate_group_response(cls, event_type: MessageType, users: list) -> str:
        user_list = "、".join(users[:3])
        if len(users) > 3:
            user_list += f"等{len(users)}位小伙伴"
        
        templates = getattr(cls, f"{event_type.upper()}_TEMPLATES")
        return random.choice(templates).format(users=user_list)

    @classmethod
    def generate_warmup(cls) -> str:
        return random.choice(cls.WARMUP_TEMPLATES)