import requests
import json
import time

class CognitiveEngine:
    def __init__(self, model_name="llama3", host="http://localhost:11434"):
        self.model = model_name
        self.host = host
        self.history = [] #以此保存简短的对话历史
        
        # 定义机器人的基础人设
        self.system_persona = (
            "You are 'Sentient', an advanced emotional support robot. "
            "You are concise, empathetic, and observant. "
            "Your responses should be short (under 2 sentences). "
            "Current goal: Monitor the user's wellbeing."
        )

    def _generate_context_prompt(self, visual_data, bio_data):
        """
        【核心逻辑】Prompt 动态注入中间件
        将传感器数据转化为自然语言描述
        """
        context_lines = []
        
        # 1. 视觉上下文
        if visual_data['has_face']:
            context_lines.append(f"[Visual]: User is present and looking at the screen.")
        else:
            context_lines.append(f"[Visual]: User is NOT looking at the screen / Face not visible.")
            
        # 2. 生理上下文 (心率)
        bpm = bio_data['bpm']
        if bpm > 100:
            context_lines.append(f"[Bio-Signal]: User's Heart Rate is HIGH ({int(bpm)} BPM). They might be stressed or excited.")
        elif bpm < 65:
            context_lines.append(f"[Bio-Signal]: User's Heart Rate is LOW ({int(bpm)} BPM). They are relaxed or tired.")
        else:
            context_lines.append(f"[Bio-Signal]: User's Heart Rate is NORMAL ({int(bpm)} BPM).")

        return "\n".join(context_lines)

    def chat(self, user_input, visual_data, bio_data):
        """
        发送请求给 Ollama
        """
        # 1. 动态生成当前的 System Prompt
        current_context = self._generate_context_prompt(visual_data, bio_data)
        full_system_prompt = f"{self.system_persona}\n\n== REAL-TIME SENSOR DATA ==\n{current_context}"
        
        print(f"\n[Thinking] Context Injected: {current_context}")

        # 2. 构建消息体
        messages = [
            {"role": "system", "content": full_system_prompt},
        ]
        # 添加历史 (简单做，只保留最近2轮以免Context过长)
        messages.extend(self.history[-4:]) 
        messages.append({"role": "user", "content": user_input})

        # 3. 调用 Ollama API
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

        try:
            start_t = time.time()
            response = requests.post(f"{self.host}/api/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            
            bot_reply = result['message']['content']
            latency = time.time() - start_t
            
            # 更新历史
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": bot_reply})
            
            return bot_reply, latency

        except Exception as e:
            return f"[Error]: Brain connection failed - {str(e)}", 0