"""
VisionBackend: PySide6 后端模块，连接核心检测器与 QML UI。

┌─────────────────────────────────────────────────────┐
│  QML (VisionUI.qml) — 纯声明式 UI                   │
│         ↕ 属性绑定 / 信号槽                          │
│  VisionBackend — Qt 属性 + 信号，隔离 UI 与检测       │
│         ↕ 方法调用                                   │
│  ScrewDetector (core/detector.py) — 检测算法         │
│  AI Model (后续接入) — 分类/识别                     │
└─────────────────────────────────────────────────────┘

画面源说明（摄像头替换点见 _grab_frame 方法注释）：
    当前 — 从 samples/ 读取静态图片模拟摄像头帧
    后续 — 替换为 cv2.VideoCapture(0).read() 实现实时画面

测量扩展说明（长宽接口已预留）：
    self._length / self._width 属性已定义，QML 中值 <= 0 时显示 "--"
    后续在 detector 中实现长度/宽度测量后，只需在本类的 _process_current_frame
    中赋值即可自动更新 UI。
"""

import os
import json
import cv2
import numpy as np
from typing import Optional, List

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider


class FrameProvider(QQuickImageProvider):
    """
    将 OpenCV 帧以 QImage 形式提供给 QML Image 元素。
    QML 中引用方式: source="image://camera/live?{counter}"
    counter 递增时 QML 自动重新请求画面。
    """
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        # 初始化为纯黑画面，避免首帧前显示破图
        blank = QImage(640, 480, QImage.Format_RGB888)
        blank.fill(0xFF0F111A)
        self._frame = blank

    def requestImage(self, id: str, size, requestedSize):
        """Qt Quick 回调：返回当前帧和原始尺寸"""
        if self._frame.isNull():
            return QImage()
        return self._frame

    def update_frame(self, cv_img: np.ndarray):
        """将 OpenCV BGR 数组转为 QImage 存储"""
        if cv_img is None:
            return
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self._frame = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)


