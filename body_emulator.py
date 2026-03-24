import zmq
import time
import json

def run_fake_robot():
    context = zmq.Context()
    
    # REP (Reply) 模式：作为服务端，接收指令并回复 "OK"
    # 未来这段代码会运行在树莓派上，监听 0.0.0.0
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555") 
    
    print(">>> [Body Emulator] Virtual Raspberry Pi Online.")
    print(">>> [Network] Listening on port 5555...")
    
    while True:
        try:
            # 1. 接收消息 (阻塞等待)
            message = socket.recv_json()
            
            # 2. 解析协议
            msg_type = message.get("type")
            payload = message.get("data")
            
            # 3. 模拟硬件执行
            if msg_type == "servo":
                # 这里未来会调用真实的舵机库
                yaw = payload.get('yaw', 0)
                pitch = payload.get('pitch', 0)
                # 打印出来证明收到了，模拟舵机动作
                print(f"[Body-Servo]: Moved to Yaw={yaw:.1f}, Pitch={pitch:.1f}")
                
            elif msg_type == "tts":
                text = payload.get('text', "")
                print(f"[Body-Speaker]: Playing audio for text -> '{text[:20]}...'")
            
            # 4. 发送回执 (必须的，否则 ZMQ 客户端会卡死)
            socket.send_string("ACK")
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            # 发生错误也要回执，防止死锁
            socket.send_string("ERR")

if __name__ == "__main__":
    run_fake_robot()