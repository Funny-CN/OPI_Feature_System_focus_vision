# 螺丝特征筛选视觉系统

基于 RK3588 的螺丝精密尺寸测量与自动筛选系统。

## 方案概述

采用 **"AI 定位 + 传统 CV 精测"** 的双阶段融合架构，当前已实现并验证全流程贯通。

**模式一：直接选择模式**
用户在界面中从已建档的螺丝列表直接选择目标型号，系统根据数据库中记录的尺寸参数直接调整 V 型槽开口宽度，无需拍照测量。

**模式二：智能匹配模式**
1. **AI 检测阶段**（当前 ONNX Runtime，部署后切换 RKNN NPU）
   训练好的 YOLOv5s 模型检测螺丝在画面中的位置（单类检测），输出检测框坐标。

2. **传统 CV 精测阶段**
   在检测框 ROI 区域内，做 Otsu 二值化掩码 + 宽度轮廓分析，精确计算螺丝的螺帽直径 (Head)、螺杆直径 (Shaft)、总长度 (Total Length) 等尺寸参数，通过像素-毫米标定系数换算为物理尺寸。

3. **数据库匹配阶段**
   将测量结果与预先录入的螺丝型号数据库进行比对，匹配到最接近的型号并展示在界面上，经用户确认后执行硬件分拣。

## 项目架构

```
OPI_Feature_System_focus_vision/
+-- core/                      >> 核心模块
|   +-- detector.py            >> 协调控制器 -- AI > CV > DB 三阶段流水线
|   +-- ai_detector.py         >> AI 检测模块（ONNX / RKNN / Torch 三后端）
|   +-- measurement.py         >> CV 精密测量模块（Otsu + 宽度轮廓分析）
|   +-- database.py            >> 螺丝型号数据库模块（CRUD + 匹配）
|
+-- hardware/                  >> 硬件适配层（自动检测环境，回退模拟模式）
|   +-- hardware_manager.py    >> 硬件管理器（连接/归零/分拣/紧急停止）
|   +-- opi_motor.py           >> 双路电机驱动模块（步进电机 + 振动电机，PWM）
|   +-- opi_sensor.py          >> 电阻尺 + 微动开关传感器模块（ADS1115）
|   +-- opi_ir.py              >> 红外传感器模块（E18-D80NK）
|
+-- ui/
|   +-- main_window.py         >> PyQt6 Widgets 界面（多螺丝列表/偏差颜色/模式切换/背景动画）
|   +-- main_window_pyqt5.py   >> PyQt5 移植版（功能对齐 PyQt6，Orange Pi 部署用）
|   +-- vision_backend.py      >> PySide6 后端隔离层（QML 界面的逻辑层）
|   +-- VisionUI.qml           >> PySide6 + QML 浅色玻璃质感界面
|
+-- yolo/                      >> YOLO 模型与数据集
|   +-- weights/
|   |   +-- best.pt            >> 训练好的模型权重
|   |   +-- best.onnx          >> 导出的 ONNX 模型
|   +-- configs/
|   |   +-- model.yaml         >> 模型结构定义（YOLOv5s, nc=1）
|   |   +-- hyp.yaml           >> 训练超参数
|   +-- dataset/
|       +-- images/train/      >> 84 张训练图片
|       +-- images/val/        >> 21 张验证图片
|       +-- labels/train/      >> 84 个训练标注 (YOLO 格式)
|       +-- labels/val/        >> 21 个验证标注
|
+-- scripts/
|   +-- convert_rknn.py        >> ONNX > RKNN 模型转换脚本（待运行）
|   +-- export_onnx.py         >> PT > ONNX 模型导出脚本
|
+-- calibrate.py               >> 硬币标定脚本（摄像头拍摄模式）
+-- calibrate_from_image.py    >> 硬币标定脚本（基于已有图片模式）
+-- test_pipeline.py           >> 全流水线命令行测试脚本
+-- main_gui_pyqt6.py          >> GUI 主入口（PyQt6 Widgets，PC 端调试用）
+-- main_gui_pyqt5.py          >> GUI 主入口（PyQt5，Orange Pi 部署用）
+-- main_gui_qml.py            >> GUI 主入口（PySide6 + QML，PC 端）
+-- config.json                >> 配置文件（含螺丝型号数据库与标定参数）
+-- requirements.txt           >> 依赖库文件
+-- ultralytics_settings.json  >> Ultralytics 设置文件
+-- .gitignore
+-- .gitattributes
+-- README.md

+-- samples/                   >> 待测样本图片（含 coin.jpg 标定参考图）
+-- models/                    >> 保留目录，未来存放 RKNN 模型
```

