import sys
import os
import cv2
import numpy as np
import math
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QWidget,
                             QLabel, QHBoxLayout, QComboBox, QFrame, QApplication,
                             QSizePolicy, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage, QColor, QLinearGradient, QPalette, QBrush, QPainter, QRadialGradient
from PyQt5.QtCore import Qt, QTimer

from core.detector import ScrewDetector
from core.database import ScrewDatabase


# ── 颜色常量 ────────────────────────────────────────────
C_BG_START   = "#FCF7F0"
C_BG_END     = "#F0E9E0"
C_CYAN       = "#2563EB"
C_GREEN      = "#059669"
C_GOLD       = "#D97706"
C_RED        = "#DC2626"
C_TEXT_MAIN  = "#1E3A5F"
C_TEXT_SEC   = "#5A7184"
C_TEXT_DIM   = "#94A3B8"
C_CARD_BG    = "rgba(245, 252, 248, 0.65)"
C_BORDER     = "rgba(100, 116, 139, 0.20)"


def _ss(color, size=13, weight="normal"):
    return f"color: {color}; font-size: {size}px; font-weight: {weight}; background: transparent; border: none;"


def _card(radius=12):
    return (f"background-color: {C_CARD_BG}; border: 1px solid {C_BORDER};"
            f" border-radius: {radius}px;")


def _deviation_color(dev: float) -> str:
    if dev < 0.2:
        return C_GREEN
    elif dev < 0.5:
        return C_GOLD
    return C_RED


