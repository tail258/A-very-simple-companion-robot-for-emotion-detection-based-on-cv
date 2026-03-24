from enum import Enum

# 定义机器人的所有可能状态
class RobotState(Enum):
    IDLE = 0        # 待机/发呆
    TRACKING = 1    # 锁定目标/追踪
    LISTENING = 2   # 倾听用户说话
    THINKING = 3    # 大脑处理中
    SPEAKING = 4    # 正在回答
    SLEEPING = 5    # 省电/休眠

class DecisionMaker:
    def __init__(self):
        self.current_state = RobotState.IDLE
        self.last_interaction_time = 0

    def decide(self, visual_data, audio_active, brain_busy):
        """
        输入：所有感知数据
        输出：下一步的行动指令 (Action)
        """
        # 1. 状态流转逻辑 (State Transitions)
        
        # 如果大脑在思考，强制进入思考状态
        if brain_busy:
            self.current_state = RobotState.THINKING
            return {"action": "look_up", "led": "purple"}

        # 如果正在录音，进入倾听状态
        if audio_active:
            self.current_state = RobotState.LISTENING
            return {"action": "lean_forward", "led": "green"}

        # 如果看到人脸
        if visual_data.get('has_face'):
            # 如果之前在发呆，现在看到了，就变成追踪
            if self.current_state == RobotState.IDLE:
                self.current_state = RobotState.TRACKING
            
            return {"action": "track_face", "target": visual_data['landmarks']}
        
        # 如果啥都没发生
        else:
            self.current_state = RobotState.IDLE
            return {"action": "scan_environment", "led": "blue"}

    def get_state(self):
        return self.current_state