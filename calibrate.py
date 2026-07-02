#!/usr/bin/env python3
"""
硬币标定脚本

把 1 元硬币（25mm）放在摄像头正下方拍摄区域，运行本脚本。
会自动检测硬币、计算 pixel_per_mm 并更新 config.json。
"""

import cv2
import numpy as np
import json
import os
import sys

COIN_DIAMETER_MM = 25.0
CONFIG_PATH = "config.json"
SAVE_PATH = "calibration_result.jpg"


def detect_coin(frame):
    """检测画面中最大的圆形（硬币）"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT,
        dp=1, minDist=500,
        param1=100, param2=40,
        minRadius=50, maxRadius=800
    )

    if circles is None:
        return None, frame

    circles = np.round(circles[0]).astype(int)
    ref = max(circles, key=lambda c: c[2])
    cx, cy, r = ref

    annotated = frame.copy()
    cv2.circle(annotated, (cx, cy), r, (0, 255, 0), 3)
    cv2.circle(annotated, (cx, cy), 3, (0, 0, 255), -1)
    label = f"Coin: {r * 2}px = {COIN_DIAMETER_MM}mm"
    cv2.putText(annotated, label, (cx - r, cy - r - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    return ref, annotated


def main():
    print("=" * 50)
    print("螺丝特征筛选系统 - 硬币标定")
    print("=" * 50)
    print(f"\n参考物: 1 元硬币 (直径 {COIN_DIAMETER_MM}mm)")
    print("请确保硬币完全在画面内，背景简洁无干扰\n")

    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        cam = cv2.VideoCapture(1)
    if not cam.isOpened():
        print("[ERROR] 无法打开摄像头")
        sys.exit(1)

    print("[INFO] 摄像头已打开")
    print("[INFO] 按 Enter 键拍照标定")
    input("     (放好硬币后按 Enter)...")

    ret, frame = cam.read()
    cam.release()

    if not ret or frame is None:
        print("[ERROR] 拍照失败")
        sys.exit(1)

    h, w = frame.shape[:2]
    print(f"[INFO] 图像尺寸: {w}x{h}")

    result, annotated = detect_coin(frame)

    if result is None:
        cv2.imwrite(SAVE_PATH, frame)
        print(f"\n[ERROR] 未检测到硬币")
        print(f"已将原始画面保存到 {SAVE_PATH}")
        print("请检查:")
        print("  1. 硬币是否在画面正中央")
        print("  2. 光线是否充足")
        print("  3. 背景不要太杂乱")
        sys.exit(1)

    cx, cy, r = result
    pixel_diameter = r * 2
    ratio = pixel_diameter / COIN_DIAMETER_MM

    cv2.imwrite(SAVE_PATH, annotated)

    print(f"\n[OK] 检测到硬币!")
    print(f"  圆心: ({cx}, {cy})")
    print(f"  像素直径: {pixel_diameter} px")
    print(f"  物理直径: {COIN_DIAMETER_MM} mm")
    print(f"  pixel_per_mm = {ratio:.4f}")
    print(f"  标定图已保存: {SAVE_PATH}")

    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)

    old_ratio = cfg["calibration"]["pixel_to_mm_ratio"]
    cfg["calibration"]["pixel_to_mm_ratio"] = round(ratio, 4)

    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    print(f"\n[UPDATE] config.json 已更新:")
    print(f"  旧值: {old_ratio}")
    print(f"  新值: {ratio:.4f}")
    print("\n标定完成! 现在可以运行主程序了")


if __name__ == "__main__":
    main()
