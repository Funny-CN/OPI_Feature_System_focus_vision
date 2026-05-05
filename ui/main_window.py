import sys
import os
import cv2
import numpy as np
from PyQt6.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                             QLabel, QHBoxLayout, QComboBox, QFrame, QApplication)
from PyQt6.QtGui import QPixmap, QImage, QColor, QLinearGradient, QPalette, QBrush
from PyQt6.QtCore import Qt

# 引入检测器
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
        self.setWindowTitle("VisionFlow | 智能视觉监控面板")
        self.setMinimumSize(1200, 850)
        
        # 1. 应用混色玻璃底色风格
        self.apply_global_style()

        # 主容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # ================= 左侧：视觉展示中心 =================
        left_layout = QVBoxLayout()
        
        self.app_title = QLabel("视觉分析监控系统")
        self.app_title.setStyleSheet("color: #444; font-weight: bold; font-size: 18px; background: transparent;")
        left_layout.addWidget(self.app_title)

        # 图像预览区：采用半透明磨砂质感卡片
        self.image_card = QFrame()
        self.image_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.7);
                border-radius: 35px;
            }
        """)
        img_layout = QVBoxLayout(self.image_card)
        self.image_label = QLabel("正在初始化视频流...")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 核心修改：设置最小尺寸防止布局坍塌或异常拉伸
        self.image_label.setMinimumSize(640, 480) 
        self.image_label.setStyleSheet("background: transparent; border-radius: 20px;")
        img_layout.addWidget(self.image_label)
        left_layout.addWidget(self.image_card, stretch=6)

        # 底部数值显示区
        self.data_card = QFrame()
        self.data_card.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.6);
                border-radius: 35px;
            }
        """)
        data_layout = QHBoxLayout(self.data_card)
        data_layout.setContentsMargins(50, 30, 50, 30)
        
        label_v = QVBoxLayout()
        v_title = QLabel("当前测量直径")
        v_title.setStyleSheet("color: #666; font-size: 16px; font-weight: bold;")
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
                background-color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.8);
                border-radius: 45px;
            }
        """)
        right_layout = QVBoxLayout(self.control_panel)
        right_layout.setContentsMargins(25, 45, 25, 45)
        right_layout.setSpacing(25)

        # 1. 配置选择框
        self.setup_config_section(right_layout)
        
        # 2. 状态显示区
        self.setup_status_section(right_layout)

        right_layout.addStretch()

        # 3. 触控大按钮组 (解决过小、不协调问题)
        self.setup_action_section(right_layout)

        main_layout.addWidget(self.control_panel)
        self.load_frame()

    def apply_global_style(self):
        """恢复备受好评的浅蓝紫色渐变混色背景"""
        palette = self.palette()
        gradient = QLinearGradient(0, 0, 1200, 850)
        gradient.setColorAt(0.0, QColor("#E0EAFC")) # 丝滑浅蓝
        gradient.setColorAt(1.0, QColor("#CFDEF3")) # 柔和浅紫
        palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
        self.setPalette(palette)
        self.setStyleSheet("*{ font-family: 'Microsoft YaHei UI'; }")

    def setup_config_section(self, layout):
        lbl = QLabel("零件规格设定")
        lbl.setStyleSheet("color: #7F8C8D; font-size: 14px; font-weight: bold; margin-left: 10px;")
        layout.addWidget(lbl)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["M8 螺丝 (标准件)", "M10 螺丝 (标准件)", "硬币校准模式", "自定义规格"])
        self.type_combo.setMinimumHeight(65) # 适配触控高度
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(200, 200, 200, 0.3);
                border-radius: 20px;
                padding-left: 20px;
                font-size: 16px;
                color: #2D3436;
            }
            QComboBox::drop-down { border: 0px; width: 45px; }
        """)
        layout.addWidget(self.type_combo)

    def setup_status_section(self, layout):
        status_box = QFrame()
        status_box.setStyleSheet("background: rgba(255,255,255,0.2); border-radius: 25px; border: none;")
        v_lay = QVBoxLayout(status_box)
        
        self.file_info = QLabel("源文件: --")
        self.file_info.setStyleSheet("color: #636E72; font-size: 14px;")
        
        self.status_msg = QLabel("● 系统就绪")
        self.status_msg.setStyleSheet("color: #27AE60; font-weight: bold; font-size: 16px;")
        
        v_lay.addWidget(self.file_info)
        v_lay.addWidget(self.status_msg)
        layout.addWidget(status_box)

    def setup_action_section(self, layout):
        """构建大面积、高协调性的触控按钮组"""
        # 统一样式：高透磨砂感
        btn_style = """
            QPushButton {{
                min-height: 85px;
                border-radius: 30px;
                font-size: 18px;
                font-weight: bold;
                border: 1px solid rgba(255, 255, 255, 0.4);
            }}
        """
        self.btn_measure = QPushButton("一键分析测量")
        self.btn_measure.setStyleSheet(btn_style + """
            QPushButton { background-color: #0984E3; color: white; }
            QPushButton:hover { background-color: #74B9FF; }
        """)

        self.btn_next = QPushButton("切换下一样本")
        self.btn_next.setStyleSheet(btn_style + """
            QPushButton { background-color: rgba(255, 255, 255, 0.8); color: #2D3436; }
            QPushButton:hover { background-color: white; }
        """)

        self.btn_adjust = QPushButton("同步指令下发")
        self.btn_adjust.setStyleSheet(btn_style + """
            QPushButton { background-color: #D63031; color: white; }
            QPushButton:hover { background-color: #FF7675; }
        """)

        self.btn_measure.clicked.connect(self.do_measure)
        self.btn_next.clicked.connect(self.go_next)
        self.btn_adjust.clicked.connect(self.send_to_hardware)

        layout.addWidget(self.btn_measure)
        layout.addWidget(self.btn_next)
        layout.addWidget(self.btn_adjust)

    # ================= 核心业务与接口注释 =================

    def get_current_frame(self):
        """
        【摄像头接入接口】
        当前逻辑：从本地 samples 文件夹读取图片
        未来逻辑：在此处插入 self.cap.read() 获取实时画面
        """
        if not self.image_files: return None
        img_path = os.path.join(self.sample_dir, self.image_files[self.current_idx])
        return cv2.imread(img_path)

    def display_image(self, cv_img):
        """稳定的图像显示函数，防止点击按键时图像尺寸跳变"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        # 修正：使用固定的缩放策略，防止因控件微小形变导致的长宽比剧变
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.width(), 
            self.image_label.height(), 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        ))

    def load_frame(self):
        """初始化或切换样本时的载入逻辑"""
        frame = self.get_current_frame()
        if frame is not None:
            self.display_image(frame)
            self.file_info.setText(f"源文件: {self.image_files[self.current_idx]}")
            self.value_display.setText("00.00")
            self.status_msg.setText("● 待命就绪")
            self.status_msg.setStyleSheet("color: #E67E22; font-weight: bold; background: transparent;")

    def do_measure(self):
        """执行视觉分析算法"""
        frame = self.get_current_frame()
        if frame is not None:
            self.status_msg.setText("● 正在分析...")
            self.status_msg.setStyleSheet("color: #0984E3; font-weight: bold; background: transparent;")
            QApplication.processEvents()
            
            # 调用 detector.py 中的算法
            diameters, processed_img = self.detector._calculate_real_diameters(frame)
            if diameters:
                self.current_measured_value = diameters[0]
                self.value_display.setText(f"{self.current_measured_value:.2f}")
                self.display_image(processed_img)
                self.status_msg.setText("● 检测成功")
                self.status_msg.setStyleSheet("color: #27AE60; font-weight: bold; background: transparent;")
            else:
                self.status_msg.setText("● 无法识别目标")
                self.status_msg.setStyleSheet("color: #D32F2F; font-weight: bold; background: transparent;")

    def go_next(self):
        """遍历本地样本库"""
        if not self.image_files: return
        self.current_idx = (self.current_idx + 1) % len(self.image_files)
        self.load_frame()

    def send_to_hardware(self):
        """模拟指令下发"""
        if self.current_measured_value > 0:
            self.status_msg.setText("● 指令同步中...")
            QApplication.processEvents()
            # 此处应调用 hardware_stub 中的接口
            self.status_msg.setText("● 硬件同步完成")
            self.status_msg.setStyleSheet("color: #27AE60; font-weight: bold; background: transparent;")
        else:
            self.status_msg.setText("● 错误: 无分析数据")
            self.status_msg.setStyleSheet("color: #D32F2F; font-weight: bold; background: transparent;")

    def update_image_list(self):
        """扫描样本文件夹"""
        if os.path.exists(self.sample_dir):
            self.image_files = [f for f in os.listdir(self.sample_dir) if f.endswith(('.jpg', '.png'))]
            self.image_files.sort()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())