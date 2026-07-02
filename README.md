# 螺丝特征筛选视觉系统（Orange Pi 5 Pro 移植版）

基于 Orange Pi 5 Pro 的螺丝精密尺寸测量与自动筛选系统。
原项目从树莓派 4B 移植至此平台。

## 方案概述

采用 **"AI 定位 + 传统 CV 精测"** 的双阶段融合架构，当前已实现并验证全流程贯通。

**模式一：直接选择模式**
用户在界面中从已建档的螺丝列表直接选择目标型号，系统根据数据库中记录的尺寸参数直接调整 V 型槽开口宽度，无需拍照测量。

**模式二：智能匹配模式**
1. **AI 检测阶段**（当前 ONNX Runtime，部署后切换 RKNN NPU）
   训练好的 YOLOv5s 模型检测螺丝在画面中的位置（单类检测），输出检测框坐标。

2. **传统 CV 精测阶段**
   在检测框 ROI 区域内，做亚像素级边缘检测与轮廓拟合，精确计算螺丝的直径、长度、宽度等尺寸参数，通过像素-毫米标定系数换算为物理尺寸。

3. **数据库匹配阶段**
   将测量结果与预先录入的螺丝型号数据库进行比对，匹配到最接近的型号并展示在界面上，经用户确认后执行硬件分拣。

### 数据处理流水线

```
USB 摄像头 / 本地图片（当前使用 samples/ 静态图）
        |
        v
  +-------------------------+
  |  AI 检测模块            |
  |  YOLOv5s -> ONNX        |  当前 ONNX Runtime，部署后切 RKNN
  |  输出: 螺丝检测框        |
  +-------------------------+
               |
               v
  +-------------------------+
  |  ROI 裁剪 + CV 精密测量   |
  |  Canny 边缘检测 + 轮廓拟合 |
  |  输出: 直径/长度/宽度      |
  +-------------------------+
               |
               v
  +-------------------------+
  |  螺丝型号数据库匹配        |
  |  config.json 预置 4 种型号 |
  +-------------------------+
               |
               v
  +-------------------------+
  |  GUI 展示 + 用户确认       |
  |  PySide6 / PyQt5 界面     |
  +-------------------------+
               |
               v
  +-------------------------+
  |  硬件执行（待硬件联调）     |
  |  V 型槽开口 + 振动落料     |
  +-------------------------+
```

## 项目架构

```
OPI_Feature_System_focus_vision/
+-- core/                      >> 核心模块
|   +-- detector.py            >> 协调控制器 -- AI > CV > DB 三阶段流水线
|   +-- ai_detector.py         >> AI 检测模块（ONNX / RKNN / Torch 三后端）
|   +-- measurement.py         >> CV 精密测量模块（边缘检测 + 轮廓拟合）
|   +-- database.py            >> 螺丝型号数据库模块（CRUD + 匹配）
|
+-- hardware/
|   +-- hardware_stub.py       硬件接口（GPIO 占位，待硬件联调）
|
+-- ui/
|   +-- main_window.py         旧版 PyQt6 Widgets 界面（回滚备份）
|   +-- vision_backend.py      >> 新版 PySide6 后端隔离层
|   +-- VisionUI.qml           >> 新版 QML 深色玻璃质感界面
|
+-- yolo/                      >> YOLO 模型与数据集
|   +-- weights/
|   |   +-- best.pt            >> 训练好的模型权重（56.7 MB）
|   |   +-- best.onnx          >> 导出的 ONNX 模型（27.5 MB）
|   +-- configs/
|   |   +-- model.yaml         模型结构定义（YOLOv5s, nc=1）
|   |   +-- hyp.yaml           训练超参数
|   +-- dataset/
|       +-- images/train/      84 张训练图片
|       +-- images/val/        21 张验证图片
|       +-- labels/train/      84 个训练标注 (YOLO 格式)
|       +-- labels/val/        21 个验证标注
|
+-- scripts/
|   +-- convert_rknn.py        >> ONNX > RKNN 模型转换脚本（待运行）
|   +-- calibrate.py           >> 硬币标定脚本（1 元硬币 25mm 参考物）
|   +-- __init__.py
|
+-- samples/                   存放待测样本图片
+-- models/                    （保留目录，未来存放 RKNN 模型）
|
+-- main.py                    CLI 主入口（命令行模式，尚未适配 AI 流水线）
+-- main_gui.py                GUI 主入口（PySide6 + QML，PC 端）
+-- main_gui_pyqt6.py          旧版 PyQt6 入口（回滚用）
+-- run.bat                    双击启动新版 QML UI
+-- run_legacy.bat             双击启动旧版 PyQt6 UI
+-- config.json                配置文件（含螺丝型号数据库与模型配置）
+-- enviroment.txt             Conda 环境说明
+-- requirements.txt           依赖库文件
+-- .gitignore
+-- README.md
```

