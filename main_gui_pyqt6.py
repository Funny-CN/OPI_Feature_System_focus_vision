"""
主 GUI 入口 — PyQt6 旧版（回滚用）
保留此文件以便随时切换回原版 UI。

启动方式：
    python main_gui_pyqt6.py
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
