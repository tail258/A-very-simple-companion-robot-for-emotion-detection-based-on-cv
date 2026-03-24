import math
import time

class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        """
        One-Euro Filter: 专为减少抖动和延迟而设计
        :param min_cutoff: 最小截止频率 (Hz)。越小越平滑，但延迟越高。推荐 1.0
        :param beta: 速度系数。越大，快速运动时延迟越低（但也越容易抖）。推荐 0.007
        :param d_cutoff: 导数截止频率。通常设为 1.0
        """
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    def smoothing_factor(self, t_e, cutoff):
        r = 2 * math.pi * cutoff * t_e
        return r / (r + 1)

    def exponential_smoothing(self, a, x, x_prev):
        return a * x + (1 - a) * x_prev

    def filter(self, x, t=None):
        """
        输入当前的测量值 x，返回滤波后的值
        """
        if t is None:
            t = time.time()
            
        if self.x_prev is None:
            self.x_prev = x
            self.t_prev = t
            return x

        t_e = t - self.t_prev
        
        # 避免除以零（极高频调用时）
        if t_e <= 0.0:
            return self.x_prev

        # 1. 计算信号的变化率（导数）
        a_d = self.smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = self.exponential_smoothing(a_d, dx, self.dx_prev)

        # 2. 动态调整截止频率
        # 速度越快 (abs(dx_hat) 越大)，cutoff 越高 -> 滤波越弱 -> 延迟越低
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)

        # 3. 对信号本身进行滤波
        a = self.smoothing_factor(t_e, cutoff)
        x_hat = self.exponential_smoothing(a, x, self.x_prev)

        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat