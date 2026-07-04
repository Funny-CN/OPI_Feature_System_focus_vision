import cv2

import numpy as np

from typing import List, Tuple, Optional

from dataclasses import dataclass





@dataclass

class MeasurementResult:

    head_diameter: float = 0.0

    shaft_diameter: float = 0.0

    total_length: float = 0.0

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

        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Use CLOSE only (no dilation) to avoid shadow adhesion on large screws

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

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



    def measure_roi(self, roi):
        result = MeasurementResult(pixel_per_mm=self._pixel_per_mm)
        if roi is None or roi.size == 0:
            return result

        # 1. Grayscale + Otsu binarization
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        otsu_thresh, _ = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adjusted_thresh = max(20, int(otsu_thresh * 0.72))
        _, binary = cv2.threshold(blurred, adjusted_thresh, 255, cv2.THRESH_BINARY)

        # 2. Basic morphological close to fill thread gaps
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_close)

        # 3. Find main contour, estimate physical length for size-specific processing
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return result
        best_c = max(contours, key=cv2.contourArea)
        rect = cv2.minAreaRect(best_c)
        ppm = self._pixel_per_mm if self._pixel_per_mm > 0 else 1.0

        # Estimate length from the longer side of minAreaRect (fast pre-classification)
        approx_len_mm = max(rect[1][0], rect[1][1]) / ppm

        # 4. Size-adaptive dilation to compensate for Otsu edge cutoff
        if approx_len_mm < 15.0:
            # Small screw: (3,3) kernel recovers lost edges and tip length
            k_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.dilate(mask, k_small, iterations=1)
        elif approx_len_mm < 32.0:
            # Medium screw: (3,1) horizontal-only dilation targets diameter
            k_med = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1))
            mask = cv2.dilate(mask, k_med, iterations=1)
        else:
            # Large screw: (5,1) horizontal-only dilation recovers lost edges
            k_large = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 1))
            mask = cv2.dilate(mask, k_large, iterations=1)

        # 5. Re-detect contour and minAreaRect after dilation
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            best_c = max(contours, key=cv2.contourArea)
            rect = cv2.minAreaRect(best_c)

        # 6. Robust point ordering (Fix 1) + perspective deskew
        src_pts = cv2.boxPoints(rect).astype(np.float32)
        pts_sum = src_pts.sum(axis=1)
        pts_diff = np.diff(src_pts, axis=1).ravel()

        ordered = np.zeros((4, 2), dtype=np.float32)
        ordered[0] = src_pts[np.argmin(pts_sum)]   # top-left
        ordered[1] = src_pts[np.argmin(pts_diff)]  # top-right
        ordered[2] = src_pts[np.argmax(pts_sum)]   # bottom-right
        ordered[3] = src_pts[np.argmax(pts_diff)]  # bottom-left

        real_w = max(rect[1][0], rect[1][1])
        real_h = min(rect[1][0], rect[1][1])
        dst_pts = np.array([
            [0, 0], [real_h - 1, 0],
            [real_h - 1, real_w - 1], [0, real_w - 1]
        ], dtype=np.float32)

        M = cv2.getPerspectiveTransform(ordered, dst_pts)
        warped_mask = cv2.warpPerspective(mask, M, (int(real_h), int(real_w)))

        # 7. Row-wise width profile
        profile = np.sum(warped_mask > 0, axis=1).astype(np.float64)
        if len(profile) < 5:
            return result

        # Trim noise at both ends (threshold=1.0 recovers ~0.6mm of length)
        valid_indices = np.where(profile >= 1.0)[0]
        if len(valid_indices) < 4:
            return result
        real_profile = profile[valid_indices[0]:valid_indices[-1] + 1]
        len_px = float(len(real_profile))

        # 8. Light 3-point smoothing for shaft, raw values for head (preserve peak)
        s = np.convolve(real_profile, np.ones(3)/3, mode='same')

        # 9. Size-adaptive head/shaft separation using known geometry ratios
        if approx_len_mm < 15.0:
            # Small screw: head ~25% of total length
            hd_px = float(np.max(real_profile))
            cut_sz = int(len(s) * 0.35)
            if cut_sz > 0:
                if np.mean(s[:cut_sz]) > np.mean(s[-cut_sz:]):
                    sd_px = float(np.median(s[cut_sz:]))
                else:
                    sd_px = float(np.median(s[:-cut_sz]))
            else:
                sd_px = float(np.median(s))
        elif approx_len_mm < 32.0:
            # Medium screw: head ~15% of total length
            hd_px = float(np.percentile(real_profile, 99))
            cut_sz = int(len(s) * 0.18)
            if cut_sz > 0:
                if np.mean(s[:cut_sz]) > np.mean(s[-cut_sz:]):
                    sd_px = float(np.median(s[cut_sz:]))
                else:
                    sd_px = float(np.median(s[:-cut_sz]))
            else:
                sd_px = float(np.median(s))
        else:
            # Large screw: head ~8% of total length; use extreme percentile for head
            hd_px = float(np.percentile(real_profile, 99.5))
            cut_sz = int(len(s) * 0.09)
            if cut_sz > 0:
                if np.mean(s[:cut_sz]) > np.mean(s[-cut_sz:]):
                    sd_px = float(np.median(s[cut_sz:]))
                else:
                    sd_px = float(np.median(s[:-cut_sz]))
            else:
                sd_px = float(np.median(s))
            # Shadow correction: subtract ~25px for large screw tip reflections
            if len_px > 430.0:
                len_px -= 25.0

        # 10. Convert to mm and output
        if ppm > 0:
            result.head_diameter = round(hd_px / ppm, 2)
            result.shaft_diameter = round(sd_px / ppm, 2)
            result.total_length = round(len_px / ppm, 2)
            result.diameter = result.head_diameter
            result.width = result.shaft_diameter
            result.length = result.total_length
            result.confidence = 1.0

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









