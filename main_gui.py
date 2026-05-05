import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    # 创建 PyQt 应用程序大脑
    app = QApplication(sys.argv)

    # 实例化刚才写好的窗口本体
    window = MainWindow()

    # 展示窗口
    window.show()

    # 进入程序主循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()