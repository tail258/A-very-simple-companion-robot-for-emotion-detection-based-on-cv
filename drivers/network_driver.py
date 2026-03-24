import zmq
import json
from .interfaces import IMotorController

class NetworkServo(IMotorController):
    def __init__(self, ip="127.0.0.1", port=5555):
        self.context = zmq.Context()
        # REQ (Request) 模式：客户端
        self.socket = self.context.socket(zmq.REQ)
        # 设置超时，防止网络断了导致大脑卡死
        self.socket.setsockopt(zmq.RCVTIMEO, 2000) 
        self.socket.setsockopt(zmq.LINGER, 0)
        
        print(f"[NetworkServo] Connecting to Body at {ip}:{port}...")
        self.socket.connect(f"tcp://{ip}:{port}")
        
        # 缓存当前角度，用于 get_angle 读取
        self.cache = {'yaw': 0.0, 'pitch': 0.0}

    def set_angle(self, axis, angle):
        # 1. 更新本地缓存
        self.cache[axis] = angle
        
        # 2. 构建协议包
        # 注意：为了减少带宽，我们可以优化策略：
        # 这里为了演示，我们每次 set 都发包。
        # 实际生产中，建议把 yaw/pitch 打包在一起发，或者限制发送频率（例如每 30ms 发一次）
        
        # 构造完整的数据包
        payload = {
            "type": "servo",
            "data": {
                "yaw": self.cache['yaw'],
                "pitch": self.cache['pitch']
            }
        }
        
        try:
            # 发送
            self.socket.send_json(payload)
            # 等待回执 (REQ-REP模式必须一问一答)
            _ = self.socket.recv()
        except zmq.error.Again:
            print("[NetworkServo] Warning: Robot Body not responding (Timeout).")
            # 重连策略可以在这里实现
            pass

    def get_angle(self, axis):
        # 直接返回本地缓存，不再去网络查询（太慢）
        return self.cache.get(axis, 0.0)