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
  |  YOLOv5s -> ONNX        |  ← 当前 ONNX Runtime，部署后切 RKNN
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
  |  PySide6 + QML 界面       |
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
├── core/                      ★ 核心模块
│   ├── detector.py            ★ 协调控制器 — AI → CV → DB 三阶段流水线
│   ├── ai_detector.py         ★ AI 检测模块（ONNX / RKNN / Torch 三后端）
│   ├── measurement.py         ★ CV 精密测量模块（边缘检测 + 轮廓拟合）
│   └── database.py            ★ 螺丝型号数据库模块（CRUD + 匹配）
│
├── hardware/
│   └── hardware_stub.py       硬件接口（GPIO 占位，待硬件联调）
│
├── ui/
│   ├── main_window.py         旧版 PyQt6 Widgets 界面（回滚备份）
│   ├── vision_backend.py      ★ 新版 PySide6 后端隔离层
│   └── VisionUI.qml           ★ 新版 QML 深色玻璃质感界面
│
├── yolo/                      ★ YOLO 模型与数据集
│   ├── weights/
│   │   ├── best.pt            ★ 训练好的模型权重（56.7 MB）
│   │   └── best.onnx          ★ 导出的 ONNX 模型（27.5 MB）
│   ├── configs/
│   │   ├── model.yaml         模型结构定义（YOLOv5s, nc=1）
│   │   └── hyp.yaml           训练超参数
│   └── dataset/
│       ├── images/train/      84 张训练图片
│       ├── images/val/        21 张验证图片
│       ├── labels/train/      84 个训练标注 (YOLO 格式)
│       └── labels/val/        21 个验证标注
│
├── scripts/                   工具脚本（标定/训练/转换）
├── samples/                   存放待测样本图片（当前为 5 张俯拍验证图）
│
├── models/                    （保留目录，未来存放 RKNN 模型）
├── main.py                    CLI 主入口（命令行模式）
├── main_gui.py                GUI 主入口（PySide6 + QML）
├── main_gui_pyqt6.py          旧版 PyQt6 入口（回滚用）
├── run.bat                    双击启动新版 QML UI
├── run_legacy.bat             双击启动旧版 PyQt6 UI
├── config.json                配置文件（含螺丝型号数据库与模型配置）
├── enviroment.txt             Conda 环境说明
├── requirements.txt           依赖库文件
├── .gitignore
└── README.md
```

## 功能模块

### AI 检测模块 (core/ai_detector.py)
- **状态：已完成并接入流水线**
- 支持三后端：`onnx`（Windows 开发用）、`rknn`（Orange Pi 部署用，待接入）、`torch`（调试用）
- 自动根据 `config.json` 的 `model.backend` 字段选择后端
- 完整的前处理（letterbox 缩放 + 归一化）和后处理（NMS 去重 + 坐标映射回原图）
- 模型置信度和检测数通过 `last_confidence`、`last_box_count` 属性暴露给 UI

### 视觉检测模块 (core/detector.py)  
- 协调 AI 检测 → CV 精测 → 数据库匹配三阶段流水线
- AI 加载失败或未检测到螺丝时，自动回退到 Hough 圆检测
- 标注结果图（绿框=匹配成功，红框=未匹配）
- **待完成**：CV 精测在当前样本上的标定参数不匹配，部署后需用硬币重新标定

### GUI 模块（新版 — PySide6 + QML）
- **架构**：QML ← 属性/信号 → VisionBackend → ScrewDetector
- **风格**：深色基底 + 玻璃卡片 + 蓝紫渐变强调
- **包含 AI 信息面板**：Page 0 显示检测来源（AI/Hough），Page 1 显示实时 AI 状态、后端类型、置信度、检测数
- **画面源**：当前从 `samples/` 读取静态图片，**后续需替换为摄像头实时画面**

### GUI 模块（旧版 — PyQt6 Widgets）
- 基于 QMainWindow 的传统 Widgets 界面，保留作为回滚方案

### 硬件控制模块 (hardware/hardware_stub.py)
- 步进电机、舵机、限位开关接口已定义
- **状态：待硬件联调**——当前为 GPIO 占位实现，无物理硬件时进入模拟模式

### 主程序 (main.py)
- **注意**：当前 `main.py` 调用的是旧版 Hough 圆检测流程，**尚未适配新版 AI 流水线**
- 新版 GUI 启动请使用 `python main_gui.py`

## 模型训练情况

| 项目 | 内容 |
|---|---|
| 基础模型 | YOLOv5s（从预训练权重微调） |
| 训练数据 | 84 张训练 + 21 张验证（俯拍螺丝照片） |
| 标注格式 | YOLO 格式 `.txt`，单类 "screw" |
| 训练轮数 | 100 epochs，输入尺寸 640×640 |
| 输出格式 | .pt → .onnx (ONNX opset 17, 27.5 MB) |
| **待完成** | ⚠️ 训练数据仅 84 张，偏少。部署后建议补拍 200-300 张重训 |
| **待完成** | ⚠️ 当前仅为 ONNX 格式，部署到 Orange Pi 前需转 RKNN |

## 标定策略

采用一次性固定标定方案。摄像头安装高度固定后，将一枚已知直径的硬币（如 1 元硬币，直径 25mm）放置在拍摄区域，系统自动识别并计算像素-毫米转换系数 `pixel_to_mm_ratio`。

**当前状态**：`config.json` 中的 `pixel_to_mm_ratio: 0.05` 是旧摄像头的数据，与新样片不匹配。部署实际摄像头后需重新标定。

测量模块已内置标定方法 `PrecisionMeasurer.calibrate_from_reference()`，自动检测硬币并计算新系数。

## GUI 版本说明

| 版本 | 框架 | 入口文件 | AI 适配 |
|---|---|---|---|
| **新版（默认）** | PySide6 + QML | `main_gui.py` | ✅ 已适配 |
| 旧版（回滚） | PyQt6 + Widgets | `main_gui_pyqt6.py` | ❌ 未适配 |

## 当前进度

```
   核心流水线（AI → CV → DB）  ████████████████░░░░  80%
   AI 模型（已训练 + ONNX）     ████████████████████  100%
   AI → GUI 适配               ████████████████░░░░  80%
   标定（参数待更新）           ██░░░░░░░░░░░░░░░░░░  10%
   数据集（已标注 105 张）       ████░░░░░░░░░░░░░░░░  20%
   RKNN 部署到 Orange Pi       ░░░░░░░░░░░░░░░░░░░░   0%
   摄像头实时画面                ░░░░░░░░░░░░░░░░░░░░   0%
   V 型槽 + 步进电机            ░░░░░░░░░░░░░░░░░░░░   0%
   振动落料 + 硬件分拣          ░░░░░░░░░░░░░░░░░░░░   0%
