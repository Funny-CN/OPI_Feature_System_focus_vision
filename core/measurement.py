import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass

"""
CV 精密测量模块

在 ROI 区域内做边缘检测与轮廓拟合，
输出螺丝的直径、长度等精确尺寸。
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional



class MeasurementResult:
    """单颗螺丝的测量结果"""
    diameter: float = 0.0       # 直径 (mm)
    length: float = 0.0         # 长度 (mm)
    width: float = 0.0          # 宽度 (mm)
    confidence: float = 0.0     # 测量置信度 (0~1)
    pixel_per_mm: float = 0.05  # 像素-毫米换算比


class PrecisionMeasurer:
    """
    精密测量器
    在给定的 ROI 区域内执行边缘检测和尺寸计算。
    """

    def __init__(self, pixel_per_mm: float = 0.05):
        """
        :param pixel_per_mm: 像素-毫米换算比，通过标定获得
        """
        self._pixel_per_mm = pixel_per_mm

    def update_calibration(self, pixel_per_mm: float):
        """更新标定参数"""
        self._pixel_per_mm = pixel_per_mm

    # ── 核心测量方法 ──────────────────────────────

    def measure_roi(self, roi: np.ndarray) -> MeasurementResult:
        """
        对单个 ROI 区域进行精密测量。

        步骤：
          1. 灰度化 + 高斯模糊
          2. Canny 边缘检测
          3. 寻找轮廓
          4. 拟合包围圆 / 包围矩形
          5. 换算为毫米并返回结果
        """
        result = MeasurementResult(pixel_per_mm=self._pixel_per_mm)

        if roi is None or roi.size == 0:
            return result

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny 边缘检测
        edges = cv2.Canny(blurred, 50, 150)

        # 寻找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return result

        # 取面积最大的轮廓
        main_contour = max(contours, key=cv2.contourArea)

        # 拟合最小包围圆 → 获取直径
        (cx, cy), radius = cv2.minEnclosingCircle(main_contour)
        result.diameter = round((radius * 2) / self._pixel_per_mm, 2)

        # 拟合最小包围矩形 → 获取长宽
        rect = cv2.minAreaRect(main_contour)
        box_width, box_height = rect[1]

        # 区分长和宽
        if box_width >= box_height:
            result.length = round(box_width / self._pixel_per_mm, 2)
            result.width = round(box_height / self._pixel_per_mm, 2)
        else:
            result.length = round(box_height / self._pixel_per_mm, 2)
            result.width = round(box_width / self._pixel_per_mm, 2)

        # 置信度：根据轮廓面积与包围圆面积的比例
        circle_area = np.pi * (radius ** 2)
        contour_area = cv2.contourArea(main_contour)
        if circle_area > 0:
            result.confidence = round(min(contour_area / circle_area, 1.0), 3)

        return result

    def measure_with_boxes(
        self, frame: np.ndarray, boxes: List[Tuple[int, int, int, int]]
    ) -> List[MeasurementResult]:
        """
        对帧中的多个检测框分别进行精密测量。

        :param frame:  原始图像
        :param boxes:  检测框列表，每项为 (x, y, w, h)
        :return:       测量结果列表，与 boxes 一一对应
        """
        results = []
        h_frame, w_frame = frame.shape[:2]

        for x, y, w, h in boxes:
            # 边界保护
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w_frame, x + w)
            y2 = min(h_frame, y + h)

            if x2 <= x1 or y2 <= y1:
                results.append(MeasurementResult(pixel_per_mm=self._pixel_per_mm))
                continue

            roi = frame[y1:y2, x1:x2]
            result = self.measure_roi(roi)
            results.append(result)

        return results

    # ── 标定辅助 ──────────────────────────────────

    def calibrate_from_reference(
        self, frame: np.ndarray, reference_diameter_mm: float = 25.0
    ) -> float:
        """
        通过已知直径的参照物（如 1 元硬币）自动标定。

        在画面中检测圆形参照物，计算 pixel_per_mm。
        返回计算出的 pixel_per_mm 值。
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)

        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT,
            dp=1, minDist=500,
            param1=100, param2=40,
            minRadius=50, maxRadius=500
        )

        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
            # 取最大的圆作为参照物
            ref = max(circles, key=lambda c: c[2])
            pixel_radius = ref[2]
            self._pixel_per_mm = pixel_radius * 2 / reference_diameter_mm
            return self._pixel_per_mm

        return self._pixel_per_mm

