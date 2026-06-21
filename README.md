# 螺丝特征筛选视觉系统（Orange Pi 5 Pro 移植版）

基于香橙派 5 Pro 的螺丝特征筛选视觉系统，用于自动化检测和分类螺丝。
原项目从树莓派 4B 移植至此平台。

## 项目架构

```
OPI_Feature_System_focus_vision/
├── main.py                  # CLI 主入口（无 GUI，命令行模式）
├── main_gui.py              # GUI 主入口（新版默认：PySide6 + QML）
├── main_gui_qml.py          # 新版 QML 入口备份副本
├── main_gui_pyqt6.py        # 旧版 PyQt6 入口（回滚用）
├── run.bat                  # 双击启动新版 QML UI
├── run_legacy.bat           # 双击启动旧版 PyQt6 UI
├── config.json              # 配置文件，存储目标标准特征数据
├── enviroment.txt           # Conda 环境说明
├── .gitignore
├── README.md
├── requirements.txt         # 依赖库文件（含 PySide6 + PyQt6）
├── core/
│   ├── __init__.py
│   └── detector.py          # 核心视觉算法：采样、特征提取、比对逻辑
├── hardware/
│   ├── __init__.py
│   └── hardware_stub.py     # 硬件接口（Orange Pi 5 Pro GPIO 适配）
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # 旧版 PyQt6 Widgets 界面（保留）
│   ├── vision_backend.py    # ★ 新版：PySide6 后端隔离层
│   └── VisionUI.qml         # ★ 新版：QML 深色玻璃质感界面
└── samples/                 # 存放待测量螺丝静态图
```

## 功能模块

### 视觉检测模块 (core/detector.py)
- **目标采样阶段**：提取像素长度、直径、HSV 特征并锁定目标标准
- **实时比对阶段**：实现当前特征与目标特征的逻辑比对
- 支持特征提取：像素长度、直径、HSV 颜色特征
- 支持特征比对：基于阈值的匹配判断
- 后续可扩展：长宽测量接口、AI 模型检测

### GUI 模块 (新版 — PySide6 + QML)
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

## GUI 版本说明

本项目维护两个 GUI 版本，可共存切换：

| 版本 | 框架 | 入口文件 | 启动方式 |
|---|---|---|---|
| **新版（默认）** | PySide6 + QML | `main_gui.py` | `python main_gui.py` 或双击 `run.bat` |
| 旧版（回滚） | PyQt6 + Widgets | `main_gui_pyqt6.py` | `python main_gui_pyqt6.py` 或双击 `run_legacy.bat` |

三个入口文件（`main_gui.py` / `main_gui_qml.py` / `main_gui_pyqt6.py`）均接入了 `core/detector.py` 的核心检测逻辑。

## 开发计划

1. **目标采样**：实现目标螺丝的特征提取和标准锁定
2. **实时检测**：实现实时图像的特征提取和比对
3. **硬件对接**：连接步进电机和舵机，实现自动化控制
4. **系统集成**：整合视觉检测和硬件控制，实现完整流程
5. **AI 检测**（规划中）：接入 AI 视觉模型进行螺丝分类和缺陷检测

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
- OpenCV (视觉处理)
- NumPy (数值计算)
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

### Orange Pi 5 Pro 特定依赖

对于香橙派 5 Pro 硬件控制，需要额外安装：

```bash
# 安装 OPi.GPIO（RPi.GPIO 的香橙派移植版）
sudo apt-get update
sudo apt-get install -y python3-dev python3-pip
pip install OPi.GPIO

# 或者安装 python3-gpiod（内核原生 GPIO 接口）
sudo apt-get install -y python3-libgpiod gpiod

# 运行时建议以 root 或 gpio 用户组权限运行
```

## 关于迁移（树莓派 4B → Orange Pi 5 Pro）

本项目原基于树莓派 4B 开发，现已移植至香橙派 5 Pro。主要变更：

| 方面 | 树莓派 4B | Orange Pi 5 Pro |
|---|---|---|
| SoC | Broadcom BCM2711 | Rockchip RK3585 |
| GPIO 库 | RPi.GPIO / pigpio | OPi.GPIO / python3-gpiod |
| 引脚编号 | BCM 方案 | BOARD 物理编号 |
| 舵机控制 | pigpio 硬件 PWM | 软件 PWM |
| 摄像头 | libcamera / picamera2 | V4L2 / Rockchip MPP |

### 移植注意事项

- GPIO 引脚映射完全不同，`hardware/hardware_stub.py` 已使用 BOARD 物理编号
- 新版 GUI 基于 PySide6 + QML（Qt6），利用 Mali G610 GPU 硬件加速
- 旧版 PyQt6 保留作为回滚方案，两者可共存
- 建议使用 USB 摄像头（通用 V4L2 驱动），可最小化平台差异
- GPIO 操作需要 root 权限，运行时建议 `sudo python main.py`
