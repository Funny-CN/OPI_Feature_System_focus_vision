"""
AI 检测模块

支持双后端：
  - "onnx": 在 Windows/Linux 上用 ONNX Runtime 推理（开发调试阶段）
  - "rknn": 在 Orange Pi 5 Pro 上用 RKNN Toolkit Lite2 推理（部署阶段）
  - None:   stub 模式，返回空结果

输出格式统一为 [(x, y, w, h), ...]，坐标原点为原始图像左上角。
"""

import os
import cv2
import numpy as np
from typing import List, Optional, Tuple


class AIDetector:
    def __init__(self, model_path=None, backend=None,
                 conf_threshold=0.5, nms_threshold=0.45, input_size=640):
        self._model_path = model_path
        self._backend = backend
        self._conf_threshold = conf_threshold
        self._nms_threshold = nms_threshold
        self._input_size = input_size
        self._model = None
        self._loaded = False

        if self._backend is None and model_path:
            ext = os.path.splitext(model_path)[1].lower()
            if ext == ".onnx":
                self._backend = "onnx"
            elif ext == ".rknn":
                self._backend = "rknn"
            elif ext == ".pt":
                self._backend = "torch"

        if model_path:
            self._load_model()
        else:
            print("[AI] Stub 模式")

    def _load_model(self):
        print("[AI] 加载模型:", self._model_path)
        print("[AI] 推理后端:", self._backend)
        if self._backend == "onnx":
            self._load_onnx()
        elif self._backend == "rknn":
            self._load_rknn()
        elif self._backend == "torch":
            self._load_torch()

    def _load_onnx(self):
        try:
            import onnxruntime as ort
            providers = ["CPUExecutionProvider"]
            if "CUDAExecutionProvider" in ort.get_available_providers():
                providers.insert(0, "CUDAExecutionProvider")
            self._model = ort.InferenceSession(self._model_path, providers=providers)
            self._loaded = True
            print("[AI] ONNX OK:", self._model.get_providers()[0])
        except Exception as e:
            print("[AI] ONNX 加载失败:", e)
            self._model = None
            self._loaded = False

    def _load_rknn(self):
        try:
            from rknnlite.api import RKNNLite
            self._model = RKNNLite()
            ret = self._model.load_rknn(self._model_path)
            if ret != 0:
                raise RuntimeError("load_rknn error", ret)
            ret = self._model.init_runtime(core_mask=RKNNLite.NPU_CORE_0)
            if ret != 0:
                raise RuntimeError("init_runtime error", ret)
            self._loaded = True
            print("[AI] RKNN OK")
        except Exception as e:
            print("[AI] RKNN 加载失败:", e)
            self._model = None
            self._loaded = False

    def _load_torch(self):
        try:
            import torch
            ckpt = torch.load(self._model_path, map_location="cpu", weights_only=False)
            if isinstance(ckpt, dict) and "model" in ckpt:
                m = ckpt["model"]
            else:
                m = ckpt
            m.eval()
            self._model = m
            self._loaded = True
            print("[AI] PyTorch OK")
        except Exception as e:
            print("[AI] PyTorch 加载失败:", e)
            self._model = None
            self._loaded = False

    def _preprocess(self, frame):
        h, w = frame.shape[:2]
        scale = min(self._input_size / h, self._input_size / w)
        new_h = int(round(h * scale))
        new_w = int(round(w * scale))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        pad_w = (self._input_size - new_w) / 2.0
        pad_h = (self._input_size - new_h) / 2.0
        top = int(round(pad_h - 0.1))
        bottom = int(round(pad_h + 0.1))
        left = int(round(pad_w - 0.1))
        right = int(round(pad_w + 0.1))
        padded = cv2.copyMakeBorder(resized, top, bottom, left, right,
                                     cv2.BORDER_CONSTANT, value=(114, 114, 114))
        blob = padded.astype(np.float32) / 255.0
        blob = np.transpose(blob, (2, 0, 1))
        blob = np.expand_dims(blob, axis=0)
        return blob, scale, (scale, left, top, new_w, new_h)

    def _postprocess(self, outputs, scale, pad_info, orig_shape):
        _, left, top, new_w, new_h = pad_info
        raw = outputs[0].squeeze(0)
        conf = raw[:, 4] * raw[:, 5]
        mask = conf >= self._conf_threshold
        if not np.any(mask):
            return []
        filtered = raw[mask]
        scores = conf[mask]
        boxes = np.zeros((len(filtered), 4), dtype=np.float32)
        boxes[:, 0] = filtered[:, 0]
        boxes[:, 1] = filtered[:, 1]
        boxes[:, 2] = filtered[:, 2]
        boxes[:, 3] = filtered[:, 3]
        xyxy = np.zeros_like(boxes)
        xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2
        xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2
        xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2
        xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2
        keep = self._nms(xyxy, scores, self._nms_threshold)
        h_orig, w_orig = orig_shape
        results = []
        for idx in keep:
            x1 = (xyxy[idx, 0] - left) / scale
            y1 = (xyxy[idx, 1] - top) / scale
            x2 = (xyxy[idx, 2] - left) / scale
            y2 = (xyxy[idx, 3] - top) / scale
            x = int(round(max(0, x1)))
            y = int(round(max(0, y1)))
            x2i = int(round(min(w_orig, x2)))
            y2i = int(round(min(h_orig, y2)))
            w = x2i - x
            h = y2i - y
            if w > 0 and h > 0:
                results.append((x, y, w, h))
        return results

    def _nms(self, boxes, scores, iou_threshold):
        indices = np.argsort(scores)[::-1]
        keep = []
        while len(indices) > 0:
            i = indices[0]
            keep.append(i)
            if len(indices) == 1:
                break
            xx1 = np.maximum(boxes[i, 0], boxes[indices[1:], 0])
            yy1 = np.maximum(boxes[i, 1], boxes[indices[1:], 1])
            xx2 = np.minimum(boxes[i, 2], boxes[indices[1:], 2])
            yy2 = np.minimum(boxes[i, 3], boxes[indices[1:], 3])
            inter = np.maximum(0, xx2 - xx1) * np.maximum(0, yy2 - yy1)
            area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
            area_j = (boxes[indices[1:], 2] - boxes[indices[1:], 0]) * (boxes[indices[1:], 3] - boxes[indices[1:], 1])
            union = area_i + area_j - inter
            iou = inter / np.maximum(union, 1e-6)
            mask = iou <= iou_threshold
            indices = indices[1:][mask]
        return keep

    def detect(self, frame):
        if frame is None or frame.size == 0 or not self._loaded:
            return []
        try:
            input_tensor, scale, pad_info = self._preprocess(frame)
            if self._backend == "onnx":
                outputs = self._model.run(None, {"images": input_tensor})
            elif self._backend == "rknn":
                outputs = self._model.inference(inputs=[input_tensor])
            elif self._backend == "torch":
                import torch
                with torch.no_grad():
                    raw = self._model(torch.from_numpy(input_tensor))
                    outputs = [raw.cpu().numpy()]
            else:
                return []
            return self._postprocess(outputs, scale, pad_info, frame.shape[:2])
        except Exception as e:
            print("[AI] 推理错误:", e)
            return []

    def detect_single(self, frame):
        boxes = self.detect(frame)
        if not boxes:
            return None
        return max(boxes, key=lambda b: b[2] * b[3])

    @property
    def is_loaded(self):
        return self._loaded

    @property
    def backend(self):
        return self._backend
