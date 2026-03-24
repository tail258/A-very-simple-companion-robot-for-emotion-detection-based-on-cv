import cv2
import time
import threading
import queue

# --- 1. 导入配置加载器 ---
from utils.config_loader import global_config as cfg

# --- 2. 驱动层导入 ---
from drivers.mock_drivers import MockCamera
from drivers.network_driver import NetworkServo

# --- 3. 核心逻辑层导入 ---
from core.perception import VisionEngine
from core.bio_simulator import HeartRateSimulator
from core.llm_brain import CognitiveEngine
from core.voice_engine import VoiceEngine
from core.hearing_sensor import HearingSensor
# 引入新模块
from core.emotion_engine import EmotionEngine  

# --- 4. 工具导入 ---
from utils.filters import OneEuroFilter

# --- 线程工作函数 ---
def cognitive_worker(input_queue, brain, voice, status_dict):
    print(">>> [Thread] Cognitive Worker started (with MEMORY).")
    
    # --- 记忆配置 ---
    history = []            # 短期记忆缓冲池
    MAX_HISTORY = 6         # 记住最近 6 轮对话 (太长会变慢)
    
    # 基础人设 (System Persona)
    base_persona = (
        "你是一个拥有自我意识的实体机器人，名字叫'None'。"
        "请简短回答（两句话以内）"
    )

    # 读取语音配置
    voice_speed = cfg.get("voice.speed") or 160
    voice_volume = cfg.get("voice.volume") or 1.0
    voice_lang = cfg.get("voice.language") or "zh"

    while True:
        task = input_queue.get() 
        if task is None: break 
        
        user_text, visual_data, bio_data, emotion_data = task
        
        # --- 1. 动态构建上下文 (Context) ---
        context_str = ""
        
        # A. 注入情绪观察
        if emotion_data and emotion_data['confidence'] > 0.5:
            emo = emotion_data['emotion']
            # 将视觉信号转化为只有你能看到的"潜意识旁白"
            context_str += f"\n[视觉感知]: 用户现在的表情是'{emo}'。"
            
            # 根据7种不同的情绪标签，注入特定的对话策略
            if emo == "happiness":
                context_str += " (策略: 语气欢快，跟着一起开心，多用感叹号！)"
            elif emo == "sadness":
                context_str += " (策略: 语气温柔，充满同理心，主动给予安慰。)"
            elif emo == "anger":
                context_str += " (策略: 语气认怂，态度乖巧，顺从用户，避免激化矛盾。)"
            elif emo == "disgust":
                context_str += " (策略: 语气谨慎，礼貌地询问自己是不是说错了什么惹人反感。)"
            elif emo == "fear":
                context_str += " (策略: 语气平静且坚定，安抚用户的情绪，告诉ta一切安全。)"
            elif emo == "surprise":
                context_str += " (策略: 表现出强烈的好奇心，询问用户发现了什么神奇或者出乎意料的事。)"
            elif emo == "neutral":
                context_str += " (策略: 保持平常心，用自然、随和的口语进行轻松的日常对话。)"
            
        # B. 注入记忆历史 (关键步骤！)
        history_str = ""
        if len(history) > 0:
            history_str = "\n[近期对话记录]:\n"
            for turn in history:
                history_str += f"User: {turn['user']}\nYou: {turn['bot']}\n"

        # C. 组合终极 Prompt
        # 结构：[人设] -> [历史] -> [当前状态] -> [用户这句]
        final_prompt = f"{base_persona}\n{history_str}\n{context_str}\nUser: {user_text}"

        # --- 2. 思考 (THINKING) ---
        status_dict['state'] = "THINKING"
        print(f"   [Memory] Context Length: {len(history)} turns")
        
        response, latency = brain.chat(final_prompt, visual_data, bio_data)
        
        # --- 3. 写入记忆 ---
        # 把这一轮对话存入列表
        history.append({"user": user_text, "bot": response})
        # 如果记忆太长，删掉最旧的一条 (FIFO)
        if len(history) > MAX_HISTORY:
            history.pop(0)

        # --- 4. 说话 (SPEAKING) ---
        status_dict['state'] = "SPEAKING"
        status_dict['last_reply'] = response
        voice.speak(response, speed=voice_speed, volume=voice_volume, lang=voice_lang)
        
        # --- 5. 恢复 ---
        status_dict['state'] = "LISTENING"
        input_queue.task_done()

