# 螺丝特征筛选视觉系统（Orange Pi 5 Pro 移植版）

基于香橙派 5 Pro 的螺丝特征筛选视觉系统，用于自动化检测和分类螺丝。
原项目从树莓派 4B 移植至此平台。

## 项目架构

```
OPI_Feature_System_focus_vision/
├── main.py                # 主入口文件
├── main_gui.py            # GUI 操作主入口（PyQt6）
├── config.json            # 配置文件，存储目标标准特征数据
├── .gitignore             # Git 忽略文件
├── README.md              # 项目说明文档
├── requirements.txt       # 依赖库文件
├── core/
│   ├── __init__.py
│   └── detector.py        # 核心视觉算法：采样、特征提取、比对逻辑
├── hardware/
│   ├── __init__.py
│   └── hardware_stub.py   # 硬件接口（Orange Pi 5 Pro GPIO 适配）
├── ui/
│   ├── __init__.py
│   └── main_window.py     # 图形操作界面
└── samples/               # 存放待测量螺丝静态图
```

## 功能模块

### 视觉检测模块 (core/detector.py)
- **目标采样阶段**：提取像素长度、直径、HSV 特征并锁定目标标准
- **实时比对阶段**：实现 $S_{current}$ 与 $S_{target}$ 的逻辑比对
- 支持特征提取：像素长度、直径、HSV 颜色特征
- 支持特征比对：基于阈值的匹配判断

### 硬件控制模块 (hardware/hardware_stub.py)
- 步进电机接口：基于 OPi.GPIO / python3-gpiod 实现
- 舵机接口：基于软件 PWM 实现角度控制
- 硬件连接管理
- Orange Pi 5 Pro 物理引脚映射已内置

### 主程序 (main.py)
- 协调视觉检测和硬件控制
- 配置加载和参数管理
- 实时检测循环

## 开发计划

1. **目标采样**：实现目标螺丝的特征提取和标准锁定
2. **实时检测**：实现实时图像的特征提取和比对
3. **硬件对接**：连接步进电机和舵机，实现自动化控制
4. **系统集成**：整合视觉检测和硬件控制，实现完整流程

## 使用说明

1. 将目标螺丝图片放入 `samples/` 文件夹
2. 修改 `config.json` 配置目标标准特征
3. 运行 `python main.py` 启动系统
4. 系统会自动进行目标采样和实时检测

## 技术栈

- Python 3.x
- OpenCV (视觉处理)
- NumPy (数值计算)
- Orange Pi 5 Pro（硬件平台，Rockchip RK3585）
- PyQt6（GUI 界面）
- OPi.GPIO / python3-gpiod（GPIO 控制）

## 依赖安装

### 使用 pip 安装依赖

```bash
pip install -r requirements.txt
```

### 开发环境建议

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux

# 安装依赖
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
- PyQt6 可用 pip 安装，若不可用可降级至 PyQt5（API 基本兼容）
- 建议使用 USB 摄像头（通用 V4L2 驱动），可最小化平台差异
- GPIO 操作需要 root 权限，运行时建议 `sudo python main.py`
