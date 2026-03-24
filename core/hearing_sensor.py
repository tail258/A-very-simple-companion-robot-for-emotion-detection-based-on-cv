import pyaudio
import wave
import os
import time
from faster_whisper import WhisperModel

class HearingSensor:
    def __init__(self, model_size="small", device="cuda"):
        print(f">>> [Hearing] Loading Whisper model '{model_size}' on {device}...")
        
        # 【架构师修复 1】智能选择精度，防止 CPU 报错
        # 如果是 cuda，用 float16 (快)；如果是 cpu，必须用 int8 (兼容性好)
        compute_type = "float16" if device == "cuda" else "int8"
        
        try:
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            print(f">>> [Hearing] Model loaded ({compute_type}). Ear is open.")
        except Exception as e:
            print(f">>> [Hearing Error] Failed to load model: {e}")
            # 如果 CUDA 失败，自动回退到 CPU (可选保险措施)
            if device == "cuda":
                print(">>> [Hearing] Fallback to CPU...")
                self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

        # 录音参数
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000 # Whisper 喜欢 16k 采样率

    # 【架构师修复 2】增加 lang 参数
    def listen_and_transcribe(self, duration=4, lang="zh"):
        """
        阻塞式录音：录制 duration 秒，然后转录。
        :param lang: 强制指定语言 ("zh", "en") 或 None (自动识别)
        """
        p = pyaudio.PyAudio()
        
        # 1. 开始录音
        print(f">>> [Hearing] Listening for {duration}s...")
        try:
            stream = p.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK)
            
            frames = []
            for i in range(0, int(self.RATE / self.CHUNK * duration)):
                data = stream.read(self.CHUNK)
                frames.append(data)
                
            print(">>> [Hearing] Recording stopped. Transcribing...")
            
            stream.stop_stream()
            stream.close()
        except Exception as e:
            print(f"[Audio Error] Microphone failed: {e}")
            p.terminate()
            return ""
            
        p.terminate()

        # 2. 保存临时文件
        temp_filename = "temp_voice.wav"
        wf = wave.open(temp_filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # 3. 转录 (ASR)
        try:
            print(f">>> [Hearing] Transcribing (Language: {lang if lang else 'Auto'})...")
            
            # 【关键修改】将 lang 参数传递给 transcribe
            segments, info = self.model.transcribe(
                temp_filename, 
                beam_size=5, 
                language=lang  # <--- 这里使用了传入的参数
            )
            
            full_text = ""
            for segment in segments:
                full_text += segment.text

            # 清理临时文件
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

            print(f">>> [Hearing] Result: '{full_text}'")
            return full_text
            
        except Exception as e:
            print(f">>> [Transcribe Error]: {e}")
            return ""