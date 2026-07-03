import cv2
import numpy as np
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MeasurementResult:
    head_diameter: float = 0.0
    shaft_diameter: float = 0.0
    shaft_length: float = 0.0
    diameter: float = 0.0
    width: float = 0.0
    length: float = 0.0
    confidence: float = 0.0
    pixel_per_mm: float = 0.05


class PrecisionMeasurer:

    def __init__(self, pixel_per_mm: float = 0.05):
        self._pixel_per_mm = pixel_per_mm

    def update_calibration(self, pixel_per_mm: float):
        self._pixel_per_mm = pixel_per_mm

    def _get_screw_mask(self, roi):
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None
        h, w = roi.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        for c in contours:
            if cv2.contourArea(c) > 100:
                cv2.drawContours(mask, [c], -1, 255, -1)
        if cv2.countNonZero(mask) < 50:
            return None
        return mask

    def _extract_width_profile(self, mask):
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, 0.0
        mc = max(contours, key=cv2.contourArea)
        pts = mc.squeeze()
        if pts.ndim != 2 or pts.shape[1] != 2:
            return None, 0.0
        vx, vy, cx, cy = cv2.fitLine(mc, cv2.DIST_L2, 0, 0.01, 0.01)
        vx, vy, cx, cy = float(vx), float(vy), float(cx), float(cy)
        axis = np.array([vx, vy])
        perp = np.array([-vy, vx])
        proj_along = (pts - [cx, cy]) @ axis
        proj_perp = (pts - [cx, cy]) @ perp
        t_min, t_max = float(np.min(proj_along)), float(np.max(proj_along))
        total_length_px = t_max - t_min
        num_slices = max(40, min(100, int(total_length_px)))
        slice_edges = np.linspace(t_min, t_max, num_slices + 1)
        profile = np.zeros(num_slices, dtype=np.float64)
        for i in range(num_slices):
            in_slice = (proj_along >= slice_edges[i]) & (proj_along < slice_edges[i+1])
            if np.sum(in_slice) >= 2:
                perp_vals = proj_perp[in_slice]
                profile[i] = float(np.max(perp_vals) - np.min(perp_vals))
            else:
                profile[i] = 0.0
        return profile, total_length_px

    def _classify_sides(self, smoothed, peak_idx):
        # 利用螺丝的不对称物理结构：螺杆永远比螺帽长
        # 峰值（螺帽中心）哪一侧的切片数多，哪一侧就是螺杆
        n = len(smoothed)
        left_len = peak_idx
        right_len = n - 1 - peak_idx
        # 如果右侧切片数 >= 左侧，说明螺杆在右，螺帽在左 -> left_side = True
        left_side = right_len >= left_len
        return left_side, float(left_len), float(right_len)

    def _find_transition(self, smoothed, pi, left_side, mw):
        base_w = min(smoothed[0], smoothed[-1])
        thr = base_w + (mw - base_w) * 0.45
        if left_side:
            # 螺帽在左，分界在右：从峰值向右寻找下降到跳变拐点
            for i in range(pi + 1, len(smoothed)):
                if smoothed[i] < thr:
                    return i
            return len(smoothed) - 1
        else:
            # 螺帽在右，分界在左：从峰值向左寻找下降到跳变拐点
            for i in range(pi - 1, -1, -1):
                if smoothed[i] < thr:
                    return i
            return 0

    def _analyze_width_profile(self, rotated_mask=None, profile=None):
        if profile is None and rotated_mask is not None:
            profile = np.sum(rotated_mask > 0, axis=0).astype(np.float64)
        elif profile is None:
            return 0.0, 0.0, 0.0, 0.0, 0.0
            
        n = len(profile)
        if n < 5:
            return 0.0, 0.0, 0.0, 0.0, 0.0
            
        nz = np.nonzero(profile > 0)[0]
        if len(nz) < 4:
            return 0.0, 0.0, 0.0, 0.0, 0.0
            
        p = profile[nz[0]:nz[-1]+1].copy()
        total_valid_slices = len(p)
        
        # 使用边缘复制平滑，防止 mode='same' 带来的两端向 0 塌陷
        padded_p = np.pad(p, 2, mode='edge')
        ks = np.ones(5) / 5
        s = np.convolve(padded_p, ks, mode='valid')
        
        mw = float(np.max(s))
        if mw < 1:
            return 0.0, 0.0, 0.0, 0.0, 0.0
            
        pi = int(np.argmax(s))
        left_side, _, _ = self._classify_sides(s, pi)
        ti = self._find_transition(s, pi, left_side, mw)
        
        if left_side:
            # 螺帽在左：只取峰值附近的核心饱满段，避开左侧边缘的极窄切片
            head_start = max(0, int(pi * 0.4))
            head_region = s[head_start:ti] if head_start < ti else s[:ti]
            
            # 螺杆在右：用 0.35 阈值精准切齐螺杆末端
            raw_shaft = s[ti:]
            valid_shaft_idx = np.where(raw_shaft > (mw * 0.35))[0]
            shaft_region = raw_shaft[valid_shaft_idx] if len(valid_shaft_idx) > 0 else raw_shaft
            
            sl = float(len(shaft_region))
        else:
            # 螺帽在右：只取峰值右侧的核心饱满段
            head_end = min(total_valid_slices, pi + int((total_valid_slices - pi) * 0.6))
            head_region = s[ti:head_end] if ti < head_end else s[ti:]
            
            # 螺杆在左
            raw_shaft = s[:ti]
            valid_shaft_idx = np.where(raw_shaft > (mw * 0.35))[0]
            shaft_region = raw_shaft[valid_shaft_idx] if len(valid_shaft_idx) > 0 else raw_shaft
            
            sl = float(len(shaft_region))
            
        # 纯净区域统计
        hd = float(np.max(head_region)) if len(head_region) > 0 else mw
        sd = float(np.median(shaft_region)) if len(shaft_region) > 0 else mw * 0.5
        
        if sd < 1:
            sd = hd * 0.5
        if sl < 1:
            sl = float(total_valid_slices) * 0.7
            
        if hd > 0 and sd > 0:
            sep = (hd - sd) / hd
            conf = float(min(max(sep * 1.5, 0.0), 1.0))
        else:
            conf = 0.0
            
        return hd, sd, sl, total_valid_slices, conf
    def measure_roi(self, roi):
        result = MeasurementResult(pixel_per_mm=self._pixel_per_mm)
        if roi is None or roi.size == 0:
            return result
        mask = self._get_screw_mask(roi)
        if mask is None or cv2.countNonZero(mask) < 50:
            return result
        profile, total_length_px = self._extract_width_profile(mask)
        if profile is None or len(profile) < 5:
            return result
        hd_px, sd_px, sl_idx, valid_slices, conf = self._analyze_width_profile(profile=profile)
        ppm = self._pixel_per_mm
        if ppm > 0 and hd_px > 0:
            result.head_diameter = round((hd_px / ppm) + 0.2, 2)
            result.shaft_diameter = round(sd_px / ppm, 2)
            if sl_idx > 0 and valid_slices > 0:
                sl_px = total_length_px * (sl_idx / valid_slices)
            else:
                sl_px = 0.0
            result.shaft_length = round(sl_px / ppm, 2)

            result.diameter = result.head_diameter
            result.width = result.shaft_diameter
            result.length = result.shaft_length
            result.confidence = round(conf, 3)
        return result

    def measure_with_boxes(self, frame, boxes):
        results = []
        h_frame, w_frame = frame.shape[:2]
        for x, y, w, h in boxes:
            x1 = max(0, x)
            y1 = max(0, y)
            x2 = min(w_frame, x + w)
            y2 = min(h_frame, y + h)
            if x2 <= x1 or y2 <= y1:
                results.append(MeasurementResult(pixel_per_mm=self._pixel_per_mm))
                continue
            roi = frame[y1:y2, x1:x2]
            results.append(self.measure_roi(roi))
        return results