## 当前进度（2026-07-05 更新）

```
   核心流水线（AI > CV > DB）  ##################..  85%
   AI 模型（已训练 + ONNX）     ####################  100%
   PyQt6 Widgets 界面升级      ##################..  90%
   PyQt5 移植适配              ####################  100%
   QML 界面功能同步             #############.......  60%
   标定                        ##########..........  45%
   数据集（已标注 105 张）       ####................  20%
   项目部署到 Orange Pi         ####################  100%
   环境搭建                     ####################  100%
   摄像头接入 + 拍照验证         ####################  100%
   RKNN 模型转换                ##..................  10%
   CV 精测参数调优（Otsu 重构）  ###############....  70%
   硬件模块（电机/传感器/红外）   ###############....  70%
   V 型槽 + 步进电机             ....................   0%
   振动落料 + 硬件分拣           ....................   0%
```

### 已完成
- [x] YOLOv5s 模型训练（84 张训练图，21 张验证图）+ ONNX 导出
- [x] ai_detector.py：支持 ONNX / RKNN / Torch 三后端
- [x] measurement.py：Otsu 二值化掩码 + 宽度轮廓分析 + 尺寸自适应膨胀
- [x] detector.py：AI > CV > DB 三阶段流水线协调 + Hough 圆检测回退
- [x] database.py：螺丝型号数据库 CRUD + 偏差匹配
- [x] hardware_manager.py：硬件管理器（连接/归零/归位/分拣/紧急停止）
- [x] opi_motor.py：双路电机驱动（步进电机正反转 + 振动电机，带 PWM）
- [x] opi_sensor.py：电阻尺位移传感器 + 微动开关（ADS1115 采样，支持模拟模式）
- [x] opi_ir.py：红外传感器模块（E18-D80NK，支持模拟模式）
- [x] 全流水线（AI > CV 精测 > DB 匹配）在 Windows 上调通
- [x] PyQt6 Widgets 界面全面升级：多螺丝列表 + 偏差颜色 + 模式切换 + 测量标签优化
- [x] PyQt5 版本移植（ui/main_window_pyqt5.py + main_gui_pyqt5.py）
- [x] QML UI 适配：AI 信息面板 + 检测来源指示 + 螺丝列表下拉框
- [x] 项目代码完整部署到 Orange Pi 5 Pro
- [x] 环境搭建：Python 3.10 + OpenCV + PyQt5 + ONNX Runtime
- [x] AI 模型在 Orange Pi 上成功加载并运行（CPUExecutionProvider）
- [x] USB 摄像头接入 Orange Pi 并成功拍照
- [x] 硬币标定（1 元硬币 25mm）=> pixel_to_mm_ratio = 9.36
- [x] scripts/convert_rknn.py：ONNX > RKNN 转换脚本
- [x] scripts/export_onnx.py：PT > ONNX 模型导出脚本
- [x] calibrate_from_image.py：基于已有图片的标定脚本
- [x] 双端开发调试工作流建立（PC 改代码 + Orange Pi 验证）
- [x] GitHub 做版本管理主通道（git push / git pull）
- [x] 背景动画层（BackgroundCanvas，QPainter 浮动光晕）
- [x] 按钮配色方案（科技绿/灰蓝/深蓝分层级）
- [x] 偏差颜色指示（绿 < 0.2mm / 黄 < 0.5mm / 红 > 0.5mm）
- [x] 智能匹配/直接选择双模式差异化布局
- [x] 项目文件清理：移除 main.py（旧 CLI）、main_gui.py（旧入口）、enviroment.txt、run.bat、run_legacy.bat

