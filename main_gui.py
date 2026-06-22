'''
主 GUI 入口 — PySide6 + QML 版

启动方式：
    python main_gui.py (需在 Conda 环境 opi_vision 下运行)

启动流程：
    1. 创建 QGuiApplication
    2. 创建 FrameProvider（画面供应器）
    3. 创建 VisionBackend（后端状态管理）
    4. 建立 QML 引擎，注册 provider 和 context property
    5. 加载 VisionUI.qml
    6. backend.start() 启动帧循环
    7. 进入事件循环
'''

import sys
import os

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QUrl

# 确保项目根目录在 sys.path 中
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from core.detector import ScrewDetector
from ui.vision_backend import VisionBackend, FrameProvider
from PySide6.QtQuickControls2 import QQuickStyle

# Use Basic style for ComboBox customization
QQuickStyle.setStyle("Basic")



def main():
    app = QGuiApplication(sys.argv)
    app.setApplicationName("视觉智能筛选系统")
    app.setOrganizationName("OPI")

    # ── 创建画面供应器 ──────────────────────────────
    frame_provider = FrameProvider()

    # ── 创建检测器和后端 ─────────────────────────────
    detector = ScrewDetector()
    backend = VisionBackend(detector, frame_provider)

    # ── 初始化 QML 引擎 ─────────────────────────────
    engine = QQmlApplicationEngine()

    # 注册图像供应器，QML 中通过 "image://camera/live" 访问
    engine.addImageProvider("camera", frame_provider)

    # 将后端暴露给 QML，QML 中通过 backend.xxx 引用
    engine.rootContext().setContextProperty("backend", backend)

    # 加载主界面
    qml_path = os.path.join(_project_root, "ui", "VisionUI.qml")
    engine.load(QUrl.fromLocalFile(qml_path))

    if not engine.rootObjects():
        print("[FATAL] QML 加载失败，请检查 ui/VisionUI.qml 是否存在")
        sys.exit(-1)

    # ── 启动后端帧循环 ──────────────────────────────
    backend.start()

    # ── 进入 Qt 事件循环 ────────────────────────────
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
