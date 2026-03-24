import pyttsx3

class VoiceEngine:
    def __init__(self):
        # 保持为空，确保线程安全，在 speak 中初始化
        pass

    def speak(self, text, speed=160, volume=1.0, lang="zh"):
        """
        :param text: 要朗读的文本
        :param speed: 语速 (默认160)
        :param volume: 音量 (0.0-1.0)
        :param lang: 语言偏好 "zh" 或 "en"
        """
        try:
            # 1. 临时初始化 (线程安全)
            engine = pyttsx3.init()
            
            # 2. 设置基础参数
            engine.setProperty('rate', speed)
            engine.setProperty('volume', volume)
            
            # 3. 智能选择语音包 (根据语言参数)
            voices = engine.getProperty('voices')
            target_voice = None
            
            # 遍历所有安装的语音
            for v in voices:
                # 打印语音名称以便调试，初次运行建议取消注释
                # print(f"[Debug] Found voice: {v.name}") 
                
                if lang == "zh":
                    # 匹配中文语音 (通常包含 'Chinese', 'Huihui', 'Yaoyao' 等)
                    if "Chinese" in v.name or "Huihui" in v.name:
                        target_voice = v.id
                        break # 找到就停止
                elif lang == "en":
                    # 匹配英文语音 (通常包含 'English', 'David', 'Zira' 等)
                    if "English" in v.name or "David" in v.name:
                        target_voice = v.id
                        break
            
            # 如果找到了匹配的语言，就应用；否则用默认的
            if target_voice:
                engine.setProperty('voice', target_voice)
            
            print(f"[Voice ({lang})]: {text}")
            
            # 4. 朗读
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            
        except Exception as e:
            print(f"[Voice Error]: {e}")