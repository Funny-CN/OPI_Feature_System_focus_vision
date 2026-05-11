import sys
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                             QLabel, QHBoxLayout, QComboBox, QFrame, QApplication)
from PyQt6.QtGui import QPixmap, QImage, QColor, QLinearGradient, QPalette, QBrush
from PyQt6.QtCore import Qt

# 引入检测器（保持原有架构 core.detector）
from core.detector import ScrewDetector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.detector = ScrewDetector()
        
        # 数据初始化
        self.sample_dir = 'samples/'
        self.image_files = []
        self.current_idx = 0
        self.current_measured_value = 0.0
        self.update_image_list()

        # --- 窗口全局配置 ---
        self.setWindowTitle("VisionFlow | 视觉智能筛选系统")
        self.setMinimumSize(1200, 850)
        
        # 应用浅色玻璃美学背景
        self.apply_glass_style()

        # 主容器布局：采用水平布局，左侧为显示与数据区，右侧为控制面板
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # ================= 左侧：视觉展示中心 =================
        left_layout = QVBoxLayout()
        
        self.app_title = QLabel("实时监控画面")
        self.app_title.setStyleSheet("color: #576574; font-weight: bold; font-size: 18px; background: transparent;")
        left_layout.addWidget(self.app_title)

        # 图像预览区卡片：通过 rgba 控制透明度实现毛玻璃质感
        self.image_card = QFrame()
        self.image_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.6);
                border-radius: 20px;
            }
        """)
        img_layout = QVBoxLayout(self.image_card)
        self.image_label = QLabel("正在初始化视频流...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(640, 480) # 锁定最小尺寸防止 UI 抖动
        self.image_label.setStyleSheet("background: transparent;")
        img_layout.addWidget(self.image_label)
        left_layout.addWidget(self.image_card, stretch=6)

        # 底部数据面板：大字体展示测量数值
        self.data_card = QFrame()
        self.data_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.5);
                border-radius: 20px;
            }
        """)
        data_layout = QHBoxLayout(self.data_card)
        data_layout.setContentsMargins(50, 20, 50, 20)
        
        label_v = QVBoxLayout()
        v_title = QLabel("当前测量结果")
        v_title.setStyleSheet("color: #8395a7; font-size: 16px; font-weight: bold;")
        label_v.addWidget(v_title)
        
        self.value_display = QLabel("00.00")
        self.value_display.setStyleSheet("font-size: 95px; color: #2D3436; font-weight: 200;")
        
        self.unit_label = QLabel("mm")
        self.unit_label.setStyleSheet("font-size: 28px; color: #636E72; margin-bottom: 22px;")
        
        data_layout.addLayout(label_v)
        data_layout.addStretch()
        data_layout.addWidget(self.value_display)
        data_layout.addWidget(self.unit_label, alignment=Qt.AlignmentFlag.AlignBottom)
        
        left_layout.addWidget(self.data_card, stretch=3)
        main_layout.addLayout(left_layout, stretch=7)

        # ================= 右侧：操作控制中心 =================
        self.control_panel = QFrame()
        self.control_panel.setFixedWidth(380)
        self.control_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 30px;
            }
        """)
        right_layout = QVBoxLayout(self.control_panel)
        right_layout.setContentsMargins(25, 45, 25, 45)
        right_layout.setSpacing(25)

        # 1. 模式选择下拉框
        cfg_lbl = QLabel("作业模式选择")
        cfg_lbl.setStyleSheet("color: #576574; font-size: 14px; font-weight: bold; margin-left: 5px;")
        right_layout.addWidget(cfg_lbl)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["螺丝", "螺母垫片", "其他"])
        self.type_combo.setMinimumHeight(60)
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #F8F9FA;
                border: 1px solid #CED4DA;
                border-radius: 8px;
                padding-left: 15px;
                font-size: 16px;
                color: #2D3436;
            }
            QComboBox::drop-down { border: none; background: transparent; width: 40px; }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 8px solid #0984E3;
                margin-right: 15px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: #E1F5FE;
                selection-color: #01579B;
                border: 1px solid #CED4DA;
                outline: none;
            }
        """)
        right_layout.addWidget(self.type_combo)
        
        # 状态显示盒
        status_box = QFrame()
        status_box.setStyleSheet("background: rgba(255,255,255,0.4); border-radius: 15px;")
        v_lay = QVBoxLayout(status_box)
        self.file_info = QLabel("源文件: --")
        self.file_info.setStyleSheet("color: #636E72; font-size: 13px;")
        self.status_msg = QLabel("● 系统待命")
        self.status_msg.setStyleSheet("color: #2e86de; font-weight: bold; font-size: 16px;")
        v_lay.addWidget(self.file_info)
        v_lay.addWidget(self.status_msg)
        right_layout.addWidget(status_box)

        right_layout.addStretch()

        # 2. 按钮组样式定义
        btn_base_style = """
            QPushButton {
                min-height: 85px;
                border-radius: 20px;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.8);
            }
        """
        
        self.btn_measure = QPushButton("开始分析")
        self.btn_measure.setStyleSheet(btn_base_style + """
            QPushButton { background-color: rgba(116, 185, 255, 0.8); color: #0652DD; }
            QPushButton:hover { background-color: rgba(116, 185, 255, 1.0); }
        """)

        self.btn_next = QPushButton("下一样本")
        self.btn_next.setStyleSheet(btn_base_style + """
            QPushButton { background-color: rgba(223, 230, 233, 0.7); color: #2D3436; }
            QPushButton:hover { background-color: rgba(223, 230, 233, 1.0); }
        """)

        self.btn_adjust = QPushButton("下发指令")
        self.btn_adjust.setStyleSheet(btn_base_style + """
            QPushButton { background-color: rgba(255, 118, 117, 0.4); color: #D32F2F; }
            QPushButton:hover { background-color: rgba(255, 118, 117, 0.6); }
        """)

        # 信号与槽连接
        self.btn_measure.clicked.connect(self.do_measure)
        self.btn_next.clicked.connect(self.go_next)
        self.btn_adjust.clicked.connect(self.send_to_hardware)

        right_layout.addWidget(self.btn_measure)
        right_layout.addWidget(self.btn_next)
        right_layout.addWidget(self.btn_adjust)

        main_layout.addWidget(self.control_panel)
        self.load_frame()

    def apply_glass_style(self):
        """
        【UI 美化函数】
        使用 QLinearGradient 创建从浅蓝灰到柔和蓝的渐变背景。
        通过 QPalette 将渐变刷入窗口背景，实现非纯色的视觉深度感。
        """
        palette = self.palette()
        gradient = QLinearGradient(0, 0, 1200, 850)
        gradient.setColorAt(0.0, QColor("#F0F3F7")) 
        gradient.setColorAt(1.0, QColor("#D9E4F5")) 
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)
        self.setStyleSheet("*{ font-family: 'Microsoft YaHei UI'; }")

    def get_current_frame(self):
        """
        【核心摄像头/图像接入预留接口】
        当前阶段：通过读取本地 samples/ 目录下的静态图片模拟视频帧。
        
        后续接入实时摄像头（Camera）的修改建议：
        1. 在 __init__ 中初始化：self.cap = cv2.VideoCapture(0)
        2. 设置分辨率：self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280) 等
        3. 修改本函数逻辑：
           ret, frame = self.cap.read()
           if ret: return frame
           else: return None
        4. 为了实现“实时”显示，建议后续引入 QTimer 定时器，每隔 30ms 调用一次本函数。
        """
        if not self.image_files: return None
        img_path = os.path.join(self.sample_dir, self.image_files[self.current_idx])
        return cv2.imread(img_path)

    def display_image(self, cv_img):
        """
        【图像转换与渲染函数】
        将 OpenCV 的 BGR 格式图像转换为 Qt 可显示的 RGB 格式 QImage。
        参数：
            cv_img: cv2.imread 或摄像头返回的 numpy 数组。
        优化点：使用 KeepAspectRatio 实现等比缩放，避免图像变形；使用 SmoothTransformation 减少锯齿。
        """
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(), 
            self.image_label.height(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def load_frame(self):
        """
        【初始化/切换加载函数】
        当点击“下一样本”或程序启动时触发，负责重置测量数值并显示当前底图。
        """
        frame = self.get_current_frame()
        if frame is not None:
            self.display_image(frame)
            self.file_info.setText(f"当前源: {self.image_files[self.current_idx]}")
            self.value_display.setText("00.00")
            self.status_msg.setText("● 系统就绪")
            self.status_msg.setStyleSheet("color: #2e86de; font-weight: bold;")

    def do_measure(self):
        """
        【核心业务处理函数 - 分析测量】
        1. 获取当前待处理帧。
        2. 调用 core.detector 中的算法进行特征提取。
        3. 更新界面上的直径数值，并显示带有检测框（绿圈）的渲染后图像。
        注：QApplication.processEvents() 用于在计算期间刷新 UI 状态，防止界面卡死。
        """
        frame = self.get_current_frame()
        if frame is not None:
            self.status_msg.setText("● 分析中...")
            QApplication.processEvents() # 强制 UI 响应，显示“分析中”状态
            diameters, processed_img = self.detector._calculate_real_diameters(frame)
            if diameters:
                self.current_measured_value = diameters[0]
                self.value_display.setText(f"{self.current_measured_value:.2f}")
                self.display_image(processed_img) # 显示带标记的结果图
                self.status_msg.setText("● 分析成功")
                self.status_msg.setStyleSheet("color: #10ac84; font-weight: bold;")
            else:
                self.status_msg.setText("● 分析失败")
                self.status_msg.setStyleSheet("color: #ee5253; font-weight: bold;")

    def go_next(self):
        """【样本切换】循环遍历 samples 文件夹内的所有图片。"""
        if not self.image_files: return
        self.current_idx = (self.current_idx + 1) % len(self.image_files)
        self.load_frame()

    def send_to_hardware(self):
        """
        【硬件通信同步接口】
        当视觉分析完成后，点击此按钮将测量出的直径数据下发。
        后续扩展：
        1. 此处应引入 hardware/hardware_stub.py 中的控制类。
        2. 调用如 self.hardware.move_to(self.current_measured_value) 等方法。
        """
        if self.current_measured_value > 0:
            print(f"HW_LOG >> 指令下发: {self.current_measured_value:.2f}mm")
            self.status_msg.setText("● 指令已传达")
            self.status_msg.setStyleSheet("color: #10ac84; font-weight: bold;")
        else:
            self.status_msg.setText("● 无有效数据")
            self.status_msg.setStyleSheet("color: #ee5253; font-weight: bold;")

    def update_image_list(self):
        """【文件系统检索】扫描 samples 目录，支持常用图像格式。"""
        if os.path.exists(self.sample_dir):
            self.image_files = [f for f in os.listdir(self.sample_dir) if f.endswith(('.jpg', '.png'))]
            self.image_files.sort()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())