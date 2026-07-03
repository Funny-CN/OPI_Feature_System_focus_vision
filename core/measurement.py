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
        _, binary = cv2.threshold(blurred, 110, 255, cv2.THRESH_BINARY_INV)
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
            return None
        mc = max(contours, key=cv2.contourArea)
        pts = mc.squeeze()
        if pts.ndim != 2 or pts.shape[1] != 2:
            return None
        vx, vy, cx, cy = cv2.fitLine(mc, cv2.DIST_L2, 0, 0.01, 0.01)
        vx, vy, cx, cy = float(vx), float(vy), float(cx), float(cy)
        proj = (pts - [cx, cy]) @ np.array([vx, vy])
        t_min, t_max = float(np.min(proj)), float(np.max(proj))
        num = max(int((t_max - t_min)), 10)
        h, w = mask.shape
        ts = np.linspace(t_min, t_max, num)
        px_arr = cx + ts * vx
        py_arr = cy + ts * vy
        perp_x, perp_y = -vy, vx
        profile = np.zeros(num, dtype=np.float64)
        for i in range(num):
            px, py = px_arr[i], py_arr[i]
            pos = 0
            while True:
                sx = int(round(px + pos * perp_x))
                sy = int(round(py + pos * perp_y))
                if sx < 0 or sx >= w or sy < 0 or sy >= h or mask[sy, sx] == 0:
                    break
                pos += 1
            neg = 0
            while True:
                sx = int(round(px - neg * perp_x))
                sy = int(round(py - neg * perp_y))
                if sx < 0 or sx >= w or sy < 0 or sy >= h or mask[sy, sx] == 0:
                    break
                neg += 1
            profile[i] = float(max(pos + neg - 1, 0))
        return profile

    def _classify_sides(self, smoothed, peak_idx):
        ls = max(int(peak_idx * 0.3), 3)
        rs = max(int((len(smoothed) - peak_idx - 1) * 0.3), 3)
        lm = float(np.median(smoothed[:ls]))
        rm = float(np.median(smoothed[-rs:]))
        return lm >= rm, lm, rm

    def _find_transition(self, smoothed, pi, left_side, mw):
        thr = mw * 0.70
        if left_side:
            for i in range(pi - 1, -1, -1):
                if smoothed[i] < thr:
                    return i
            return 0
        else:
            for i in range(pi + 1, len(smoothed)):
                if smoothed[i] < thr:
                    return i
            return len(smoothed) - 1

    def _find_tail(self, smoothed, ti, left_side, sd):
        thr = max(sd * 0.08, 1.0)
        if left_side:
            for i in range(ti - 1, -1, -1):
                if smoothed[i] < thr:
                    return i
            return 0
        else:
            for i in range(ti + 1, len(smoothed)):
                if smoothed[i] < thr:
                    return i
            return len(smoothed) - 1

    def _analyze_width_profile(self, rotated_mask=None, profile=None):
        if profile is None and rotated_mask is not None:
            profile = np.sum(rotated_mask > 0, axis=0).astype(np.float64)
        elif profile is None:
            return 0.0, 0.0, 0.0, 0.0
        n = len(profile)
        if n < 10:
            return 0.0, 0.0, 0.0, 0.0
        nz = np.nonzero(profile > 0)[0]
        if len(nz) < 5:
            return 0.0, 0.0, 0.0, 0.0
        p = profile[nz[0]:nz[-1]+1].copy()
        ks = np.ones(5) / 5
        s = np.convolve(p, ks, mode='same')
        mw = float(np.max(s))
        if mw < 1:
            return 0.0, 0.0, 0.0, 0.0
        pi = int(np.argmax(s))
        left_side, _, _ = self._classify_sides(s, pi)
        hd = float(np.percentile(s, 95))
        ti = self._find_transition(s, pi, left_side, mw)
        if left_side:
            sr = s[:ti + 1] if ti > 0 else s[:pi]
        else:
            sr = s[ti:] if ti < n - 1 else s[pi:]
        sd = float(np.median(sr)) if len(sr) > 3 else 0.0
        if sd < 1:
            sd = hd * 0.4
        tai = self._find_tail(s, ti, left_side, sd)
        if left_side:
            sl = float(ti - tai - 1) if ti > tai else float(ti)
        else:
            sl = float(tai - ti - 1) if tai > ti else float(n - 1 - ti)
        if sl < 1:
            sl = float(ti) if left_side else float(n - 1 - ti)
        if hd > 0 and sd > 0 and mw > 0:
            sep = (hd - sd) / hd
            conf = float(min(max(sep * 1.5, 0.0), 1.0))
        else:
            conf = 0.0
        return hd, sd, sl, conf

    def measure_roi(self, roi):
        result = MeasurementResult(pixel_per_mm=self._pixel_per_mm)
        if roi is None or roi.size == 0:
            return result
        mask = self._get_screw_mask(roi)
        if mask is None or cv2.countNonZero(mask) < 50:
            return result
        profile = self._extract_width_profile(mask)
        if profile is None or len(profile) < 10:
            return result
        hd_px, sd_px, sl_px, conf = self._analyze_width_profile(profile=profile)
        ppm = self._pixel_per_mm
        if ppm > 0 and hd_px > 0:
            result.head_diameter = round(hd_px / ppm, 2)
            result.shaft_diameter = round(sd_px / ppm, 2)
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