### 进行中
- [ ] CV 精测参数精细调优：边缘剪切比、平滑核尺寸、跳变阈值等参数继续优化
- [ ] 扩建数据集：补拍 200-300 张现场照片后重训模型
- [ ] QML 界面的多螺丝列表 + 偏差颜色同步适配

### 待完成
- [ ] RKNN 模型转换（onnx > rknn）并在 开发板 上部署
- [ ] 硬件模块联调（步进电机、V 型槽、振动落料）

## UI 设计演进

本项目经历了三套 GUI 方案：

| 版本 | 技术栈 | 入口 | 特点 |
|---|---|---|---|
| **V1 - QML 版（PC 端主力）** | PySide6 + QML | main_gui_qml.py | 浅色玻璃质感、Canvas 动态光晕背景、侧边导航两页布局 |
| **V2 - PyQt6 升级版（PC 端调试）** | PyQt6 Widgets | main_gui_pyqt6.py | 功能对齐 QML，新增多螺丝列表、偏差颜色指示（绿/黄/红）、模式差异化布局、QPainter 背景动画 |
| **V3 - PyQt5 移植版（开发板 部署）** | PyQt5 Widgets | main_gui_pyqt5.py | 功能与 V2 完全一致，适配 开发板 的 apt 安装环境 |

**核心差异说明**：
- 三个版本共享同一套 core/ 算法模块和 config.json 配置
- V2 和 V3 在功能上完全对称（PyQt6 与 PyQt5 的 API 差异已全部转换）
- V1（QML）仍有部分新功能待同步（多螺丝列表、偏差颜色）
- 建议 PC 调试用 V2（python main_gui_pyqt6.py），开发板 部署用 V3（python main_gui_pyqt5.py）

## 双端开发工作流

本项目的开发模式是 **PC 端写代码调算法，开发板 端部署验证**。

```
PC (Windows)                    Orange Pi 5 Pro
Python 3.10 + conda             Python 3.10 + pip
PySide6 + QML / PyQt6           PyQt5（apt 安装）
ONNX Runtime                    ONNX Runtime
OpenCV / NumPy / SciPy          同左
无硬件模块（模拟模式）           GPIO 接口 (OPi.GPIO + gpiod)

代码改动 -> git push              -> git pull
         -> scp 单文件             -> 直接覆盖
```

**GUI 选择**：
- **PC 端调试**：python main_gui_pyqt6.py（功能最完整，推荐）
- **PC 端体验**：python main_gui_qml.py（QML 动效界面）
- **开发板 部署**：python3 main_gui_pyqt5.py

**注意**：
- 核心算法（core/ 目录）纯 Python，两边代码完全一致
- 硬件模块（hardware/ 目录）自动检测运行环境，非 开发板 时回退模拟模式
- 配置文件 config.json 需要两边保持一致（特别是 pixel_to_mm_ratio）

## 标定说明

### 硬币标定（已完成）

使用 1 元硬币（25mm）完成标定：

| 项目 | 当前值 |
|---|---|
| 硬币像素直径 | 234 px（基于 samples/coin.jpg） |
| 物理直径 | 25.0 mm |
| pixel_to_mm_ratio | **9.36** |

#### 基于拍照标定

把 1 元硬币放在摄像头下方，运行：

```bash
cd ~/OPI_Feature_System_focus_vision
python3 calibrate.py
```

按 Enter 拍照，自动检测硬币、计算 ratio 并更新 config.json。

#### 基于已有图片标定

```bash
python calibrate_from_image.py samples/coin.jpg
```