## 当前进度（2026-07-03 更新）

```
   核心流水线（AI > CV > DB）  ################....  80%
   AI 模型（已训练 + ONNX）     ####################  100%
   AI > GUI 适配               ################....  80%
   标定（Orange Pi 已标定）      ######............  30%
   数据集（已标注 105 张）       ####................  20%
   项目部署到 Orange Pi         ####################  100%
   Orange Pi 环境搭建           ####################  100%
   摄像头接入 + 拍照验证         ####################  100%
   RKNN 模型转换                ##..................  10%
   CV 精测参数调优               ###.................  15%
   V 型槽 + 步进电机            ....................   0%
   振动落料 + 硬件分拣          ....................   0%
```

### 已完成
- [x] YOLOv5s 模型训练（84 张训练图，21 张验证图）+ ONNX 导出
- [x] ai_detector.py：支持 ONNX / RKNN / Torch 三后端
- [x] measurement.py：亚像素边缘检测 + 轮廓拟合
- [x] detector.py：AI > CV > DB 三阶段流水线协调
- [x] 全流水线（AI > CV 精测 > DB 匹配）在 Windows 上调通
- [x] QML UI 适配：AI 信息面板 + 检测来源指示
- [x] 项目代码完整部署到 Orange Pi 5 Pro
- [x] Orange Pi 环境搭建：Python 3.10 + OpenCV + PyQt5 + ONNX Runtime
- [x] AI 模型在 Orange Pi 上成功加载并运行（CPUExecutionProvider）
- [x] USB 摄像头接入 Orange Pi 并成功拍照
- [x] 硬币标定（1 元硬币 25mm）=> pixel_to_mm_ratio = 6.24
- [x] scripts/convert_rknn.py：ONNX > RKNN 转换脚本
- [x] scripts/calibrate.py：硬币自动标定脚本
- [x] 双端开发调试工作流建立（PC 改代码 + Orange Pi 验证）
- [x] GitHub 做版本管理主通道（git push / git pull）

### 进行中
- [ ] CV 精测参数调优：检测框偏大导致测量值偏大，需调整
- [ ] Hough 圆检测参数适配新摄像头
- [ ] 扩建数据集：补拍 200-300 张现场照片后重训模型

### 待完成
- [ ] RKNN 模型转换（onnx > rknn）并在 Orange Pi 5 Pro 上部署
- [ ] 摄像头标定重新确认（如有需要重跑 calibrate.py）
- [ ] main.py 更新为 AI 流水线
- [ ] 硬件模块联调（步进电机、V 型槽、振动落料）

## 双端开发工作流

本项目的开发模式是 **PC 端写代码调算法，Orange Pi 端部署验证**。

```
PC (Windows)                    Orange Pi 5 Pro
Python 3.10 + conda             Python 3.10 + pip
PySide6 + QML                   PyQt5（apt 安装）
ONNX Runtime                    ONNX Runtime
OpenCV / NumPy / SciPy          同左
无硬件模块                       GPIO 接口 (OPi.GPIO)

代码改动 -> git push              -> git pull
         -> scp 单文件             -> 直接覆盖
```

**注意**：
- 核心算法（core/ 目录）纯 Python，两边代码完全一致
- 配置文件 config.json 需要两边保持一致（特别是 pixel_to_mm_ratio）
- GUI 层 PC 用 PySide6，Orange Pi 用 PyQt5，算法调试建议用命令行模式

## 标定说明

### 硬币标定（已完成）

2026-07-03 在 Orange Pi 上使用 1 元硬币（25mm）完成标定：

| 项目 | 值 |
|---|---|
| 硬币像素直径 | 156 px |
| 物理直径 | 25.0 mm |
| pixel_to_mm_ratio | **6.24** |
| 旧值 | 0.05（旧摄像头数据） |

重新标定只需在 Orange Pi 上运行：

```bash
cd ~/OPI_Feature_System_focus_vision
python3 calibrate.py
```

把 1 元硬币放在摄像头下方，按 Enter 即可自动计算并更新 config.json。

