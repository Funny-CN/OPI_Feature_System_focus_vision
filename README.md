# 螺丝特征筛选视觉系统（Orange Pi 5 Pro 移植版）

基于香橙派 5 Pro 的螺丝精密尺寸测量系统，采用 **AI 定位 + 传统 CV 精测** 双阶段融合架构。
原项目从树莓派 4B 移植至此平台。

## 方案概述

本系统采用"AI 定位 + 传统 CV 精测"的双阶段融合架构：

1. **AI 检测阶段（NPU 推理）**
   轻量 YOLO 模型在 RK3585 NPU 上实时推理，鲁棒地检测螺丝在画面中的位置，输出检测框坐标。

2. **传统 CV 精测阶段（CPU 运行）**
   在检测框 ROI 区域内，使用传统计算机视觉方法做亚像素级边缘检测与轮廓拟合，精确计算螺丝的直径、长度等尺寸参数，通过固定的像素-毫米标定系数换算为物理尺寸。

### 数据处理流水线

```
USB 摄像头 / 本地图片
        |
        v
  +-------------------------+
  |  AI 检测模块 (NPU)       |
  |  YOLOv5n -> RKNN        |
  |  输出: 螺丝检测框         |
  +-------------------------+
               |
               v
  +-------------------------+
  |  ROI 裁剪                |
  +-------------------------+
               |
               v
  +-------------------------+
  |  传统 CV 测量模块 (CPU)   |
  |  边缘检测 -> 轮廓拟合      |
  |  像素-毫米换算            |
  |  输出: 直径/长度          |
  +-------------------------+
               |
               v
  +-------------------------+
  |  GUI 展示层              |
  |  实时画面 + 检测框叠加     |
  |  尺寸标注 + 统计数据       |
  +-------------------------+
               |
               v
          硬件分拣（远期）
```

## 项目架构

```
OPI_Feature_System_focus_vision/
├── main.py                     # CLI 主入口（无 GUI，命令行模式）
├── main_gui.py                 # GUI 主入口（新版默认：PySide6 + QML）
├── main_gui_qml.py             # 新版 QML 入口备份副本
├── main_gui_pyqt6.py           # 旧版 PyQt6 入口（回滚用）
├── run.bat                     # 双击启动新版 QML UI
├── run_legacy.bat              # 双击启动旧版 PyQt6 UI
├── config.json                 # 配置文件，存储目标标准特征数据和标定参数
├── enviroment.txt              # Conda 环境说明
├── .gitignore
├── README.md
├── requirements.txt            # 依赖库文件（含 PySide6 + PyQt6）
├── AI+CV.pdf                   # AI+CV 方案计划书
│
├── core/
│   ├── __init__.py
│   ├── detector.py             # 核心视觉算法：协调 AI + CV 两阶段流水线
│   ├── ai_detector.py          # ★ AI 检测模块（新建）：YOLO → RKNN NPU 推理
│   └── measurement.py          # ★ CV 精密测量模块（新建）：边缘检测 + 尺寸换算
│
├── hardware/
│   ├── __init__.py
│   └── hardware_stub.py        # 硬件接口（Orange Pi 5 Pro GPIO 适配）
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py          # 旧版 PyQt6 Widgets 界面（保留）
│   ├── vision_backend.py       # ★ 新版：PySide6 后端隔离层
│   └── VisionUI.qml            # ★ 新版：QML 深色玻璃质感界面
│
├── models/
│   ├── best.rknn               # ★ RKNN 量化模型（新建）
│   └── best.onnx               # ★ ONNX 模型（新建）
│
├── samples/                    # 存放待测量螺丝静态图
└── scripts/
    └── calibrate.py            # ★ 标定工具脚本（新建）
```

## 功能模块

### AI 检测模块 (core/ai_detector.py)
- **模型**：YOLOv5n / YOLOv8n
- **部署格式**：RKNN INT8 量化
- **推理后端**：Rockchip NPU（RKNN Toolkit 2）
- **功能**：输入一帧图像，返回螺丝检测框坐标

### CV 精密测量模块 (core/measurement.py)
- **方法**：Canny 边缘检测 + 轮廓拟合
- **标定策略**：一次性固定标定，标定系数存入 config.json 的 calibration 字段
- **功能**：在 ROI 区域内计算精密尺寸（直径、长度等）

### 协调控制器 (core/detector.py)
- 协调 AI + CV 两阶段流水线
- 组合检测框、尺寸、判定结果为统一输出

### 视觉检测模块 (core/detector.py 传统部分)
- **目标采样阶段**：提取像素长度、直径、HSV 特征并锁定目标标准
- **实时比对阶段**：实现当前特征与目标特征的逻辑比对
- 支持特征提取：像素长度、直径、HSV 颜色特征
- 支持特征比对：基于阈值的匹配判断

### GUI 模块（新版 — PySide6 + QML）
- **架构**：`QML` ← 属性/信号 → `VisionBackend` → `ScrewDetector`
- **风格**：深色基底 + 玻璃卡片 + 蓝紫渐变强调 + 霓虹光晕
- **预留接口**：长宽测量（`measuredLength` / `measuredWidth`）、AI 检测结果（`aiResultLabel` / `aiConfidence`）
- **画面源**：当前从 `samples/` 读取静态图片，后续可替换为摄像头实时画面

### 硬件控制模块 (hardware/hardware_stub.py)
- 步进电机接口：基于 OPi.GPIO / python3-gpiod 实现
- 舵机接口：基于软件 PWM 实现角度控制
- 硬件连接管理
- Orange Pi 5 Pro 物理引脚映射已内置

### 主程序 (main.py)
- 协调视觉检测和硬件控制
- 配置加载和参数管理
- 实时检测循环