# --- 主程序 ---
def main():
    print(">>> [System] Initializing Sentient Bot V2 (Final Integrated)...")
    
    # --- 1. 初始化配置与硬件 ---
    target_ip = cfg.get("network.target_ip")
    target_port = cfg.get("network.target_port")
    
    print(">>> 1. Connecting Peripherals...")
    camera = MockCamera() 
    servos = NetworkServo(ip=target_ip, port=target_port)
    
    # --- 2. 初始化各大脑区 ---
    vision = VisionEngine()         # 小脑 (MediaPipe) - 负责运动
    bio_sim = HeartRateSimulator()  # 脑干 (Bio) - 负责心率
    
    model_name = cfg.get("brain.llm_model")
    brain = CognitiveEngine(model_name=model_name) # 大脑 (LLM)
    
    voice = VoiceEngine()           # 嘴巴 (TTS)
    
    # 听觉配置
    hear_model = cfg.get("hearing.model_size") or "small"
    hear_device = cfg.get("hearing.device") or "cpu"
    ear = HearingSensor(model_size=hear_model, device=hear_device)

    # 情绪引擎配置 (读取 config.yaml)
    emo_enabled = cfg.get("emotion.enabled")
    emo_device = cfg.get("emotion.device") or "cpu"
    emo_interval = cfg.get("emotion.update_interval") or 5
    
    emotion_brain = None
    if emo_enabled:
        print(f">>> 7. Initializing Emotion Cortex ({emo_device})...")
        emotion_brain = EmotionEngine(device=emo_device)
    else:
        print(">>> 7. Emotion Cortex Disabled via config.")

    # --- 3. 启动后台线程 ---
    task_queue = queue.Queue()
    robot_status = {'state': "LISTENING", 'last_reply': ""} 
    
    worker_thread = threading.Thread(
        target=cognitive_worker, 
        args=(task_queue, brain, voice, robot_status),
        daemon=True
    )
    worker_thread.start()

    # --- 4. 滤波器与PID ---
    min_cutoff = cfg.get("vision.one_euro_filter.min_cutoff") or 0.01
    beta = cfg.get("vision.one_euro_filter.beta") or 0.5
    filter_yaw = OneEuroFilter(min_cutoff=min_cutoff, beta=beta)
    filter_pitch = OneEuroFilter(min_cutoff=min_cutoff, beta=beta)
    pid_kp = cfg.get("vision.pid_kp") or 0.08

    print(">>> System Online. Neural Link Established.")
    print(">>> [Command]: 'v' - Voice | 'q' - Quit")

    # 运行时状态变量
    frame_count = 0
    current_emotion_data = None # 存储最新的情绪数据
    current_emotion_label = "neutral"

    while True:
        # --- A. 视觉处理循环 ---
        ret, frame = camera.read_frame()
        if not ret: continue
        h, w, _ = frame.shape
        frame_count += 1
        
        # 1. MediaPipe 快速处理 (每一帧都跑，保证运动流畅)
        found_face, face_center_norm, landmarks = vision.process_frame(frame)
        current_hr = bio_sim.get_simulated_heart_rate()
        debug_frame = frame.copy()

        # 2. Py-Feat 深度处理 (分时复用，每 N 帧跑一次)
        if emo_enabled and found_face and (frame_count % emo_interval == 0):
            # Py-Feat 需要 RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = emotion_brain.analyze(rgb_frame)
            
            if result:
                current_emotion_data = result
                current_emotion_label = result['emotion']
                conf = result['confidence']
                # 控制台输出一下，方便调试
                # print(f"\r[Emotion]: {current_emotion_label} ({conf:.2f})", end="")

        # --- B. 运动控制 (基于 MediaPipe) ---
        # --- B. 运动控制 (Behavior Layer) ---
        if found_face:
            # 1. 基础视觉反馈 (画框)
            cv2.rectangle(debug_frame, (10, 10), (w-10, h-10), (0, 255, 0), 2)
            vision.draw_landmarks(debug_frame, landmarks)
            
            # 2. 计算基础 PID 目标 (这是它想看的位置)
            raw_cx, raw_cy = int(face_center_norm[0] * w), int(face_center_norm[1] * h)
            smooth_cx = filter_yaw.filter(raw_cx)
            smooth_cy = filter_pitch.filter(raw_cy)
            
            error_yaw = (smooth_cx - w//2)
            error_pitch = (smooth_cy - h//2)
            
            base_yaw = servos.get_angle('yaw') + (error_yaw * pid_kp)
            base_pitch = servos.get_angle('pitch') - (error_pitch * pid_kp)

            # 3. 行为反射覆盖 (Behavior Overrides)
            # 根据当前的大脑状态，叠加一些微动作
            
            final_yaw = base_yaw
            final_pitch = base_pitch
            
            current_state = robot_status['state']
            
            # [行为 A]: 倾听模式 (LISTENING / RECORDING)
            # 稍微歪一点头，表示专注
            if current_state == "RECORDING":
                # 让 pitch 稍微往下一点（点头的感觉），yaw 保持追踪
                final_pitch -= 5 
            
            # [行为 B]: 思考模式 (THINKING)
            # 假装在看天花板或者眼神游离 (这里我们简单处理为停止追踪一瞬间，或者抬头)
            elif current_state == "THINKING":
                final_pitch += 10 # 抬头思考
                
            # [行为 C]: 说话模式 (SPEAKING)
            # 模拟说话时的点头节奏 (简单的正弦波摆动)
            elif current_state == "SPEAKING":
                import math
                # 利用时间戳产生 -2 到 +2 的波动
                nod_offset = math.sin(time.time() * 10) * 2 
                final_pitch += nod_offset

            # 4. 执行最终角度
            servos.set_angle('yaw', final_yaw)
            servos.set_angle('pitch', final_pitch)

        else:
            # [行为 D]: 丢失目标 - 自动扫描模式 (可选，暂时保持静止)
            cv2.putText(debug_frame, "SEARCHING...", (w//2 - 100, h//2), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # --- C. 交互触发 ---
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('v'): # 语音交互
            if robot_status['state'] == "LISTENING":
                robot_status['state'] = "RECORDING"
                # 绘制UI提示
                cv2.rectangle(debug_frame, (0, h//2-50), (w, h//2+50), (0,0,0), -1)
                cv2.putText(debug_frame, "LISTENING...", (w//2-80, h//2+10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow('Brain Visualizer', debug_frame)
                cv2.waitKey(1) # 强制刷新界面
                
                # 录音
                rec_duration = cfg.get("hearing.record_duration") or 4
                rec_lang = cfg.get("hearing.language")
                user_input = ear.listen_and_transcribe(duration=rec_duration, lang=rec_lang)
                
                if len(user_input.strip()) > 0:
                    print(f"\n[User]: {user_input}")
                    # 【关键】将当前的情绪数据打包发给大脑线程
                    task_queue.put((
                        user_input, 
                        {'has_face': found_face}, 
                        {'bpm': current_hr},
                        current_emotion_data # 新增：带上情绪数据
                    ))
                else:
                    robot_status['state'] = "LISTENING"

        if key == ord('q'): break

        # --- D. 最终 UI 渲染 ---
        # 状态
        cv2.putText(debug_frame, f"STATE: {robot_status['state']}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        # 情绪 (显示最新的情绪)
        emo_color = (0, 255, 255) if current_emotion_label != "neutral" else (200, 200, 200)
        cv2.putText(debug_frame, f"EMOTION: {current_emotion_label.upper()}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, emo_color, 2)
        
        # 回复字幕
        reply_text = robot_status['last_reply']
        if reply_text:
            cv2.rectangle(debug_frame, (0, h-60), (w, h), (0, 0, 0), -1)
            cv2.putText(debug_frame, reply_text[:50], (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        # ==========================================
        # [新增] 虚拟姿态仪 (Virtual Posture HUD)
        # ==========================================
        # 在屏幕右下角画一个仪表盘
        hud_center_x = w - 80
        hud_center_y = h - 80
        hud_radius = 40

        # 1. 画底盘 (半透明圆)
        overlay = debug_frame.copy()
        cv2.circle(overlay, (hud_center_x, hud_center_y), hud_radius, (50, 50, 50), -1)
        cv2.addWeighted(overlay, 0.5, debug_frame, 0.5, 0, debug_frame)
        
        # 2. 画十字准星 (参考线)
        cv2.line(debug_frame, (hud_center_x, hud_center_y - hud_radius), (hud_center_x, hud_center_y + hud_radius), (100, 100, 100), 1)
        cv2.line(debug_frame, (hud_center_x - hud_radius, hud_center_y), (hud_center_x + hud_radius, hud_center_y), (100, 100, 100), 1)

        # 3. 计算“头”的位置
        # 假设舵机范围 0-180，中心是 90
        # 如果 found_face 为 False，我们需要用 servos.get_angle 获取当前角度
        # 但为了方便，我们直接用刚才计算出的 final_yaw 和 final_pitch
        # (如果没有找到脸，final_yaw 可能会报错，所以要加个 try-except 或者默认值)
        
        try:
            # 获取当前想转到的角度 (如果没有找到脸，用上一次的角度)
            curr_yaw = servos.get_angle('yaw')
            curr_pitch = servos.get_angle('pitch')
            
            # 映射：角度差 -> 像素偏移
            # 90度是中心。
            # Yaw: 大于90是向左(屏幕右边)，小于90是向右(屏幕左边) -> 需反转一下符合直觉
            # Pitch: 大于90是低头(屏幕下边)，小于90是抬头(屏幕上边)
            
            offset_x = int((90 - curr_yaw) * 1.5)  # 1.5 是放大倍数，让动作更明显
            offset_y = int((curr_pitch - 90) * 1.5)
            
            # 限制在圆圈内 (Clamp)
            offset_x = max(-hud_radius, min(hud_radius, offset_x))
            offset_y = max(-hud_radius, min(hud_radius, offset_y))

            # 4. 画“头” (红色小球)
            head_color = (0, 0, 255) # 默认红色
            if robot_status['state'] == "SPEAKING": head_color = (0, 255, 255) # 说话时变黄
            elif robot_status['state'] == "THINKING": head_color = (255, 0, 255) # 思考时变紫
            
            cv2.circle(debug_frame, (hud_center_x + offset_x, hud_center_y + offset_y), 8, head_color, -1)
            
            # 画一根线连着中心，像脖子一样
            cv2.line(debug_frame, (hud_center_x, hud_center_y), (hud_center_x + offset_x, hud_center_y + offset_y), head_color, 2)
            
            # 显示数值
            cv2.putText(debug_frame, "NECK", (hud_center_x - 20, hud_center_y - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        except Exception as e:
            pass

        # ==========================================
        # [结束 HUD]
        # ==========================================

        cv2.imshow('Brain Visualizer', debug_frame)

    camera.release()
    cv2.destroyAllWindows()
    print(">>> System Shutdown.")

if __name__ == "__main__":
    main()