## 使用说明

### PC 端调试

```bash
conda activate opi_vision

# 使用样本图片运行全流水线检测
python -c "
import cv2
from core.detector import ScrewDetector
detector = ScrewDetector()
img = cv2.imread('samples/sample_01.jpg')
result = detector.analyze(img)
print('螺丝数:', result.screw_count)
for s in result.screws:
    print(f'直径: {s.measurement.diameter:.1f}mm')
"

# 启动 GUI
python main_gui.py
```

### Orange Pi 端部署

```bash
cd ~/OPI_Feature_System_focus_vision

# 命令行检测（拍照模式）
python3 -c "
import cv2
from core.detector import ScrewDetector
cam = cv2.VideoCapture(0)
input('放好螺丝后按 Enter 拍照...')
ret, frame = cam.read()
cam.release()
detector = ScrewDetector()
result = detector.analyze(frame)
print('螺丝数:', result.screw_count)
for s in result.screws:
    print(f'直径: {s.measurement.diameter:.1f}mm')
"
```

## 模型训练情况

| 项目 | 内容 |
|---|---|
| 基础模型 | YOLOv5s（从预训练权重微调） |
| 训练数据 | 84 张训练 + 21 张验证（俯拍螺丝照片） |
| 标注格式 | YOLO 格式 `.txt`，单类 "screw" |
| 训练轮数 | 100 epochs，输入尺寸 640x640 |
| 输出格式 | .pt > .onnx (ONNX opset 17, 27.5 MB) |
| 待完成 | 训练数据仅 84 张，偏少。部署后建议补拍 200-300 张重训 |
| 待完成 | 当前仅为 ONNX 格式，部署到 Orange Pi 前需转 RKNN |

## RKNN 模型转换

转换脚本已就绪：`scripts/convert_rknn.py`。在 x86 Linux 或 WSL2 上运行：

```bash
# 安装 rknn-toolkit2
pip install rknn-toolkit2

# 转换（默认 INT8 量化，推荐）
python scripts/convert_rknn.py

# 或 FP16 量化
python scripts/convert_rknn.py --fp16
```

转换后将 `models/best.rknn` 传到 Orange Pi，修改 `config.json` 中 `model.backend` 为 `"rknn"`，并在 Orange Pi 上安装 `rknn-toolkit-lite2` 即可。

## 技术栈

| 领域 | 技术 | 状态 |
|---|---|---|
| AI 检测 | YOLOv5s + ONNX Runtime | 已接入 |
| CV 精测 | OpenCV（Canny + 轮廓拟合） | 已实现 |
| 数据库 | JSON（config.json 内嵌） | 已实现 |
| GUI（PC 端） | PySide6 + QML | 已适配 AI |
| GUI（Orange Pi） | PyQt5 | 可用 |
| 部署平台 | Orange Pi 5 Pro（Rockchip RK3585） | 已部署 |
| NPU 推理 | RKNN Toolkit Lite2 | 待转换与部署 |
| 硬件控制 | OPi.GPIO / gpiod | 待硬件联调 |
| 模型训练 | PyTorch + YOLOv5 | 已完成 |

## 依赖安装

### PC 端（Conda 推荐）

```bash
conda create -n opi_vision python=3.10
conda activate opi_vision
pip install -r requirements.txt
```

### Orange Pi 5 Pro

```bash
# 核心依赖
pip3 install opencv-python numpy scipy matplotlib pillow
pip3 install onnxruntime

# GUI（apt 安装更稳定）
sudo apt-get install python3-pyqt5 -y

# NPU 推理（部署 RKNN 时安装）
# pip3 install rknn-toolkit-lite2

# 硬件控制
# pip3 install OPi.GPIO
```

## 关于迁移（树莓派 4B > Orange Pi 5 Pro）

| 方面 | 树莓派 4B | Orange Pi 5 Pro |
|---|---|---|
| SoC | Broadcom BCM2711 | Rockchip RK3585 |
| NPU | 无 | 6 TOPS（支持 INT8 量化推理） |
| GPIO 库 | RPi.GPIO / pigpio | OPi.GPIO / python3-gpiod |
| 引脚编号 | BCM 方案 | BOARD 物理编号 |
| 舵机控制 | pigpio 硬件 PWM | 软件 PWM |
| 摄像头 | libcamera / picamera2 | V4L2 / Rockchip MPP |
| 视觉方案 | 纯传统 CV | AI 检测 + CV 精测 + 数据库匹配 |