## 使用说明

### PC 端调试

```bash
conda activate opi_vision

# 使用 test_pipeline.py 批量测试
python test_pipeline.py                     # 处理 samples/ 下所有图片
python test_pipeline.py samples/sample_01.jpg --save   # 单张 + 保存标注图

# 启动 PyQt6 Widgets 界面（功能最完整）
python main_gui_pyqt6.py

# 启动 QML 界面
python main_gui_qml.py
```

### Orange Pi 端部署

```bash
cd ~/OPI_Feature_System_focus_vision

# 启动 PyQt5 界面
python3 main_gui_pyqt5.py
```

## 螺丝型号数据库

当前 config.json 中预置 3 种型号：

| ID | 名称 | 直径 (mm) | 长度 (mm) | 公差 (mm) |
|---|---|---|---|---|
| M3x6 | M3x6 圆头螺丝 | 3.0 | 6.0 | 0.5 |
| M5x20 | M5x20 圆头螺丝 | 5.0 | 20.0 | 0.5 |
| M6x40 | M6x40 圆头螺丝 | 6.0 | 40.0 | 0.5 |

可通过界面或直接编辑 config.json 增删改型号。

## 模型训练情况

| 项目 | 内容 |
|---|---|
| 基础模型 | YOLOv5s（从预训练权重微调） |
| 训练数据 | 84 张训练 + 21 张验证（俯拍螺丝照片） |
| 标注格式 | YOLO 格式 .txt，单类 "screw" |
| 训练轮数 | 100 epochs，输入尺寸 640x640 |
| 输出格式 | .pt > .onnx (ONNX opset 12, 约 27.5 MB) |
| 待完成 | 训练数据仅 84 张，后续补充 |
| 待完成 | 当前仅为 ONNX 格式，部署到 Orange Pi 前需转 RKNN |

导出 ONNX 命令：
```bash
python scripts/export_onnx.py
```

## RKNN 模型转换

转换脚本已就绪：scripts/convert_rknn.py。在 x86 Linux 或 WSL2 Ubuntu 上运行：

```bash
# 安装 rknn-toolkit2
pip install rknn-toolkit2
# numpy 版本冲突时降级
pip install numpy==1.23.5

# 转换（默认 INT8 量化，推荐）
python scripts/convert_rknn.py

# 或 FP16 量化
python scripts/convert_rknn.py --fp16

# 或 FP32 不量化
python scripts/convert_rknn.py --no-quant
```

转换后将 models/best.rknn 传到 Orange Pi，修改 config.json 中 model.backend 为 "rknn"，并在 Orange Pi 上安装 rknn-toolkit-lite2 即可。

## 技术栈

| 领域 | 技术 | 状态 |
|---|---|---|
| AI 检测 | YOLOv5s + ONNX Runtime | 已接入 |
| CV 精测 | OpenCV（Otsu + 宽度轮廓分析） | 已实现 |
| 数据库 | JSON（config.json 内嵌） | 已实现 |
| GUI（PC 端 - QML） | PySide6 + QML 浅色玻璃质感 | 已适配 AI |
| GUI（PC 端 - Widgets） | PyQt6 Widgets（升级版，多螺丝列表/偏差颜色/背景动画） | 已完成 |
| GUI（Orange Pi） | PyQt5 Widgets（功能同步版） | 已适配 |
| 部署平台 | Orange Pi 5 Pro（Rockchip RK3585） | 已部署 |
| NPU 推理 | RKNN Toolkit Lite2 | 待转换与部署 |
| 硬件控制 | OPi.GPIO + gpiod | 已实现（待硬件联调） |
| 红外传感器 | E18-D80NK | 已实现（模拟模式可用） |
| 电阻尺 + 微动开关 | ADS1115 + 限位开关 | 已实现（模拟模式可用） |
| 电机驱动 | 双路 PWM（步进 + 振动） | 已实现（模拟模式可用） |
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
