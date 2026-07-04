#!/usr/bin/env python3
"""
测试脚本 —— 全流水线命令行测试（AI检测 -> CV精测）
只输出三种尺寸测量值：螺帽直径 / 螺杆直径 / 总长度

用法：
    python test_pipeline.py                           # 处理 samples/ 下所有图片
    python test_pipeline.py samples/sample_01.jpg     # 处理单张
    python test_pipeline.py samples/ --save           # 批量 + 保存标注图

参考螺丝（实际物理尺寸 mm）：
  大：螺帽=9.4  螺杆=5.7  总长=44.2  螺杆长约40.6
  中：螺帽=6.6  螺杆=3.7  总长=32.4  螺杆长约29.7
  小：螺帽=5.2  螺杆=2.6  总长=8.0  螺杆长约6.0
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import glob
import cv2
from core.detector import ScrewDetector


def process_image(detector, image_path, save_dir=None):
    img = cv2.imread(image_path)
    if img is None:
        print(f"  [ERROR] 无法读取图片: {image_path}")
        return None

    h, w = img.shape[:2]
    filename = os.path.basename(image_path)
    result = detector.analyze(img)

    lines = []
    lines.append(f"  图片: {filename}  [{w}x{h}]")
    lines.append(f"  检测来源: {'AI' if result.has_ai else 'Hough'}")
    lines.append(f"  螺丝数: {result.screw_count}")

    for i, screw in enumerate(result.screws):
        m = screw.measurement
        box = screw.box
        lines.append(f"")
        lines.append(f"  ── 螺丝 #{i+1} [{box[2]}x{box[3]}] ──")
        lines.append(f"    螺帽直径(Head):   {m.head_diameter:.2f} mm")
        lines.append(f"    螺杆直径(Shaft):  {m.shaft_diameter:.2f} mm")
        lines.append(f"    总长度(Total):    {m.total_length:.2f} mm")
        lines.append(f"    置信度:           {m.confidence:.3f}")

    if save_dir and result.annotated_frame is not None:
        os.makedirs(save_dir, exist_ok=True)
        out_path = os.path.join(save_dir, f"annotated_{filename}")
        cv2.imwrite(out_path, result.annotated_frame)
        lines.append(f"  标注图已保存: {out_path}")

    print("\n".join(lines))
    return result


def main():
    parser = argparse.ArgumentParser(description="全流水线测试脚本")
    parser.add_argument("input", nargs="?", default="samples",
                        help="图片路径或目录（默认: samples/）")
    parser.add_argument("--save", action="store_true",
                        help="保存标注图到输出目录")
    parser.add_argument("--output", default=None,
                        help="输出目录（默认: 与输入同目录）")
    args = parser.parse_args()

    detector = ScrewDetector()

    input_path = args.input
    if os.path.isfile(input_path):
        paths = [input_path]
    else:
        paths = sorted(glob.glob(os.path.join(input_path, "*.jpg")) +
                       glob.glob(os.path.join(input_path, "*.png")))

    save_dir = args.output or (os.path.dirname(input_path)
                               if os.path.isfile(input_path) else args.input)
    if not args.save:
        save_dir = None

    for p in paths:
        print(f"\n{'='*60}")
        process_image(detector, p, save_dir=save_dir)


if __name__ == "__main__":
    main()
