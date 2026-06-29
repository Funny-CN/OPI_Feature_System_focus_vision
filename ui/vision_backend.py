"""
VisionBackend: PySide6 ????????????? QML UI?

???
  QML (VisionUI.qml)  <->  VisionBackend  <->  ScrewDetector
                                        <->  ScrewDatabase
                                        <->  PrecisionMeasurer
"""

import os
import json
import cv2
import numpy as np
from typing import Optional, List
from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider
from core.database import ScrewDatabase, ScrewSpec


class FrameProvider(QQuickImageProvider):
    """? OpenCV ?? QImage ????? QML?"""
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        blank = QImage(640, 480, QImage.Format_RGB888)
        blank.fill(0xFF0F111A)
        self._frame = blank

    def requestImage(self, id: str, size, requestedSize):
        if self._frame.isNull():
            return QImage()
        return self._frame

    def update_frame(self, cv_img: np.ndarray):
        if cv_img is None:
            return
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        self._frame = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)


class VisionBackend(QObject):
    """?????????? Qt ?????? QML ???????"""

    # Qt ??
    measurementUpdated = Signal()
    statusUpdated = Signal()
    fileUpdated = Signal()
    frameCounterChanged = Signal()
    detectionCountChanged = Signal()
    matchResultChanged = Signal()
    screwListChanged = Signal()
    modeChanged = Signal()

    def __init__(self, detector, frame_provider: FrameProvider, parent=None):
        super().__init__(parent)
        self._detector = detector
        self._frame_provider = frame_provider
        self._db = ScrewDatabase()

        # ????
        self._diameter = 0.0
        self._length = 0.0
        self._width = 0.0

        # ????
        self._match_name = "--"
        self._match_deviation = 0.0
        self._match_count = 0

        # ????
        self._status_text = "系统待命"
        self._status_color = "#4FC3F7"
        self._current_file = ""
        self._frame_counter = 0
        self._detection_count = 0
        self._mode = 0  # 0: 智能匹配, 1: 直接选择

        # ????
        self._sample_dir = "samples"
        self._image_files: List[str] = []
        self._current_idx = 0

        # ???
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.setInterval(100)

    # -- 公共生命周期 --

    def start(self):
        self._scan_samples()
        frame = self._grab_frame()
        if frame is not None:
            self._refresh_display(frame)
        self._timer.start()

    def stop(self):
        self._timer.stop()

    # -- 画面源管理 --

    def _scan_samples(self):
        if not os.path.exists(self._sample_dir):
            self._image_files = []
            return
        self._image_files = [
            f for f in os.listdir(self._sample_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        self._image_files.sort()

    def _grab_frame(self) -> Optional[np.ndarray]:
        if not self._image_files:
            return None
        img_path = os.path.join(self._sample_dir, self._image_files[self._current_idx])
        return cv2.imread(img_path)

    def _get_current_filename(self) -> str:
        if not self._image_files:
            return "--"
        return self._image_files[self._current_idx]

    def _refresh_display(self, frame: np.ndarray):
        self._frame_provider.update_frame(frame)
        self._frame_counter += 1
        self.frameCounterChanged.emit()

    def _on_timer_tick(self):
        frame = self._grab_frame()
        if frame is not None:
            self._refresh_display(frame)
        fname = self._get_current_filename()
        if fname != self._current_file:
            self._current_file = fname
            self.fileUpdated.emit()

    # -- 检测流水线 --

    def _process_current_frame(self):
        frame = self._grab_frame()
        if frame is None:
            self._set_status("无画面数据", "#FF7675")
            return

        self._set_status("分析中...", "#FDCB6E")

        # 使用新的协调器进行完整分析
        analysis = self._detector.analyze(frame)
        processed = analysis.annotated_frame

        # 更新测量值
        if analysis.screws:
            sr = analysis.screws[0]
            self._diameter = sr.measurement.diameter
            self._length = sr.measurement.length
            self._width = sr.measurement.width
            self._detection_count += 1
            self.detectionCountChanged.emit()

            # 更新匹配结果
            if sr.match.matched:
                self._match_name = sr.match.screw.name
                self._match_deviation = sr.match.deviation
                self._match_count = len([s for s in analysis.screws if s.match.matched])
            else:
                self._match_name = "未匹配"
                self._match_deviation = 0.0
                self._match_count = 0
            self.matchResultChanged.emit()
        else:
            self._diameter = 0.0
            self._length = 0.0
            self._width = 0.0
            self._match_name = "--"
            self._match_deviation = 0.0
            self.matchResultChanged.emit()

        self._refresh_display(processed)
        status = "分析成功" if analysis.screws else "未检测到螃丝"
        color = "#00B894" if analysis.screws else "#FF7675"
        self._set_status(status, color)
        self.measurementUpdated.emit()

    def _set_status(self, text: str, color: str):
        self._status_text = text
        self._status_color = color
        self.statusUpdated.emit()

    # -- 槽函数（QML 调用） --

    @Slot()
    def startAnalysis(self):
        self._process_current_frame()

    @Slot()
    def nextSample(self):
        if not self._image_files:
            return
        self._current_idx = (self._current_idx + 1) % len(self._image_files)
        self._diameter = 0.0
        self._length = 0.0
        self._width = 0.0
        self._match_name = "--"
        self._match_deviation = 0.0
        self.measurementUpdated.emit()
        self.matchResultChanged.emit()
        self._on_timer_tick()
        self._set_status("系统就绪", "#4FC3F7")

    @Slot()
    def sendCommand(self):
        if self._diameter > 0:
            print("[HARDWARE] 指令下发: {:.2f}mm".format(self._diameter))
            self._set_status("指令已传达", "#00B894")
        else:
            self._set_status("无有效数据", "#FF7675")

    @Slot(str, result=list)
    def getScrewList(self, filter=""):
        return self._db.list_all()

    @Slot(result=str)
    def getScrewJson(self):
        """返回所有螃丝的 JSON 字符串，供 QML 显示"""
        screws = self._db.list_all()
        data = [{"id": s.id, "name": s.name, "diameter": s.diameter,
                 "length": s.length} for s in screws]
        return json.dumps(data, ensure_ascii=False)

    # -- Qt 属性 --

    @Property(float, notify=measurementUpdated)
    def measuredDiameter(self) -> float:
        return self._diameter

    @Property(float, notify=measurementUpdated)
    def measuredLength(self) -> float:
        return self._length

    @Property(float, notify=measurementUpdated)
    def measuredWidth(self) -> float:
        return self._width

    @Property(int, notify=detectionCountChanged)
    def detectionCount(self) -> int:
        return self._detection_count

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

    # -- 新增：匹配结果属性 --

    @Property(str, notify=matchResultChanged)
    def matchName(self) -> str:
        return self._match_name

    @Property(float, notify=matchResultChanged)
    def matchDeviation(self) -> float:
        return self._match_deviation

    @Property(int, notify=matchResultChanged)
    def matchCount(self) -> int:
        return self._match_count

    @Property(int, notify=modeChanged)
    def mode(self) -> int:
        return self._mode

    @mode.setter
    def mode(self, val: int):
        if self._mode != val:
            self._mode = val
            self.modeChanged.emit()