class VisionBackend(QObject):
    """
    核心状态持有者，通过 Qt 属性与信号向 QML 暴露只读数据视图。

    属性（QML 可绑定）：
        measuredDiameter, measuredLength, measuredWidth — float
        statusText, statusColor, currentFile — str
        frameCounter — int（驱动画面刷新）
        aiResultLabel — str, aiConfidence — float（预留）

    槽函数（QML 可调用）：
        startAnalysis() — 对当前帧执行完整检测
        nextSample()      — 切换下一张样本
        sendCommand()     — 下发硬件指令

    摄像头替换点：_grab_frame() 方法内部有详细 TODO 注释
    长宽扩展点：_process_current_frame() 方法内部有详细预留注释
    """

    # ── Qt 信号 ─────────────────────────────────────
    measurementUpdated = Signal()        # 测量值/AI 结果变更
    statusUpdated = Signal()             # 状态文本/颜色变更
    fileUpdated = Signal()               # 当前文件名变更
    frameCounterChanged = Signal()       # 帧计数器递增
    detectionCountChanged = Signal()     # 检测次数变更

    def __init__(self, detector, frame_provider: FrameProvider, parent=None):
        super().__init__(parent)
        self._detector = detector
        self._frame_provider = frame_provider

        # 测量状态（0.0 时 QML 显示 "--"）
        self._diameter = 0.0
        self._length = 0.0          # ★ 预留：后续 detector 实现长度后赋值
        self._width = 0.0           # ★ 预留：后续 detector 实现宽度后赋值

        # AI 检测结果（预留）
        self._ai_label = "--"
        self._ai_confidence = 0.0

        # 界面状态
        self._status_text = "系统待命"
        self._status_color = "#4FC3F7"
        self._current_file = ""
        self._frame_counter = 0
        self._detection_count = 0
        self._tolerance = self._load_tolerance()

        # 样本管理
        self._sample_dir = "samples"
        self._image_files: List[str] = []
        self._current_idx = 0

        # 定时器（模拟摄像头帧循环）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.setInterval(100)  # 100ms ≈ 10fps

    # ── 公共生命周期 ─────────────────────────────────

    def start(self):
        """程序入口：扫描样本、显示首帧、启动帧循环"""
        self._scan_samples()
        self._tolerance = self._load_tolerance()
        frame = self._grab_frame()
        if frame is not None:
            self._refresh_display(frame)
        self._timer.start()

    def stop(self):
        """停止帧循环（窗口关闭时调用）"""
        self._timer.stop()

    # ── 画面源管理 ──────────────────────────────────

    def _scan_samples(self):
        """扫描 samples/ 目录，获取图片列表并排序"""
        if not os.path.exists(self._sample_dir):
            self._image_files = []
            return
        self._image_files = [
            f for f in os.listdir(self._sample_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ]
        self._image_files.sort()

    def _grab_frame(self) -> Optional[np.ndarray]:
        """
        获取当前帧。

        当前：从 samples/ 读取静态图片。
        --------------------------------------------------
        TODO (OPi 5 Pro) — 替换为实时摄像头接入：
            1. __init__ 中添加: self._cap = cv2.VideoCapture(0)
            2. 本方法改为:
               ret, frame = self._cap.read()
               return frame if ret else None
        --------------------------------------------------
        """
        if not self._image_files:
            return None
        img_path = os.path.join(
            self._sample_dir, self._image_files[self._current_idx])
        return cv2.imread(img_path)

    def _get_current_filename(self) -> str:
        if not self._image_files:
            return "--"
        return self._image_files[self._current_idx]

    def _refresh_display(self, frame: np.ndarray):
        """更新供应器并递增计数器（驱动 QML Image 刷新）"""
        self._frame_provider.update_frame(frame)
        self._frame_counter += 1
        self.frameCounterChanged.emit()

    def _on_timer_tick(self):
        """定时器回调：只刷新画面，不触发检测"""
        frame = self._grab_frame()
        if frame is not None:
            self._refresh_display(frame)
        fname = self._get_current_filename()
        if fname != self._current_file:
            self._current_file = fname
            self.fileUpdated.emit()

    # ── 检测流水线 ──────────────────────────────────

    def _process_current_frame(self):
        """
        对当前帧执行完整检测流水线。

        ★ 后续扩展（长宽测量）：
            在 detector 中实现 measure_length() / measure_width()
            后，在此处调用并赋值给 self._length / self._width。

        ★ 后续扩展（AI 模型）：
            加入推理调用，将标签和置信度写入
            self._ai_label / self._ai_confidence。
        """
        frame = self._grab_frame()
        if frame is None:
            self._set_status("无画面数据", "#FF7675")
            return

        self._set_status("分析中...", "#FDCB6E")

        diameters, processed_img = self._detector._calculate_real_diameters(frame)

        if diameters:
            self._diameter = diameters[0]
            self._detection_count += 1
            self.detectionCountChanged.emit()
            # ★ 预留: self._length = self._detector.measure_length(frame)
            # ★ 预留: self._width  = self._detector.measure_width(frame)
        else:
            self._diameter = 0.0

        self._refresh_display(processed_img)

        if diameters:
            self._set_status("分析成功", "#00B894")
        else:
            self._set_status("分析失败", "#FF7675")

        self.measurementUpdated.emit()

    def _load_tolerance(self) -> float:
        """从 config.json 读取测量公差"""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        try:
            with open(config_path, "r") as f:
                cfg = json.load(f)
            return cfg.get("target_standard", {}).get("tolerance", {}).get("diameter_mm", 0.5)
        except Exception as e:
            print(f"[BACKEND] 读取 config.json 失败: {e}")
            return 0.5

    def _set_status(self, text: str, color: str):
        self._status_text = text
        self._status_color = color
        self.statusUpdated.emit()

    # ── 槽函数（QML 调用） ─────────────────────────

    @Slot()
    def startAnalysis(self):
        self._process_current_frame()

    @Slot()
    def nextSample(self):
        if not self._image_files:
            return
        self._current_idx = (self._current_idx + 1) % len(self._image_files)
        # 重置测量值
        self._diameter = 0.0
        self._length = 0.0
        self._width = 0.0
        self.measurementUpdated.emit()
        self._on_timer_tick()
        self._set_status("系统就绪", "#4FC3F7")

    @Slot()
    def sendCommand(self):
        if self._diameter > 0:
            print(f"[HARDWARE] 指令下发: {self._diameter:.2f}mm")
            self._set_status("指令已传达", "#00B894")
        else:
            self._set_status("无有效数据", "#FF7675")

    # ── Qt 属性（QML 绑定） ───────────────────────

    @Property(float, notify=measurementUpdated)
    def measuredDiameter(self) -> float:
        return self._diameter

    @Property(float, notify=measurementUpdated)
    def measuredLength(self) -> float:
        """★ 预留：长宽测量接入后自动生效"""
        return self._length

    @Property(float, notify=measurementUpdated)
    def measuredWidth(self) -> float:
        """★ 预留：长宽测量接入后自动生效"""
        return self._width

    @Property(int, notify=detectionCountChanged)
    def detectionCount(self) -> int:
        return self._detection_count

    @Property(float, notify=measurementUpdated)
    def tolerance(self) -> float:
        return self._tolerance

    @Property(str, notify=statusUpdated)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, notify=statusUpdated)
    def statusColor(self) -> str:
        return self._status_color

    @Property(str, notify=fileUpdated)
    def currentFile(self) -> str:
        return self._current_file

    @Property(int, notify=frameCounterChanged)
    def frameCounter(self) -> int:
        return self._frame_counter

    @Property(str, notify=measurementUpdated)
    def aiResultLabel(self) -> str:
        """★ 预留：AI 模型接入后自动生效"""
        return self._ai_label

    @Property(float, notify=measurementUpdated)
    def aiConfidence(self) -> float:
        """★ 预留：AI 模型接入后自动生效"""
        return self._ai_confidence
