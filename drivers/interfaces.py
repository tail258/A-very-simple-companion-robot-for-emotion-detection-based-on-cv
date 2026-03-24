from abc import ABC, abstractmethod
import numpy as np

class ICamera(ABC):
    """摄像头抽象基类"""
    @abstractmethod
    def read_frame(self) -> (bool, np.ndarray):
        """返回: (是否成功, 图像帧)"""
        pass

    @abstractmethod
    def release(self):
        """释放资源"""
        pass

class IMotorController(ABC):
    """电机/舵机控制抽象基类"""
    @abstractmethod
    def set_angle(self, axis: str, angle: float):
        """
        axis: 'yaw' (水平摇头) 或 'pitch' (垂直点头)
        angle: 目标角度 (例如 -90 到 90)
        """
        pass

    @abstractmethod
    def get_angle(self, axis: str) -> float:
        """获取当前角度（用于PID反馈）"""
        pass

class IAudioInput(ABC):
    """麦克风抽象基类"""
    @abstractmethod
    def listen(self) -> bytes:
        pass