class BackgroundCanvas(QWidget):
    """Animated background with floating radial gradients"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._phase = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self._timer = QTimer(self)
        self._timer.timeout.connect(lambda: self.update())
        self._timer.setInterval(50)
        self._timer.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        self._phase += 0.045
        if w < 1 or h < 1:
            return

        # Blue gradient
        cx1 = w * (0.05 + 0.85 * (0.5 + 0.5 * math.sin(self._phase)))
        cy1 = h * (0.10 + 0.75 * (0.5 + 0.5 * math.cos(self._phase * 0.8)))
        g1 = QRadialGradient(cx1, cy1, w * 0.38)
        g1.setColorAt(0.0, QColor(37, 99, 235, 115))
        g1.setColorAt(0.4, QColor(37, 99, 235, 50))
        g1.setColorAt(0.7, QColor(37, 99, 235, 12))
        g1.setColorAt(1.0, QColor(37, 99, 235, 0))
        painter.fillRect(self.rect(), QBrush(g1))

        # Gold gradient
        cx2 = w * (0.10 + 0.75 * (0.5 + 0.5 * math.sin(self._phase * 0.7 + 2.0)))
        cy2 = h * (0.05 + 0.85 * (0.5 + 0.5 * math.cos(self._phase * 0.9 + 1.0)))
        g2 = QRadialGradient(cx2, cy2, w * 0.38)
        g2.setColorAt(0.0, QColor(245, 158, 11, 105))
        g2.setColorAt(0.4, QColor(245, 158, 11, 45))
        g2.setColorAt(0.7, QColor(245, 158, 11, 12))
        g2.setColorAt(1.0, QColor(245, 158, 11, 0))
        painter.fillRect(self.rect(), QBrush(g2))

        # Teal gradient
        cx3 = w * (0.05 + 0.85 * (0.5 + 0.5 * math.sin(self._phase * 0.6 + 4.0)))
        cy3 = h * (0.10 + 0.80 * (0.5 + 0.5 * math.cos(self._phase * 1.1 + 2.0)))
        g3 = QRadialGradient(cx3, cy3, w * 0.32)
        g3.setColorAt(0.0, QColor(8, 145, 178, 105))
        g3.setColorAt(0.4, QColor(8, 145, 178, 45))
        g3.setColorAt(0.7, QColor(8, 145, 178, 12))
        g3.setColorAt(1.0, QColor(8, 145, 178, 0))
        painter.fillRect(self.rect(), QBrush(g3))

        # Fixed warm light (bottom-left)
        cx4 = w * 0.12
        cy4 = h * 0.82
        g4 = QRadialGradient(cx4, cy4, w * 0.22)
        g4.setColorAt(0.0, QColor(59, 130, 246, 65))
        g4.setColorAt(0.5, QColor(59, 130, 246, 30))
        g4.setColorAt(1.0, QColor(59, 130, 246, 0))
        painter.fillRect(self.rect(), QBrush(g4))


class MainWindow(QMainWindow):
    """PyQt6 界面 — 升级版，功能对齐 QML"""

    def __init__(self):
        super().__init__()
        self.detector = ScrewDetector()
        self.db = ScrewDatabase()

        self.sample_dir = "samples/"
        self.image_files = []
        self.current_idx = 0
        self._frame_counter = 0
        self._detection_count = 0
        self._work_mode = 1
        self._selected_screw_id = ""

        # 当前螺丝（单颗，用于直接选择模式 / 选中显示）
        self._diameter = 0.0
        self._length = 0.0
        self._width = 0.0
        self._match_name = "--"
        self._match_deviation = 0.0
        self._match_count = 0

        # 多螺丝检测结果
        self._analysis_screws = []   # list of dict
        self._selected_screw_idx = 0

        self._ai_loaded = False
        self._ai_backend = "--"
        self._ai_confidence = 0.0
        self._ai_screw_count = 0
        self._detection_source = "Hough"

        self._load_ai_info()
        self._scan_samples()

        self.setWindowTitle("VisionFlow | 视觉智能筛选系统")
        self.setMinimumSize(1200, 850)
        self._apply_glass()
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.setInterval(100)
        self._timer.start()

        self._load_frame()

    # ───────────────────── 样式 ─────────────────────────

    def _apply_glass(self):
        p = self.palette()
        g = QLinearGradient(0, 0, 1280, 800)
        g.setColorAt(0.0, QColor(C_BG_START))
        g.setColorAt(1.0, QColor(C_BG_END))
        p.setBrush(QPalette.Window, QBrush(g))
        self.setPalette(p)
        self.setStyleSheet("*{ font-family: 'Microsoft YaHei UI'; }")

    # ───────────────────── 构建 UI ──────────────────────

    def _build_ui(self):
        cw = QWidget()
        self.setCentralWidget(cw)
        cw.setStyleSheet('background: transparent;')
        self._bg_canvas = BackgroundCanvas(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        root.addLayout(self._title_bar())

        body = QHBoxLayout()
        body.setSpacing(14)
        body.addLayout(self._camera_pane(), stretch=7)
        body.addLayout(self._control_pane(), stretch=3)
        root.addLayout(body, stretch=1)

        root.addLayout(self._ai_bar())
        root.addLayout(self._status_bar())

    # ── 标题栏 ─────────────────────────────────────────

    def _title_bar(self):
        bar = QHBoxLayout()
        bar.setContentsMargins(12, 0, 12, 0)

        dot = QLabel()
        dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color: #2563EB; border-radius: 4px;")
        bar.addWidget(dot)

        t1 = QLabel("VisionFlow")
        t1.setStyleSheet(_ss(C_CYAN, 15, "bold"))
        bar.addWidget(t1)

        t2 = QLabel("| 视觉智能筛选系统")
        t2.setStyleSheet(_ss(C_TEXT_MAIN, 15, "bold"))
        bar.addWidget(t2)
        bar.addStretch()

        g = QLabel()
        g.setFixedSize(6, 6)
        g.setStyleSheet("background-color: #059669; border-radius: 3px;")
        bar.addWidget(g)

        st = QLabel("系统正常")
        st.setStyleSheet(_ss(C_TEXT_SEC, 12))
        bar.addWidget(st)

        return bar

    # ── 相机画面面板 ───────────────────────────────────

    def _camera_pane(self):
        col = QVBoxLayout()
        col.setSpacing(0)

        card = QFrame()
        card.setStyleSheet(_card(12))
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet("background-color: rgba(232, 248, 238, 0.55);"
                          " border-top-left-radius: 12px; border-top-right-radius: 12px;")
        hdr.setFixedHeight(34)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 16, 0)

        dot_b = QLabel()
        dot_b.setFixedSize(6, 6)
        dot_b.setStyleSheet("background-color: #2563EB; border-radius: 3px;")
        hl.addWidget(dot_b)
        hl.addWidget(QLabel("相机画面", styleSheet=_ss(C_TEXT_SEC, 12)))
        hl.addStretch()

        live_dot = QLabel()
        live_dot.setFixedSize(5, 5)
        live_dot.setStyleSheet("background-color: #FF4444; border-radius: 2px;")
        hl.addWidget(live_dot)
        hl.addWidget(QLabel("LIVE", styleSheet=_ss("#FF4444", 9, "bold")))

        sep1 = QLabel("|", styleSheet=_ss(C_TEXT_DIM, 11))
        hl.addWidget(sep1)

        self._file_label = QLabel("--", styleSheet=_ss(C_TEXT_DIM, 11))
        hl.addWidget(self._file_label)

        cl.addWidget(hdr)

        img_frame = QFrame()
        img_frame.setStyleSheet("background: transparent;")
        il = QVBoxLayout(img_frame)
        self._image_label = QLabel("正在初始化视频流...")
        self._image_label.setAlignment(Qt.AlignCenter)
        self._image_label.setMinimumSize(640, 420)
        self._image_label.setStyleSheet("background: transparent; border: none;")
        self._image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        il.addWidget(self._image_label)
        cl.addWidget(img_frame, stretch=1)

        col.addWidget(card)
        return col

    # ── 控制面板 ───────────────────────────────────────

    def _control_pane(self):
        col = QVBoxLayout()
        col.setSpacing(8)

        card = QFrame()
        card.setStyleSheet(_card(12))
        card.setMinimumWidth(320)
        card.setMaximumWidth(360)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 14, 14, 14)
        cl.setSpacing(8)

        # 标题
        cl.addWidget(QLabel("控制中心", styleSheet=_ss(C_TEXT_MAIN, 14, "bold")))
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: rgba(0,0,0,0.06);")
        cl.addWidget(sep)

        # 工作模式
        cl.addWidget(QLabel("工作模式", styleSheet=_ss(C_TEXT_SEC, 11)))
        mr = QHBoxLayout()
        mr.setSpacing(6)
        self._btn_mode_match = QPushButton("智能匹配")
        self._btn_mode_select = QPushButton("直接选择")
        for b, m in [(self._btn_mode_match, 1), (self._btn_mode_select, 0)]:
            b.setCheckable(True)
            b.setMinimumHeight(34)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda checked, v=m: self._set_work_mode(v))
            mr.addWidget(b)
        cl.addLayout(mr)
        self._update_mode_buttons()

        # === 直接选择模式：下拉框 ===
        self._select_mode_widget = QWidget()
        sm_lay = QVBoxLayout(self._select_mode_widget)
        sm_lay.setContentsMargins(0, 0, 0, 0)
        sm_lay.setSpacing(4)
        sm_lay.addWidget(QLabel("螺丝型号", styleSheet=_ss(C_TEXT_SEC, 11)))
        self._screw_combo = QComboBox()
        self._screw_combo.setMinimumHeight(36)
        self._screw_combo.setStyleSheet("""
            QComboBox {
                background-color: #F8F9FA; border: 1px solid #CED4DA;
                border-radius: 8px; padding-left: 12px; font-size: 13px; color: #2D3436;
            }
            QComboBox::drop-down { border: none; background: transparent; width: 32px; }
            QComboBox QAbstractItemView {
                background-color: white; selection-background-color: #E1F5FE;
                selection-color: #01579B; border: 1px solid #CED4DA;
            }
        """)
        self._populate_screw_combo()
        self._screw_combo.currentIndexChanged.connect(self._on_screw_selected)
        sm_lay.addWidget(self._screw_combo)
        cl.addWidget(self._select_mode_widget)

        # === 智能匹配模式：螺丝列表（检测完成后填充） ===
        self._match_mode_widget = QWidget()
        mm_lay = QVBoxLayout(self._match_mode_widget)
        mm_lay.setContentsMargins(0, 0, 0, 0)
        mm_lay.setSpacing(4)

        self._screw_count_label = QLabel("检测到 0 颗螺丝", styleSheet=_ss(C_TEXT_SEC, 11))
        mm_lay.addWidget(self._screw_count_label)

        # 可滚动的螺丝列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }"
                             "QScrollBar:vertical { width: 4px; }")
        self._screw_list_inner = QWidget()
        self._screw_list_layout = QVBoxLayout(self._screw_list_inner)
        self._screw_list_layout.setContentsMargins(0, 0, 0, 0)
        self._screw_list_layout.setSpacing(4)
        self._screw_list_layout.addStretch()
        scroll.setWidget(self._screw_list_inner)
        mm_lay.addWidget(scroll, stretch=1)

        cl.addWidget(self._match_mode_widget)
        cl.addSpacing(24)

        # === 测量值（三列） ===
        meas = QHBoxLayout()
        meas.setSpacing(16)

        def mk_val(title):
            vb = QVBoxLayout()
            vb.setSpacing(0)
            vb.setAlignment(Qt.AlignCenter)
            t = QLabel(title, styleSheet=_ss(C_TEXT_SEC, 12))
            t.setAlignment(Qt.AlignCenter)
            vb.addWidget(t)
            v = QLabel("--", styleSheet=_ss(C_TEXT_SEC, 32, "light"))
            v.setAlignment(Qt.AlignCenter)
            vb.addWidget(v)
            u = QLabel("mm", styleSheet=_ss(C_TEXT_SEC, 12))
            u.setAlignment(Qt.AlignCenter)
            vb.addWidget(u)
            return v, vb

        self._val_d, d_vb = mk_val("螺帽直径")
        meas.addLayout(d_vb)
        self._val_l, l_vb = mk_val("螺丝长度")
        meas.addLayout(l_vb)
        self._val_w, w_vb = mk_val("螺杆直径")
        meas.addLayout(w_vb)
        cl.addLayout(meas)

        # === 匹配结果 + 偏差 ===
        self._match_result_label = QLabel("")
        self._match_result_label.setAlignment(Qt.AlignCenter)
        self._match_result_label.setVisible(False)
        cl.addWidget(self._match_result_label)

        # === 检测次数 ===
        stats = QLabel("检测次数: 0")
        stats.setStyleSheet(_ss(C_TEXT_SEC, 11))
        self._detect_count_label = stats
        cl.addWidget(stats)

        cl.addStretch()

        # === 按钮 ===
        self._btn_analyze = QPushButton("开始分析")
        self._btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #059669; color: #FFFFFF; border: none;
                min-height: 48px; border-radius: 8px; font-size: 13px; font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #047857; }
            QPushButton:pressed { background-color: #065F46; }
        """)
        self._btn_analyze.clicked.connect(self._do_analyze)
        cl.addWidget(self._btn_analyze)

        self._btn_next = QPushButton("下一个样本")
        self._btn_next.setStyleSheet("""
            QPushButton {
                background-color: #E2E8F0; color: #1E3A5F;
                min-height: 44px; border-radius: 8px; font-size: 13px; font-weight: bold;
                padding: 8px 16px; border: none;
            }
            QPushButton:hover { background-color: #CBD5E1; }
        """)
        self._btn_next.setCursor(Qt.PointingHandCursor)
        self._btn_next.clicked.connect(self._go_next)
        cl.addWidget(self._btn_next)

        self._btn_command = QPushButton("下达指令")
        self._btn_command.setStyleSheet("""
            QPushButton {
                background-color: #1E3A5F; color: #FFFFFF;
                min-height: 44px; border-radius: 8px; font-size: 13px; font-weight: bold;
                padding: 8px 16px; border: none;
            }
            QPushButton:hover { background-color: #112240; }
            QPushButton:pressed { background-color: #0C1A2E; }
        """)
        self._btn_command.clicked.connect(self._send_command)
        cl.addWidget(self._btn_command)

        col.addWidget(card)

        # 初始可见性
        self._sync_mode_visibility()
        return col

    # ── AI 信息栏 ───────────────────────────────────────

    def _ai_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(8)

        card = QFrame()
        card.setStyleSheet("background-color: rgba(210, 238, 220, 0.55);"
                           " border-radius: 8px; border: 1px solid rgba(37,99,235,0.10);")
        card.setFixedHeight(44)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(12)

        self._ai_dot = QLabel()
        self._ai_dot.setFixedSize(8, 8)
        self._ai_dot.setStyleSheet("background-color: #94A3B8; border-radius: 4px;")
        lay.addWidget(self._ai_dot)

        self._ai_status_label = QLabel("AI 模型: 未加载", styleSheet=_ss(C_TEXT_SEC, 11))
        lay.addWidget(self._ai_status_label)

        s1 = QFrame()
        s1.setFixedWidth(1)
        s1.setStyleSheet("background: rgba(0,0,0,0.05);")
        lay.addWidget(s1)

        self._ai_backend_label = QLabel("后端: --", styleSheet=_ss(C_TEXT_SEC, 11))
        lay.addWidget(self._ai_backend_label)

        s2 = QFrame()
        s2.setFixedWidth(1)
        s2.setStyleSheet("background: rgba(0,0,0,0.05);")
        lay.addWidget(s2)

        self._ai_conf_label = QLabel("置信度: --", styleSheet=_ss(C_TEXT_SEC, 11))
        lay.addWidget(self._ai_conf_label)

        lay.addStretch()
        bar.addWidget(card)
        return bar

    # ── 状态栏 ─────────────────────────────────────────

    def _status_bar(self):
        bar = QHBoxLayout()
        bar.setContentsMargins(4, 0, 4, 0)

        self._status_text = QLabel("● 系统待命")
        self._status_text.setStyleSheet(_ss("#4FC3F7", 13, "bold"))
        bar.addWidget(self._status_text)

        bar.addStretch()
        self._file_status = QLabel("源文件: --", styleSheet=_ss(C_TEXT_DIM, 11))
        bar.addWidget(self._file_status)

        return bar

    # ───────────────────── 逻辑 ─────────────────────────

    def _load_ai_info(self):
        self._ai_loaded = self.detector.ai.is_loaded
        self._ai_backend = self.detector.ai.backend or "--"

    def _scan_samples(self):
        if os.path.exists(self.sample_dir):
            self.image_files = [f for f in os.listdir(self.sample_dir)
                                if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            self.image_files.sort()

    def _populate_screw_combo(self):
        self._screw_combo.blockSignals(True)
        self._screw_combo.clear()
        for s in self.db.list_all():
            self._screw_combo.addItem(f"{s.name} (D{s.diameter}mm)", s.id)
        if screws := self.db.list_all():
            self._screw_combo.setCurrentIndex(0)
            self._on_screw_selected(0)
        self._screw_combo.blockSignals(False)

    def _on_screw_selected(self, idx):
        screws = self.db.list_all()
        if 0 <= idx < len(screws):
            s = screws[idx]
            self._selected_screw_id = s.id
            if self._work_mode == 0:
                self._diameter = s.diameter
                self._length = s.length
                self._width = None
                self._match_name = s.name
                self._match_deviation = 0.0
                self._update_meas()
                self._update_match_display()
                self._set_status(f"已选择 {s.name}", "#4FC3F7")

    def _set_work_mode(self, mode):
        self._work_mode = mode
        self._update_mode_buttons()
        self._btn_analyze.setText("确认选择" if mode == 0 else "开始分析")
        self._sync_mode_visibility()

    def _sync_mode_visibility(self):
        is_match = (self._work_mode == 1)
        self._select_mode_widget.setVisible(not is_match)
        self._match_mode_widget.setVisible(is_match)

    def _update_mode_buttons(self):
        for btn, m in [(self._btn_mode_match, 1), (self._btn_mode_select, 0)]:
            act = (m == self._work_mode)
            btn.setChecked(act)
            if act:
                btn.setStyleSheet(
                    "QPushButton { background-color: rgba(37,99,235,0.12); color: #2563EB;"
                    " border: 1px solid rgba(37,99,235,0.25); border-radius: 8px;"
                    " min-height: 34px; font-size: 12px; font-weight: bold; }")
            else:
                btn.setStyleSheet(
                    "QPushButton { background-color: rgba(0,0,0,0.15); color: #5A7184;"
                    " border: none; border-radius: 8px; min-height: 34px; font-size: 12px; }")

    def _get_frame(self):
        if not self.image_files:
            return None
        return cv2.imread(os.path.join(self.sample_dir, self.image_files[self.current_idx]))

    def _display(self, cv_img):
        if cv_img is None:
            return
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qt)
        self._image_label.setPixmap(pix.scaled(
            self._image_label.width(), self._image_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))

    # ── 螺丝列表渲染（智能匹配模式） ─────────────────────

    def _render_screw_list(self):
        """根据 _analysis_screws 渲染螺丝列表"""
        # 清除旧项（保留最后的 stretch）
        while self._screw_list_layout.count() > 0:
            item = self._screw_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        count = len(self._analysis_screws)
        self._screw_count_label.setText(f"检测到 {count} 颗螺丝")

        for i, sc in enumerate(self._analysis_screws):
            is_selected = (i == self._selected_screw_idx)
            item = self._build_screw_item(i, sc, is_selected)
            self._screw_list_layout.addWidget(item)

        self._screw_list_layout.addStretch()

    def _build_screw_item(self, idx: int, sc: dict, selected: bool) -> QFrame:
        f = QFrame()
        if selected:
            bg = "rgba(37, 99, 235, 0.12)"
            border = "1px solid rgba(37,99,235,0.30)"
        else:
            bg = "rgba(245, 252, 248, 0.5)"
            border = "1px solid rgba(100,116,139,0.10)"
        f.setStyleSheet(f"background-color: {bg}; border: {border}; border-radius: 6px;")
        f.setCursor(Qt.PointingHandCursor)
        f.setMinimumHeight(48)

        lay = QVBoxLayout(f)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(2)

        # 第一行：编号 + 匹配结果 + 偏差
        top = QHBoxLayout()
        top.setSpacing(6)
        num = QLabel(f"#{idx + 1}", styleSheet=_ss(C_CYAN, 12, "bold"))
        top.addWidget(num)

        name = sc.get("match_name", "未匹配")
        dev = sc.get("match_deviation", 999.0)
        if name and name != "未匹配":
            name_label = QLabel(name, styleSheet=_ss(C_TEXT_MAIN, 11, "bold"))
            top.addWidget(name_label)
            top.addStretch()
            dev_color = _deviation_color(dev)
            dev_label = QLabel(f"偏差 {dev:.2f}mm", styleSheet=_ss(dev_color, 10, "bold"))
            top.addWidget(dev_label)
        else:
            name_label = QLabel("未匹配", styleSheet=_ss(C_TEXT_DIM, 11))
            top.addWidget(name_label)
            top.addStretch()

        lay.addLayout(top)

        # 第二行：尺寸
        d = sc.get("diameter", 0)
        l = sc.get("length", 0)
        w = sc.get("width", 0)
        d_txt = f"{d:.1f}" if d > 0 else "--"
        l_txt = f"{l:.1f}" if l > 0 else "--"
        w_txt = f"{w:.1f}" if w > 0 else "--"
        dims = QLabel(f"螺帽 {d_txt}  长度 {l_txt}  螺杆 {w_txt}",
                      styleSheet=_ss(C_TEXT_DIM, 10))
        lay.addWidget(dims)

        # 点击选中
        f.mousePressEvent = lambda event, i=idx: self._select_screw_by_list(i)

        return f

    def _select_screw_by_list(self, idx: int):
        """用户点击螺丝列表中的某一项"""
        if idx < 0 or idx >= len(self._analysis_screws):
            return
        self._selected_screw_idx = idx
        sc = self._analysis_screws[idx]

        self._diameter = sc.get("diameter", 0)
        self._length = sc.get("length", 0)
        self._width = sc.get("width", 0)
        self._match_name = sc.get("match_name", "未匹配")
        self._match_deviation = sc.get("match_deviation", 999.0)

        self._update_meas()
        self._update_match_display()
        self._render_screw_list()  # 刷新列表以更新高亮

        name_txt = self._match_name if self._match_name != "未匹配" else "未匹配螺丝"
        self._set_status(f"已选择 #{idx + 1} {name_txt}", "#4FC3F7")

    # ── 核心检测 ───────────────────────────────────────

    def _load_frame(self):
        frame = self._get_frame()
        if frame is not None:
            self._display(frame)
            name = self.image_files[self.current_idx]
            self._file_label.setText(name)
            self._file_status.setText(f"源文件: {name}")

            self._diameter = 0.0
            self._length = 0.0
            self._width = 0.0
            self._match_name = "--"
            self._match_deviation = 0.0
            self._analysis_screws = []
            self._selected_screw_idx = 0
            self._update_meas()
            self._update_match_display()
            self._render_screw_list()
            self._set_status("系统就绪", "#4FC3F7")

    def _on_timer_tick(self):
        if not self.image_files:
            return
        name = self.image_files[self.current_idx]
        if self._file_label.text() != name:
            self._load_frame()
        frame = self._get_frame()
        if frame is not None:
            self._display(frame)
            self._frame_counter += 1

    def _do_analyze(self):
        frame = self._get_frame()
        if frame is None:
            return

        if self._work_mode == 0:
            self._set_status("指令待确认", "#FDCB6E")
            self._update_meas()
            return

        self._set_status("分析中...", "#FDCB6E")
        QApplication.processEvents()

        analysis = self.detector.analyze(frame)
        self._display(analysis.annotated_frame)

        self._ai_loaded = self.detector.ai.is_loaded
        self._ai_backend = self.detector.ai.backend or "--"
        self._ai_confidence = self.detector.ai.last_confidence
        self._ai_screw_count = self.detector.ai.last_box_count
        self._detection_source = "AI" if (analysis.has_ai and analysis.screws) else "Hough"
        self._update_ai()

        if analysis.screws:
            # 构建多螺丝数据
            self._analysis_screws = []
            for sr in analysis.screws:
                sc = {
                    "diameter": sr.measurement.diameter,
                    "length": sr.measurement.length,
                    "width": sr.measurement.width,
                    "match_name": sr.match.screw.name if sr.match.matched else "未匹配",
                    "match_deviation": sr.match.deviation if sr.match.matched else 999.0,
                }
                self._analysis_screws.append(sc)

            self._selected_screw_idx = 0
            self._detection_count += 1
            self._detect_count_label.setText(f"检测次数: {self._detection_count}")
            self._render_screw_list()
            self._select_screw_by_list(0)
            self._set_status("分析成功", "#00B894")
        else:
            self._diameter = 0.0
            self._length = 0.0
            self._width = 0.0
            self._match_name = "--"
            self._match_deviation = 0.0
            self._analysis_screws = []
            self._render_screw_list()
            self._update_meas()
            self._update_match_display()
            self._set_status("未检测到螺丝", "#FF7675")

    def _go_next(self):
        if not self.image_files:
            return
        self.current_idx = (self.current_idx + 1) % len(self.image_files)
        self._load_frame()

    def _send_command(self):
        if self._diameter > 0:
            print(f"[HARDWARE] 指令下发: 螺帽{self._diameter:.2f}mm 长度{self._length:.2f}mm 螺杆{self._width:.2f}mm")
            self._set_status("指令已传达", "#00B894")
        else:
            self._set_status("无有效数据", "#FF7675")

    def _set_status(self, text, color):
        self._status_text.setText(f"● {text}")
        self._status_text.setStyleSheet(_ss(color, 13, "bold"))

    def _update_meas(self):
        d = f"{self._diameter:.2f}" if self._diameter > 0 else "--"
        l = f"{self._length:.2f}" if self._length > 0 else "--"
        w = f"{self._width:.2f}" if (hasattr(self, '_width') and self._width and self._width > 0) else "--"
        self._val_d.setText(d)
        self._val_l.setText(l)
        self._val_w.setText(w)
        dc = C_CYAN if self._diameter > 0 else C_TEXT_SEC
        lc = C_GREEN if self._length > 0 else C_TEXT_SEC
        wc = C_GREEN if (hasattr(self, '_width') and self._width and self._width > 0) else C_TEXT_SEC
        self._val_d.setStyleSheet(_ss(dc, 28, "light"))
        self._val_l.setStyleSheet(_ss(lc, 28, "light"))
        self._val_w.setStyleSheet(_ss(wc, 28, "light"))

    def _update_match_display(self):
        if self._match_name and self._match_name not in ("--", "未匹配"):
            dev = self._match_deviation
            dc = _deviation_color(dev)
            txt = f"匹配: {self._match_name}  偏差 ±{dev:.2f}mm"
            self._match_result_label.setText(txt)
            self._match_result_label.setStyleSheet(_ss(dc, 12, "bold"))
            self._match_result_label.setVisible(True)
        else:
            self._match_result_label.setVisible(False)

    def _update_ai(self):
        c = "#059669" if self._ai_loaded else "#94A3B8"
        self._ai_dot.setStyleSheet(f"background-color: {c}; border-radius: 4px;")
        self._ai_status_label.setText(
            f"AI 模型: {'已加载' if self._ai_loaded else '未加载'}")
        self._ai_backend_label.setText(f"后端: {self._ai_backend}")
        conf = f"{self._ai_confidence:.3f}" if self._ai_confidence > 0 else "--"
        self._ai_conf_label.setText(f"置信度: {conf}")

    def resizeEvent(self, event):
        if hasattr(self, '_bg_canvas'):
            cw = self.centralWidget()
            if cw:
                self._bg_canvas.setGeometry(cw.rect())
        super().resizeEvent(event)

    def closeEvent(self, event):
        self._timer.stop()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


