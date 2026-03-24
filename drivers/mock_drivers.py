import cv2
import numpy as np
import time
from .interfaces import ICamera, IMotorController

class MockCamera(ICamera):
    def __init__(self, source=0):
        # 尝试打开本地摄像头，失败则进入“致盲模式”
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            print("[MockCam] Warning: No webcam found. Using dummy noise.")
        else:
            print(f"[MockCam] Webcam {source} initialized.")

    def read_frame(self):
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return True, frame
        # 如果没有摄像头，生成一张随机噪点图模拟“雪花屏”
        dummy_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        return True, dummy_frame

    def release(self):
        if self.cap.isOpened():
            self.cap.release()

class MockServo(IMotorController):
    def __init__(self):
        # 模拟舵机的当前角度状态
        self.current_angles = {'yaw': 0.0, 'pitch': 0.0}
        print("[MockServo] Virtual Servos initialized.")

    def set_angle(self, axis, angle):
        # 在真实硬件中这里会发送串口指令
        # 在模拟器中，我们只打印日志，并更新内部状态
        # 模拟舵机物理运动的延迟（平滑）
        self.current_angles[axis] = angle
        # print(f"[Hardware-Mock] Servo '{axis}' moved to {angle:.2f}°") 
        # 注：为了不刷屏，这行可以注释掉，我们在可视化界面看

    def get_angle(self, axis):
        return self.current_angles.get(axis, 0.0)