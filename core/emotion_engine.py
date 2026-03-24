import cv2
import numpy as np
from feat import Detector

class EmotionEngine:
    def __init__(self, device="cpu"):
        print(f">>> [Emotion] Initializing Py-Feat on {device}...")
        
        # 定义情绪标签字典 (Py-Feat ResMaskNet 标准顺序)
        self.labels = ['anger', 'disgust', 'fear', 'happiness', 'sadness', 'surprise', 'neutral']
        
        self.detector = Detector(
            face_model="retinaface",
            landmark_model="mobilefacenet",
            au_model="xgb",
            emotion_model="resmasknet",
            device=device
        )
        print(">>> [Emotion] Engine Loaded.")

    def analyze(self, frame):
        try:
            detected_faces = self.detector.detect_faces(frame)
            if len(detected_faces) == 0 or detected_faces[0] is None:
                return None

            landmarks = self.detector.detect_landmarks(frame, detected_faces)
            aus = self.detector.detect_aus(frame, landmarks)
            emotions = self.detector.detect_emotions(frame, detected_faces, landmarks)
            
            # 【修复关键点】
            # emotions 通常是一个 DataFrame 或 数组
            # 我们先获取概率最大值的【索引位置】(这是一个数字，比如 3)
            emotion_idx = emotions[0].argmax()
            
            # 然后用字典把它【翻译】成单词 (比如 "happiness")
            dominant_emotion_label = self.labels[emotion_idx]
            
            confidence = emotions[0].max()

            return {
                "emotion": dominant_emotion_label, # 现在它是字符串了！
                "confidence": float(confidence),
                "aus": aus[0]
            }
        except Exception as e:
            # print(f"[Emotion Error]: {e}")
            return None