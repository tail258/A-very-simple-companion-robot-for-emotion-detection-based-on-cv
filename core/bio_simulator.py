import time
import math
import random

class HeartRateSimulator:
    def __init__(self, baseline_bpm=75):
        self.baseline_bpm = baseline_bpm
        self.current_bpm = baseline_bpm
        self.start_time = time.time()
        self.phase = 0.0

    def get_simulated_heart_rate(self):
        """
        模拟心率波动。
        比如：当人紧张时，心率会升高；放松时降低。
        这里我们用一个缓慢的正弦波 + 随机噪声来模拟。
        """
        t = time.time() - self.start_time
        
        # 模拟呼吸性窦性心律不齐 (RSA): 随呼吸周期波动
        # 周期约 5秒 (0.2Hz)
        respiratory_variation = 5 * math.sin(2 * math.pi * 0.2 * t)
        
        # 模拟情绪漂移 (低频趋势)
        emotional_drift = 10 * math.sin(2 * math.pi * 0.05 * t)
        
        # 随机噪声
        noise = random.uniform(-2, 2)
        
        self.current_bpm = self.baseline_bpm + respiratory_variation + emotional_drift + noise
        
        # 限制在合理范围内
        self.current_bpm = max(50, min(140, self.current_bpm))
        
        return self.current_bpm