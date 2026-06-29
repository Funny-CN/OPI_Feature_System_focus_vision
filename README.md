# 螺丝特征筛选视觉系统（Orange Pi 5 Pro 移植版）

基于香橙派 5 Pro 的螺丝精密尺寸测量与自动筛选系统。
原项目从树莓派 4B 移植至此平台。

## 方案概述

本系统计划采用"AI 定位 + 传统 CV 精测"的双阶段融合架构：

**模式一：直接选择模式**
用户在界面中从已建档的螺丝列表直接选择目标型号，系统根据数据库中记录的尺寸参数直接调整 V 型槽开口宽度，无需拍照测量。

**模式二：智能匹配模式**
1. **AI 检测阶段（NPU 推理）**
   轻量 YOLO 模型在 RK3585 NPU 上实时推理，检测螺丝在画面中的位置（单类检测，不做分类区分），输出检测框坐标。

2. **传统 CV 精测阶段（CPU 运行）**
   在检测框 ROI 区域内，使用传统计算机视觉方法做亚像素级边缘检测与轮廓拟合，精确计算螺丝的直径、长度等尺寸参数，通过固定的像素-毫米标定系数换算为物理尺寸。

3. **数据库匹配阶段**
   将测量结果与预先录入的螺丝型号数据库进行比对，匹配到最接近的型号，给出筛选方案并展示在界面上，经用户确认后执行硬件分拣。

### 数据处理流水线

```
USB 摄像头 / 本地图片
        |
        v
  +-------------------------+
  |  AI 检测模块 (NPU)       |
  |  YOLOv5n -> RKNN        |
  |  输出: 螺丝检测框        |
  +-------------------------+
               |
               v
  +-------------------------+
  |  ROI 裁剪 + CV 精密测量   |
  |  边缘检测 -> 轮廓拟合      |
  |  输出: 直径/长度/宽度      |
  +-------------------------+
               |
               v
  +-------------------------+
  |  螺丝型号数据库匹配        |
  |  匹配到: M6x12 盘头螺丝    |
  +-------------------------+
               |
               v
  +-------------------------+
  |  GUI 展示 + 用户确认       |
  |  显示筛选方案             |
  +-------------------------+
               |
               v
  +-------------------------+
  |  硬件执行                 |
  |  V 型槽开口 + 振动落料     |
  +-------------------------+
```

## 项目架构

```
OPI_Feature_System_focus_vision/
├── main.py                 # CLI 主入口（命令行模式）
├── main_gui.py             # GUI 主入口（新版默认：PySide6 + QML）
├── main_gui_qml.py         # 新版 QML 入口备份副本
├── main_gui_pyqt6.py       # 旧版 PyQt6 入口（回滚用）
├── run.bat                 # 双击启动新版 QML UI
├── run_legacy.bat          # 双击启动旧版 PyQt6 UI
├── config.json             # 配置文件
├── enviroment.txt          # Conda 环境说明
├── .gitignore
├── README.md
├── requirements.txt        # 依赖库文件
├── AI+CV.pdf               # AI+CV 方案计划书
│
├── core/
│   ├── __init__.py
│   └── detector.py         # 核心视觉算法：检测与测量
│
├── hardware/
│   ├── __init__.py
│   └── hardware_stub.py    # 硬件接口（Orange Pi 5 Pro GPIO 适配）
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py      # 旧版 PyQt6 Widgets 界面
│   ├── vision_backend.py   # ★ 新版：PySide6 后端隔离层
│   └── VisionUI.qml        # ★ 新版：QML 深色玻璃质感界面
│
└── samples/                # 存放待测量螺丝静态图
```

## 功能模块

### 视觉检测模块 (core/detector.py)
- **目标采样阶段**：提取像素长度、直径、HSV 特征并锁定目标标准
- **实时比对阶段**：实现当前特征与目标特征的逻辑比对
- 支持特征提取：像素长度、直径、HSV 颜色特征
- 支持特征比对：基于阈值的匹配判断
- **AI 扩展（规划中）**：后续接入 YOLO 模型执行螺丝检测与类型分类（NPU 推理），输出检测框和分类标签后传给传统 CV 做精测

### GUI 模块（新版 — PySide6 + QML）
- **架构**：QML ← 属性/信号 → VisionBackend → ScrewDetector
- **风格**：深色基底 + 玻璃卡片 + 蓝紫渐变强调 + 霓虹光晕
- **预留接口**：长宽测量、AI 检测结果、置信度等
- **画面源**：当前从 samples/ 读取静态图片，后续可替换为摄像头实时画面

### GUI 模块（旧版 — PyQt6 Widgets）
- 基于 QMainWindow 的传统 Widgets 界面
- 保留作为新版 QML 界面的回滚方案

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

采用一次性固定标定方案。在摄像头最终安装高度固定后，将一枚已知直径的硬币（如 1 元硬币，直径 25mm）放置在拍摄区域，系统自动识别并计算像素-毫米转换系数 pixel_to_mm_ratio。标定参数存储于 config.json 的 calibration 字段。后续日常使用无需重复标定，测量值直接通过该系数换算为物理尺寸。照片拍摄阶段不需要放置参照物。

## GUI 版本说明

本项目维护两个 GUI 版本，可共存切换：

| 版本 | 框架 | 入口文件 | 启动方式 |
|---|---|---|---|
| **新版（默认）** | PySide6 + QML | main_gui.py | python main_gui.py 或双击 run.bat |
| 旧版（回滚） | PyQt6 + Widgets | main_gui_pyqt6.py | python main_gui_pyqt6.py 或双击 run_legacy.bat |

## 开发计划

### 阶段一：数据准备（规划中）
- 拍摄 80-120 张俯视螺丝照片（纯色背景，不放参照物）
- 使用 LabelImg 标注螺丝位置，全部标注为同一类别 "screw"

### 阶段二：模型训练（规划中）
- 训练 YOLOv5n 单类检测模型
- 导出 ONNX，转换为 RKNN INT8 量化模型

### 阶段三：PC 端系统开发（规划中）
- 实现 YOLO + CV 融合测量流水线
- 建立螺丝型号数据库模块（手动建档录入尺寸）
- 实现两种操作模式（直接选择/智能匹配）
- 完善 GUI 界面（结果展示/方案确认/档案管理）

### 阶段四：部署与联调（规划中）
- 在 Orange Pi 5 Pro 上部署 RKNN 模型
- 接入 USB 摄像头实时画面
- 完整流水线联调

### 阶段五：硬件整合（规划中）
- V 型槽 + 步进电机 + 振动电机安装
- 光电传感器（或定时方案）判断筛选完成
- 软硬件联动测试

## 使用说明

### 启动 GUI

```bash
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

1. 将目标螺丝图片放入 samples/ 文件夹
2. 修改 config.json 配置目标标准特征
3. 启动 GUI 后，通过"下一个样本"按钮切换图片，"开始分析"进行检测

## 技术栈

- Python 3.x
- OpenCV（视觉处理）
- NumPy（数值计算）
- Orange Pi 5 Pro（硬件平台，Rockchip RK3585）
- PySide6 + QML（新版 GUI）
- PyQt6 + Widgets（旧版 GUI）
- OPi.GPIO / python3-gpiod（GPIO 控制）
- YOLO / RKNN Toolkit 2（AI 检测，单类，规划中）
- JSON / SQLite（螺丝型号数据库）

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
| 视觉方案 | 纯传统 CV | AI 检测 + CV 精测 + 数据库匹配 |
