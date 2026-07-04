#!/usr/bin/env python3
"""
硬币标定脚本（基于已有图片）

用法:
    python calibrate_from_image.py samples/coin.jpg

用 samples 目录下已有的 1 元硬币照片计算 pixel_per_mm，并更新 config.json。
"""
import cv2
import numpy as np
import json
import sys
import os

COIN_DIAMETER_MM = 25.0
CONFIG_PATH = "config.json"


def detect_coin(image_path):
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[ERROR] 无法读取图片: {image_path}")
        return None, None, None

    h, w = frame.shape[:2]
    print(f"[INFO] 图像尺寸: {w}x{h}")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 0)

    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT,
        dp=1, minDist=500,
        param1=100, param2=40,
        minRadius=50, maxRadius=800
    )

    if circles is None:
        print("[ERROR] 未检测到圆形")
        return None, None, None

    circles = np.round(circles[0]).astype(int)
    ref = max(circles, key=lambda c: c[2])
    cx, cy, r = ref

    annotated = frame.copy()
    cv2.circle(annotated, (cx, cy), r, (0, 255, 0), 3)
    cv2.circle(annotated, (cx, cy), 3, (0, 0, 255), -1)
    label = f"Coin: {r * 2}px = {COIN_DIAMETER_MM}mm"
    cv2.putText(annotated, label, (cx - r, cy - r - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    out_path = "calibration_result.jpg"
    cv2.imwrite(out_path, annotated)
    print(f"[INFO] 标定图已保存: {out_path}")

    pixel_diameter = r * 2
    ratio = pixel_diameter / COIN_DIAMETER_MM

    print(f"\n[OK] 检测到硬币!")
    print(f"  圆心: ({cx}, {cy})")
    print(f"  像素直径: {pixel_diameter} px")
    print(f"  物理直径: {COIN_DIAMETER_MM} mm")
    print(f"  pixel_per_mm = {ratio:.4f}")

    return ratio, pixel_diameter, annotated


def update_config(ratio):
    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取 {CONFIG_PATH} 失败: {e}")
        return

    old_ratio = cfg.get("calibration", {}).get("pixel_to_mm_ratio", "N/A")
    cfg.setdefault("calibration", {})
    cfg["calibration"]["pixel_to_mm_ratio"] = round(ratio, 4)
    cfg["calibration"]["reference_diameter_mm"] = COIN_DIAMETER_MM

    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    print(f"\n[UPDATE] config.json 已更新")
    print(f"  旧值: {old_ratio}")
    print(f"  新值: {ratio:.4f}")


def main():
    print("=" * 50)
    print("螺丝特征筛选系统 - 硬币标定 (图片版)")
    print("=" * 50)
    print(f"\n参考物: 1 元硬币 (直径 {COIN_DIAMETER_MM}mm)")

    if len(sys.argv) < 2:
        print("\n用法: python calibrate_from_image.py <图片路径>")
        print("例如: python calibrate_from_image.py samples/coin.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"[ERROR] 文件不存在: {image_path}")
        sys.exit(1)

    ratio, px_dia, _ = detect_coin(image_path)
    if ratio is None:
        sys.exit(1)

    update_config(ratio)
    print("\n标定完成! 现在可以用 test_pipeline.py 验证效果了")


if __name__ == "__main__":
    main()
