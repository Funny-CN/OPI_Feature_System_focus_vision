"""
AI 检测模块

加载 RKNN 量化模型在 NPU 上执行推理。
当前为占位实现，返回模拟结果以便 PC 端开发调试。
"""

from typing import List, Optional, Tuple


class AIDetector:
    """
    AI 检测器
    使用 YOLOv5n 模型检测螺丝位置，输出检测框坐标。
    当前为占位实现（stub），后续接入 RKNN 推理。
    """

    def __init__(self, model_path: Optional[str] = None):
        """
        :param model_path: RKNN 模型路径，为 None 时进入模拟模式
        """
        self._model_path = model_path
        self._model = None
        self._loaded = False

        if model_path:
            self._load_model()
        else:
            print("[AI] 占位模式：未指定模型路径，使用模拟检测")

    def _load_model(self):
        """加载 RKNN 模型（占位，后续实现）"""
        # TODO: 使用 RKNN Toolkit Lite2 加载模型
        #   from rknnlite.api import RKNNLite
        #   self._model = RKNNLite()
        #   self._model.load_rknn(self._model_path)
        #   self._model.init_runtime()
        print(f"[AI] 模型路径: {self._model_path}")
        print("[AI] RKNN 加载待接入")

    # ── 核心推理 ──────────────────────────────────

    def detect(self, frame) -> List[Tuple[int, int, int, int]]:
        """
        对输入帧执行检测，返回螺丝检测框列表。

        :param frame: OpenCV 图像 (numpy.ndarray)
        :return: 检测框列表 [(x, y, w, h), ...]
                 返回空列表表示未检测到螺丝
        """
        if self._loaded:
            # TODO: 调用 NPU 推理
            #   outputs = self._model.inference(inputs=[frame])
            #   解析输出，提取检测框
            pass

        # 占位：返回空列表，模拟未检测到
        return []

    def detect_single(self, frame) -> Optional[Tuple[int, int, int, int]]:
        """
        检测画面中的螺丝，返回最大的检测框。

        :return: (x, y, w, h) 或 None
        """
        boxes = self.detect(frame)
        if not boxes:
            return None
        # 取面积最大的框
        return max(boxes, key=lambda b: b[2] * b[3])

    @property
    def is_loaded(self) -> bool:
        return self._loaded
