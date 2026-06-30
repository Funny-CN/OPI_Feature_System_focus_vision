"""
协调控制器

协调 AI 检测 + CV 精密测量 + 数据库匹配 三阶段流水线。
同时保留原有的 Hough 圆检测作为回退方案。
"""
import cv2
import numpy as np
import os
import os
from typing import List, Optional, Tuple
from dataclasses import dataclass
from core.database import ScrewDatabase, MatchResult
from core.measurement import PrecisionMeasurer, MeasurementResult
from core.ai_detector import AIDetector
@dataclass
class ScrewResult:
    box: Tuple[int, int, int, int]
    measurement: MeasurementResult
    match: MatchResult
@dataclass
class AnalysisResult:
    screw_count: int = 0
    screws: List[ScrewResult] = None
    annotated_frame: Optional[np.ndarray] = None
    has_ai: bool = False
class ScrewDetector:
    def __init__(self):
        self.db = ScrewDatabase()
        cal = self._load_calibration()
        self.measurer = PrecisionMeasurer(pixel_per_mm=cal)
        self.ai = AIDetector()
        self.coin_real_diameter_mm = 25.0
        self.hough_params = {
            "dp": 1, "min_dist": 350, "param1": 100,
            "param2": 40, "min_radius": 60, "max_radius": 300
        }
    def _load_calibration(self) -> float:
        import json
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        try:
            with open(path, "r") as f:
                cfg = json.load(f)
            return cfg.get("calibration", {}).get("pixel_to_mm_ratio", 0.05)
        except Exception:
            return 0.05
    def analyze(self, frame: np.ndarray) -> AnalysisResult:
        result = AnalysisResult(screws=[], annotated_frame=frame.copy())
        boxes = self._detect_boxes(frame)
        result.has_ai = self.ai.is_loaded
        if not boxes:
            return result
        measurements = self.measurer.measure_with_boxes(frame, boxes)
        for box, meas in zip(boxes, measurements):
            match = self.db.match(meas.diameter)
            sr = ScrewResult(box=box, measurement=meas, match=match)
            result.screws.append(sr)
            self._annotate(result.annotated_frame, sr)
        result.screw_count = len(result.screws)
        return result
    def _detect_boxes(self, frame) -> List[Tuple[int, int, int, int]]:
        if self.ai.is_loaded:
            boxes = self.ai.detect(frame)
            if boxes:
                return boxes
        return self._hough_detect(frame)
    def _hough_detect(self, frame) -> List[Tuple[int, int, int, int]]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT,
            dp=self.hough_params["dp"],
            minDist=float(self.hough_params["min_dist"]),
            param1=float(self.hough_params["param1"]),
            param2=float(self.hough_params["param2"]),
            minRadius=int(self.hough_params["min_radius"]),
            maxRadius=int(self.hough_params["max_radius"])
        )
        boxes = []
        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
            for c in circles:
                x = c[0] - c[2]
                y = c[1] - c[2]
                w = c[2] * 2
                h = c[2] * 2
                boxes.append((x, y, w, h))
        return boxes
    def _annotate(self, frame, sr):
        x, y, w, h = sr.box
        meas = sr.measurement
        match = sr.match
        color = (0, 255, 0) if match.matched else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = "D:{:.1f}".format(meas.diameter)
        if meas.length > 0:
            label += " L:{:.1f}".format(meas.length)
        cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        if match.matched:
            mlabel = "{} dev:{:.2f}".format(match.screw.name, match.deviation)
            cv2.putText(frame, mlabel, (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 0), 2)
    def _calculate_real_diameters(self, img):
        boxes = self._hough_detect(img)
        if not boxes:
            return [], img
        diameters = []
        for box in boxes:
            meas = self.measurer.measure_with_boxes(img, [box])[0]
            diameters.append(meas.diameter)
            x, y, w, h = box
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, "{:.1f}mm".format(meas.diameter), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        return diameters, img
    def target_sampling(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            return None, None
        diameters, processed = self._calculate_real_diameters(img)
        if diameters:
            return diameters[0], processed
        return None, None
    def real_time_comparison(self, img, tolerance=1.0):
        diameters, processed = self._calculate_real_diameters(img)
        if not diameters:
            return False, processed
        for d in diameters:
            if abs(d - 6.0) <= tolerance:
                return True, processed
        return False, processed
