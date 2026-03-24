import cv2
import mediapipe as mp
import numpy as np
import time

class VisionEngine:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        # ref: https://developers.google.com/mediapipe/solutions/vision/face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,  # 开启瞳孔注视点检测
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

    def process_frame(self, frame):
        """
        输入: BGR 图像
        输出: (是否检测到, 归一化的中心坐标(x,y), 原始landmarks)
        """
        # MediaPipe 需要 RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        face_center = None
        landmarks = None

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            
            # 计算面部几何中心 (粗略取鼻尖 index 1 和 4 之间)
            # MediaPipe Index 1: Nose tip
            nose_tip = landmarks.landmark[1]
            face_center = (nose_tip.x, nose_tip.y)
            
            return True, face_center, landmarks
            
        return False, None, None

    def draw_landmarks(self, image, landmarks):
        """在画面上绘制网格，用于调试"""
        self.mp_drawing.draw_landmarks(
            image=image,
            landmark_list=landmarks,
            connections=self.mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_tesselation_style()
        )
        # 绘制眼睛轮廓（用于确认注视方向）
        self.mp_drawing.draw_landmarks(
            image=image,
            landmark_list=landmarks,
            connections=self.mp_face_mesh.FACEMESH_IRISES,
            landmark_drawing_spec=None,
            connection_drawing_spec=self.mp_drawing_styles.get_default_face_mesh_iris_connections_style()
        )