## 标定策略

采用一次性固定标定方案。设备搭建完成后，将一枚已知直径的硬币或标准件放置在拍摄区域，系统自动识别并计算像素-毫米转换系数 pixel_to_mm_ratio。标定参数存储于 config.json 的 calibration 字段。后续日常使用无需重复标定，亦无需在每张图像中放置参照物。

## GUI 版本说明

本项目维护两个 GUI 版本，可共存切换：

| 版本 | 框架 | 入口文件 | 启动方式 |
|---|---|---|---|
| **新版（默认）** | PySide6 + QML | `main_gui.py` | `python main_gui.py` 或双击 `run.bat` |
| 旧版（回滚） | PyQt6 + Widgets | `main_gui_pyqt6.py` | `python main_gui_pyqt6.py` 或双击 `run_legacy.bat` |

三个入口文件（`main_gui.py` / `main_gui_qml.py` / `main_gui_pyqt6.py`）均接入了 `core/detector.py` 的核心检测逻辑。

## 开发计划

### 阶段一：数据准备
- 拍摄 50-100 张俯视螺丝照片（含参照物）
- 使用 LabelImg 标注螺丝位置
- 数据增强扩充训练集

### 阶段二：PC 端算法开发
- 调通传统 CV 测量模块
- 训练 YOLO 检测模型
- 实现 AI + CV 融合流水线
- 完善 GUI 界面

### 阶段三：模型部署
- ONNX 导出
- RKNN Toolkit 2 量化转换
- 在 Orange Pi 5 Pro 上验证 NPU 推理

### 阶段四：系统集成
- 接入 USB 摄像头实时画面
- 完整流水线联调
- FPS 性能优化

### 阶段五：硬件分拣（远期可选）
- 步进电机、舵机控制实现
- AI 检测结果 → 硬件动作联动

## 使用说明

### 启动 GUI

```bash
# 激活环境后运行

# 新版 QML UI（推荐）
python main_gui.py

# 或双击项目根目录的 run.bat

# 旧版 PyQt6 UI（回滚用）
python main_gui_pyqt6.py

# 或双击项目根目录的 run_legacy.bat
```

### CLI 模式（无 GUI）

```bash
python main.py
```

### 数据准备

1. 将目标螺丝图片放入 `samples/` 文件夹
2. 修改 `config.json` 配置目标标准特征
3. 启动 GUI 后，通过"下一个样本"按钮切换图片，"开始分析"进行检测

## 技术栈

- Python 3.x
- Ultralytics (YOLOv5n/v8n) — AI 检测模型
- PyTorch / ONNX — 模型训练与导出
- RKNN Toolkit 2 — Rockchip NPU 量化与推理
- OpenCV — 传统视觉处理与边缘检测
- NumPy — 数值计算
- Orange Pi 5 Pro（硬件平台，Rockchip RK3585）
- PySide6 + QML（新版 GUI，硬件加速）
- PyQt6 + Widgets（旧版 GUI，回滚备用）
- OPi.GPIO / python3-gpiod（GPIO 控制）

## 依赖安装

### 使用 pip 安装依赖

```bash
pip install -r requirements.txt
```

### 开发环境（Conda 推荐）

```bash
# 创建虚拟环境
conda create -n opi_vision python=3.10
conda activate opi_vision
pip install -r requirements.txt
```

### AI 模型训练与转换依赖（PC 端）

```bash
# 训练环境（Windows PC）
pip install ultralytics torch torchvision onnx onnxruntime

# RKNN 转换环境（x86 Linux / Windows WSL）
# 安装 RKNN Toolkit 2，参考瑞芯微官方文档
```

### Orange Pi 5 Pro 特定依赖

对于香橙派 5 Pro 硬件控制，需要额外安装：

```bash
# 安装 OPi.GPIO（RPi.GPIO 的香橙派移植版）
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip
pip install OPi.GPIO

# 或者安装 python3-gpiod（内核原生 GPIO 接口）
sudo apt-get install -y python3-libgpiod gpiod

# NPU 推理运行时
pip install rknn-toolkit-lite2

# 运行时建议以 root 或 gpio 用户组权限运行
```

## 关于迁移（树莓派 4B → Orange Pi 5 Pro）

本项目原基于树莓派 4B 开发，现已移植至香橙派 5 Pro。主要变更：

| 方面 | 树莓派 4B | Orange Pi 5 Pro |
|---|---|---|
| SoC | Broadcom BCM2711 | Rockchip RK3585 |
| APU | 无 | 6 TOPS NPU（支持 INT8 量化推理） |
| GPIO 库 | RPi.GPIO / pigpio | OPi.GPIO / python3-gpiod |
| 引脚编号 | BCM 方案 | BOARD 物理编号 |
| 舵机控制 | pigpio 硬件 PWM | 软件 PWM |
| 摄像头 | libcamera / picamera2 | V4L2 / Rockchip MPP |
| 视觉方案 | 纯传统 CV（Hough 检测 + 阈值比对） | AI 检测 + 传统 CV 融合测量 |

### 移植注意事项

- GPIO 引脚映射完全不同，`hardware/hardware_stub.py` 已使用 BOARD 物理编号
- 新版 GUI 基于 PySide6 + QML（Qt6），利用 Mali G610 GPU 硬件加速
- 旧版 PyQt6 保留作为回滚方案，两者可共存
- 建议使用 USB 摄像头（通用 V4L2 驱动），可最小化平台差异
- AI 模型训练和 RKNN 转换在 PC 上进行，Orange Pi 仅加载推理
- GPIO 操作需要 root 权限，运行时建议 `sudo python main.py`