```

### 已完成
- [x] YOLOv5s 模型训练（84 张训练图，21 张验证图）
- [x] 模型导出为 ONNX 格式
- [x] `ai_detector.py` 重写：支持 ONNX / RKNN / Torch 三后端
- [x] `measurement.py` 修复：补上 `@dataclass` 装饰器
- [x] `detector.py` 更新：自动从 `config.json` 加载 AI 模型
- [x] `config.json` 重构成带 `model.backend` 等字段的新结构
- [x] 全流水线（AI → CV 精测 → DB 匹配）在 Windows 上调通
- [x] QML UI 适配：Page 0 检测来源指示 + Page 1 AI 实时数据面板
- [x] `requirements.txt` 添加 `onnxruntime` 依赖

### 进行中
- [ ] 部署后摄像头重新标定（硬币标定法）
- [ ] 扩建数据集：补拍 200-300 张现场照片后重训模型

### 待完成
- [ ] RKNN 模型转换（`.onnx` → `.rknn`）并在 Orange Pi 5 Pro 上部署
- [ ] 接入 USB 摄像头实时画面
- [ ] 硬件模块联调（步进电机、V 型槽、振动落料）
- [ ] `main.py` 更新为 AI 流水线
- [ ] 数据增强 + 模型迭代优化

## 使用说明

### 启动 GUI

```bash
conda activate opi_vision

# 新版 QML UI（推荐，AI 已适配）
python main_gui.py

# 或双击 run.bat

# 旧版 PyQt6 UI（回滚用，无 AI 适配）
python main_gui_pyqt6.py
```

### CLI 模式（无 GUI，尚未适配 AI）

```bash
python main.py
```

### 数据准备

1. 将待测螺丝俯拍图片放入 `samples/` 文件夹（与训练数据同视角效果更好）
2. 修改 `config.json` 中的 `screws` 字段配置螺丝型号
3. 启动 GUI 后，点击 "开始分析" 即可执行 AI → CV 测量 → 数据库匹配全流程

## 技术栈

| 领域 | 技术 | 状态 |
|---|---|---|
| AI 检测 | YOLOv5s + ONNX Runtime | ✅ 已接入 |
| CV 精测 | OpenCV（Canny + 轮廓拟合） | ✅ 已实现 |
| 数据库 | JSON（config.json 内嵌） | ✅ 已实现 |
| GUI（新版） | PySide6 + QML | ✅ 已适配 AI |
| GUI（旧版） | PyQt6 + Widgets | ❌ 未适配 |
| 部署平台 | Orange Pi 5 Pro（Rockchip RK3585） | ⏳ 待部署 |
| NPU 推理 | RKNN Toolkit Lite2 | ⏳ 待转换与部署 |
| 硬件控制 | OPi.GPIO / gpiod | ⏳ 待硬件联调 |
| 模型训练 | PyTorch + YOLOv5 | ✅ 已完成 |

## 模型转换链路

```
Windows 开发： .pt ──export.py──▶ .onnx ──onnxruntime──▶ 推理
                                        （当前链路，已验证）

Orange Pi 部署：.pt ──export.py──▶ .onnx ──rknn-toolkit2──▶ .rknn ──rknnlite──▶ NPU 推理
                                        （待转换）            （待部署）
```

- 转换脚本入口预留：`scripts/export_onnx.py`（导出 ONNX）、`scripts/convert_rknn.py`（ONNX → RKNN，待实现）
- PC 端使用 `rknn-toolkit2` 转换，Orange Pi 上使用 `rknn-toolkit-lite2` 推理

## 依赖安装

```bash
pip install -r requirements.txt
```

### 开发环境（Conda 推荐）

```bash
conda create -n opi_vision python=3.10
conda activate opi_vision
pip install -r requirements.txt
```

### Orange Pi 5 Pro 特定依赖

```bash
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip
pip install OPi.GPIO
pip install rknn-toolkit-lite2    # NPU 推理
```

## 关于迁移（树莓派 4B → Orange Pi 5 Pro）

| 方面 | 树莓派 4B | Orange Pi 5 Pro |
|---|---|---|
| SoC | Broadcom BCM2711 | Rockchip RK3585 |
| NPU | 无 | 6 TOPS（支持 INT8 量化推理） |
| GPIO 库 | RPi.GPIO / pigpio | OPi.GPIO / python3-gpiod |
| 引脚编号 | BCM 方案 | BOARD 物理编号 |
| 舵机控制 | pigpio 硬件 PWM | 软件 PWM |
| 摄像头 | libcamera / picamera2 | V4L2 / Rockchip MPP |
| 视觉方案 | 纯传统 CV | AI 检测 + CV 精测 + 数据库匹配 ✅ |
