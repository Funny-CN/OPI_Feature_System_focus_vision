#!/usr/bin/env python3
"""
ONNX -> RKNN 模型转换脚本

在 PC 上运行，需要安装 rknn-toolkit2（推荐在 x86 Linux 或 WSL2 Ubuntu 中）。
将 yolo/weights/best.onnx 转换为 Orange Pi 5 Pro 可用的 best.rknn。

环境准备（WSL2 Ubuntu / x86 Linux）:
  pip install rknn-toolkit2

如果转换时遇到 numpy 版本冲突:
  pip install numpy==1.23.5

用法:
  # INT8 量化（推荐，NPU 最快，约 6 TOPS）
  python scripts/convert_rknn.py

  # FP16 量化（精度更高，速度稍慢）
  python scripts/convert_rknn.py --fp16

  # FP32 不量化（精度最高，速度最慢）
  python scripts/convert_rknn.py --no-quant

  # 指定 ONNX 路径和输出路径
  python scripts/convert_rknn.py --onnx xxx.onnx --rknn output.rknn
"""

import argparse
import os
import sys
import tempfile

from rknn.api import RKNN

ONNX_PATH = "yolo/weights/best.onnx"
RKNN_PATH = "models/best.rknn"
CALIB_DIR = "yolo/dataset/images/train"


def create_rknn_config(quantize_type: str, target: str) -> dict:
    config = {
        "mean_values": [[0, 0, 0]],
        "std_values": [[1, 1, 1]],
        "target_platform": target,
        "quant_img_RGB2BGR": False,
    }
    if quantize_type == "int8":
        config["quantized_dtype"] = "asymmetric_quantized-8"
    elif quantize_type == "fp16":
        config["quantized_dtype"] = "float16"
    else:
        config["quantized_dtype"] = "float32"
    return config


def collect_calibration_images(calib_dir: str, max_count: int = 20) -> list[str]:
    """收集 INT8 量化所需的标定图片路径"""
    if not os.path.isdir(calib_dir):
        print(f"[WARN] 标定目录不存在: {calib_dir}, 跳过量化标定")
        return []
    exts = (".jpg", ".jpeg", ".png", ".bmp")
    images = sorted(
        os.path.join(calib_dir, f)
        for f in os.listdir(calib_dir)
        if f.lower().endswith(exts)
    )
    selected = images[:max_count]
    print(f"[INFO] 标定图片: {len(selected)} 张 (来自 {calib_dir})")
    return selected


def write_dataset_file(image_paths: list[str]) -> str:
    """rknn.build() 的 dataset 参数需要一份 txt 文件，每行一张图片路径"""
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
    for p in image_paths:
        tmp.write(p + "\n")
    tmp.close()
    return tmp.name


def main():
    parser = argparse.ArgumentParser(description="ONNX -> RKNN 模型转换")
    parser.add_argument(
        "--onnx", default=ONNX_PATH,
        help=f"ONNX 模型路径 (默认: {ONNX_PATH})"
    )
    parser.add_argument(
        "--rknn", default=RKNN_PATH,
        help=f"输出 RKNN 路径 (默认: {RKNN_PATH})"
    )
    parser.add_argument(
        "--fp16", action="store_true",
        help="FP16 量化 (默认 INT8)"
    )
    parser.add_argument(
        "--no-quant", action="store_true",
        help="不量化 (FP32)"
    )
    parser.add_argument(
        "--calib-dir", default=CALIB_DIR,
        help=f"标定图片目录 (默认: {CALIB_DIR})"
    )
    parser.add_argument(
        "--calib-size", type=int, default=20,
        help="标定用图片数量 (默认: 20)"
    )
    parser.add_argument(
        "--target", default="rk3588",
        help="目标平台 (默认: rk3588, Orange Pi 5 Pro 的 SoC)"
    )
    args = parser.parse_args()

    if args.no_quant:
        quant_type = "fp32"
    elif args.fp16:
        quant_type = "fp16"
    else:
        quant_type = "int8"
    print(f"[INFO] 量化类型: {quant_type}")
    print(f"[INFO] 目标平台: {args.target}")

    if not os.path.exists(args.onnx):
        print(f"[ERROR] ONNX 模型不存在: {args.onnx}")
        sys.exit(1)

    rknn = RKNN(verbose=False)
    config = create_rknn_config(quant_type, args.target)
    print("[INFO] RKNN config:", config)

    ret = rknn.config(**config)
    if ret != 0:
        print("[ERROR] rknn.config 失败")
        sys.exit(1)

    print(f"[INFO] 加载 ONNX: {args.onnx}")
    ret = rknn.load_onnx(model=args.onnx)
    if ret != 0:
        print("[ERROR] 加载 ONNX 失败")
        sys.exit(1)

    print("[INFO] 构建 RKNN 模型 ...")

    do_quant = (quant_type == "int8")
    dataset_file = None
    if do_quant:
        calib_images = collect_calibration_images(args.calib_dir, args.calib_size)
        if calib_images:
            dataset_file = write_dataset_file(calib_images)
            print(f"[INFO] 标定数据集: {dataset_file}")
        else:
            print("[WARN] 无标定图片, INT8 量化将使用随机标定")

    ret = rknn.build(
        do_quantization=do_quant,
        dataset=dataset_file,
    )
    if ret != 0:
        print("[ERROR] 构建 RKNN 模型失败")
        if dataset_file and os.path.exists(dataset_file):
            os.unlink(dataset_file)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.rknn), exist_ok=True)
    print(f"[INFO] 导出 RKNN: {args.rknn}")
    ret = rknn.export_rknn(args.rknn)
    if ret != 0:
        print("[ERROR] 导出失败")
        if dataset_file and os.path.exists(dataset_file):
            os.unlink(dataset_file)
        sys.exit(1)

    if dataset_file and os.path.exists(dataset_file):
        os.unlink(dataset_file)

    print("[INFO] 推理精度验证 ...")
    try:
        ret = rknn.accuracy_analysis()
        if ret != 0:
            print("[WARN] accuracy_analysis 执行异常, 但模型已导出")
        else:
            print("[INFO] 精度验证完成")
    except Exception as e:
        print(f"[WARN] 精度验证跳过 ({e})")

    rknn.release()

    size_mb = os.path.getsize(args.rknn) / 1024 / 1024
    print()
    print("=" * 56)
    print(f"  [SUCCESS] 转换完成!")
    print(f"  输出: {args.rknn}")
    print(f"  大小: {size_mb:.1f} MB")
    print(f"  类型: {quant_type.upper()}")
    print("=" * 56)
    print()
    print("下一步:")
    print(f"  1. 将 {args.rknn} 传到 Orange Pi 上")
    print(f"  2. 修改 config.json 中 model.backend 为 \"rknn\"")
    print(f"  3. 在 Orange Pi 上安装: pip install rknn-toolkit-lite2")
    print(f"  4. 运行: python main_gui.py")


if __name__ == "__main__":
    main()
