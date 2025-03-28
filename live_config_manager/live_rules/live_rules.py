from durable.lang import *
from datetime import datetime, timedelta
import time

# 直播间状态容器
class LiveRoomState:
    def __init__(self):
        self.audience = 0          # 当前观众数
        self.last_question = None  # 最后提问时间
        self.orders = 0            # 累计订单数
        self.active_speech = None  # 当前生效的话术

# 初始化全局状态
live_state = LiveRoomState()

# 规则集定义
with ruleset('live_rules'):
    # ==================== 话术选择规则 ==================== 
    @when_all((m.audience == 0) & (m.type == 'audience_update'))
    def speech_empty(c):
        live_state.active_speech = "话术_无人"
        print(f"[话术] {c.m.audience}人 → {live_state.active_speech}")

    @when_all((m.audience > 0) & (m.audience < 5) & (m.type == 'audience_update'))
    def speech_few(c):
        live_state.active_speech = "话术_少人" 
        print(f"[话术] {c.m.audience}人 → {live_state.active_speech}")

    @when_all((m.audience >=5) & (m.audience <10) & (m.type == 'audience_update'))
    def speech_medium(c):
        live_state.active_speech = "话术_中等人"
        print(f"[话术] {c.m.audience}人 → {live_state.active_speech}")

    @when_all((m.audience >=10) & (m.audience <20) & (m.type == 'audience_update'))
    def speech_many(c):
        live_state.active_speech = "话术_较多人"
        print(f"[话术] {c.m.audience}人 → {live_state.active_speech}")

    @when_all((m.audience >=20) & (m.audience <50) & (m.type == 'audience_update'))
    def speech_crowd(c):
        live_state.active_speech = "话术_多人"
        print(f"[话术] {c.m.audience}人 → {live_state.active_speech}")

    @when_all((m.audience >=50) & (m.audience <100) & (m.type == 'audience_update'))
    def speech_super(c):
        live_state.active_speech = "话术_超多"
        print(f"[话术] {c.m.audience}人 → {live_state.active_speech}")

    @when_all((m.audience >=100) & (m.type == 'audience_update'))
    def speech_mega(c):
        live_state.active_speech = "话术_巨多"
        print(f"[话术] {c.m.audience}人 → {live_state.active_speech}")

    # ==================== 互动暖场规则 ====================
    @when_all(m.type == 'question')
    def record_question(c):
        live_state.last_question = datetime.now()
        print(f"[互动] 收到问题: {c.m.text} (时间: {live_state.last_question.strftime('%H:%M:%S')})")

    # 2分钟无问题触发暖场
    # @when_all(none(+m.type == 'question'), 
    #           timeout(rule='warmup_timer', 
    #                  duration=timedelta(minutes=2).total_seconds()))
    # def trigger_warmup(c):
    #     print(f"[暖场] 已{timedelta(minutes=2)}无互动 → 启动暖场话术")

    # ==================== 下单感谢规则 ==================== 
    @when_all(m.type == 'order')
    def count_order(c):
        live_state.orders += 1
        print(f"[订单] 新增订单，累计: {live_state.orders}")

    @when_all((live_state.orders >= 1) & (live_state.orders <= 3))
    def thanks_1_3(c):
        print(f"[感谢] 当前订单数 {live_state.orders} → 感谢话术(1到3)")
        # 重置计数（根据业务需求选择是否重置）
        # live_state.orders = 0  

    @when_all((live_state.orders >= 4) & (live_state.orders <= 10))
    def thanks_3_10(c):
        print(f"[感谢] 当前订单数 {live_state.orders} → 感谢话术(3到10)")

    @when_all(live_state.orders > 10)
    def thanks_10plus(c):
        print(f"[感谢] 当前订单数 {live_state.orders} → 感谢话术(10plus)")

# ==================== 测试函数 ====================
def test_scenario():
    # 模拟观众变化
    post('live_rules', {'type': 'audience_update', 'audience': 0})   # 触发无人
    post('live_rules', {'type': 'audience_update', 'audience': 3})   # 少人
    post('live_rules', {'type': 'audience_update', 'audience': 15})  # 较多人
    
    # 模拟提问
    post('live_rules', {'type': 'question', 'text': "怎么付款？"})
    
    # 快进2分钟触发暖场（使用虚拟时钟）
    print("\n=== 测试暖场规则 ===")
    # get_host('live_rules').advance_time(120)  # 快进2分钟
    
    # 模拟订单
    print("\n=== 测试订单规则 ===")
    for _ in range(5):
        post('live_rules', {'type': 'order'})
        time.sleep(0.1)  # 模拟事件间隔

if __name__ == "__main__":
    # 运行测试场景
    print("====== 开始直播间规则测试 ======")
    test_scenario()
    print("====== 测试完成 ======")