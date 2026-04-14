# 螺丝特征筛选视觉系统

基于树莓派的螺丝特征筛选视觉系统，用于自动化检测和分类螺丝。

## 项目架构

```
vision_test_project/
├── main.py                 # 主入口文件
├── config.json            # 配置文件，存储目标标准特征数据
├── .gitignore             # Git 忽略文件
├── README.md              # 项目说明文档
├── core/
│   ├── __init__.py
│   └── detector.py        # 核心视觉算法：包含采样、特征提取、比对逻辑
├── hardware/
│   ├── __init__.py
│   └── hardware_stub.py   # 硬件接口存根（步进电机和舵机）
├── samples/               # 存放目标螺丝静态图
└── test_mix/              # 存放混料静态图
```

## 功能模块

### 视觉检测模块 (core/detector.py)
- **目标采样阶段**：提取像素长度、直径、HSV特征并锁定目标标准
- **实时比对阶段**：实现 $S_{current}$ 与 $S_{target}$ 的逻辑比对
- 支持特征提取：像素长度、直径、HSV颜色特征
- 支持特征比对：基于阈值的匹配判断

### 硬件控制模块 (hardware/hardware_stub.py)
- 步进电机接口：移动控制
- 舵机接口：角度控制
- 硬件连接管理

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
4. 系统将自动进行目标采样和实时检测

## 技术栈

- Python 3.x
- OpenCV (视觉处理)
- NumPy (数值计算)
- 树莓派 (硬件平台)
- JSON (配置管理)

## 依赖安装

### 使用pip安装依赖

```bash
pip install -r requirements.txt
```

### 开发环境建议

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate    # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 树莓派特定依赖

对于树莓派硬件控制，需要额外安装：

```bash
# 安装树莓派GPIO库
sudo apt-get update
sudo apt-get install python3-rpi.gpio
sudo apt-get install python3-pigpio
sudo systemctl start pigpiod
```

## 依赖说明

- **opencv-python**: 核心视觉处理库
- **numpy**: 数值计算和数组操作
- **scipy**: 科学计算函数
- **matplotlib**: 图像可视化和调试
- **pillow**: 图像处理和格式转换
- **RPi.GPIO**: 树莓派GPIO控制
- **pigpio**: 高级GPIO控制
- **pytest**: 单元测试框架
- **black**: 代码格式化
- **flake8**: 代码质量检查
- **sphinx**: 文档生成
- **numba**: 性能优化

## 注意事项

- 本项目目前为框架结构，具体算法实现需要根据实际需求完善
- 硬件接口为存根实现，实际使用时需要对接真实硬件
- 特征提取算法需要根据螺丝类型和光照条件进行调整