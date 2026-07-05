#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
硬件管理器 — 统一的硬件操作接口
从 hardware 项目 main.py 重构，将流程控制封装为可被 GUI 调用的方法。
"""

import time
import logging
import threading

from hardware import opi_motor as motor
from hardware import opi_sensor as sensor
from hardware import opi_ir as ir_sensor
from core.database import ScrewDatabase

logger = logging.getLogger(__name__)


class HardwareManager:
    STATUS_DISCONNECTED = "disconnected"
    STATUS_CONNECTING = "connecting"
    STATUS_CONNECTED = "connected"
    STATUS_HOMING = "homing"
    STATUS_SORTING = "sorting"
    STATUS_COMPLETED = "completed"
    STATUS_ERROR = "error"

    def __init__(self):
        self._status = self.STATUS_DISCONNECTED
        self._current_displacement = 0.0
        self._current_target = 0.0
        self._lock = threading.Lock()
        self._stop_flag = False
        self._hardware_available = False
        self._db = ScrewDatabase()
        self._slot_width = 0.0
        self._slot_width_warning = ""

    @property
    def status(self): return self._status

    @property
    def current_displacement(self): return self._current_displacement

    @property
    def current_target(self): return self._current_target

    @property
    def hardware_available(self): return self._hardware_available

    @property
    def slot_width(self): return self._slot_width

    @property
    def slot_width_warning(self): return self._slot_width_warning

    @property
    def is_busy(self):
        return self._status in (self.STATUS_HOMING, self.STATUS_SORTING, self.STATUS_CONNECTING)

    def connect(self) -> bool:
        self._status = self.STATUS_CONNECTING
        self._stop_flag = False
        try:
            self._hardware_available = any([
                motor.is_hardware_available(),
                sensor.is_ads_available(),
                ir_sensor.is_ir_available()
            ])
            self._status = self.STATUS_CONNECTED
            logger.info(f"硬件连接完成 (可用={self._hardware_available})")
            return True
        except Exception as e:
            logger.error(f"硬件连接失败: {e}")
            self._status = self.STATUS_ERROR
            return False

    def disconnect(self):
        self._stop_flag = True
        motor.emergency_stop()
        self._status = self.STATUS_DISCONNECTED
        logger.info("硬件已断开")

    def home(self):
        self._status = self.STATUS_HOMING
        self._stop_flag = False
        try:
            if self._hardware_available:
                motor.motor_reverse(speed=20)
                timeout = 10.0
                start = time.monotonic()
                while not sensor.is_home():
                    if self._stop_flag or time.monotonic() - start > timeout:
                        motor.motor_stop()
                        self._status = self.STATUS_ERROR
                        return False
                    time.sleep(0.02)
                motor.motor_stop()
            else:
                sensor.sim_press_home(True)
                time.sleep(0.5)
                sensor.sim_press_home(False)
            sensor.reset_zero()
            self._current_displacement = 0.0
            self._status = self.STATUS_CONNECTED
            logger.info("[归零] 完成")
            return True
        except Exception as e:
            logger.error(f"[归零] 失败: {e}")
            self._status = self.STATUS_ERROR
            return False

    def perform_sorting(self, target_mm: float):
        self._status = self.STATUS_SORTING
        self._stop_flag = False
        self._current_target = target_mm
        logger.info(f"[分选] 开始，目标={target_mm:.2f}mm")

        try:
            motor.vibrator_on(speed=60)

            settle_count = 0
            while True:
                if self._stop_flag:
                    self._status = self.STATUS_DISCONNECTED
                    return False

                current = sensor.get_displacement()
                if current is None:
                    time.sleep(0.2)
                    continue

                self._current_displacement = current
                error = target_mm - current

                if error > 0.3:
                    motor.motor_forward(30)
                    settle_count = 0
                elif error < -0.3:
                    motor.motor_reverse(30)
                    settle_count = 0
                else:
                    motor.motor_stop()
                    settle_count += 1
                    if settle_count >= 5:
                        break

                time.sleep(0.05)

            motor.motor_stop()

            no_object_time = 0.0
            while True:
                if self._stop_flag:
                    return False
                if ir_sensor.is_object_present():
                    no_object_time = 0.0
                    if not self._hardware_available:
                        ir_sensor.sim_set_object_present(False)
                else:
                    no_object_time += 0.05
                    if no_object_time >= 5.0:
                        break
                time.sleep(0.05)

            motor.vibrator_off()
            self._status = self.STATUS_COMPLETED
            logger.info(f"[分选] 完成，目标={target_mm:.2f}mm")
            return True

        except Exception as e:
            logger.error(f"[分选] 异常: {e}")
            motor.emergency_stop()
            self._status = self.STATUS_ERROR
            return False

    # ── 槽宽计算（参考硬件联动项目 compute_slot_width）─────────────────
    @staticmethod
    def compute_slot_width(measurements, tolerance_mm=0.15):
        """
        根据 1~3 组 (螺帽直径, 螺杆直径) 计算最优槽宽 W。

        Args:
            measurements: list of (head_diameter, shaft_diameter) tuples
            tolerance_mm: 安全余量

        Returns:
            (W, warning) — W 为槽宽 (mm)，warning 为备注或 None
        """
        if not measurements:
            return 0.0, "无测量数据"
        sorted_m = sorted(measurements, key=lambda m: m[0])
        n = len(sorted_m)
        Ns = [m[0] for m in sorted_m]
        Ss = [m[1] for m in sorted_m]
        if n >= 3:
            lower = max(Ns[0], Ss[1])
            upper = min(Ns[1], Ss[2])
            desc = "3种"
        elif n == 2:
            N0, S0 = sorted_m[0]
            N1, S1 = sorted_m[1]
            ratio = N1 / N0 if N0 > 0 else 99
            if ratio > 1.7:
                lower = N0
                upper = S1
                desc = "2种(疑似跳中)"
            elif N1 > 9.0:
                lower = S0
                upper = min(N0, S1)
                desc = "2种(中+大)"
            else:
                lower = max(N0, S1)
                upper = N1
                desc = "2种(小+中)"
        else:
            N, S = sorted_m[0]
            if N < 6.0:
                lower = N
                upper = N + 2.0
                desc = "1种(小)"
            elif N < 9.0:
                lower = S
                upper = N
                desc = "1种(中)"
            else:
                lower = S - 2.0
                upper = S
                desc = "1种(大)"
        lower_safe = lower + tolerance_mm
        upper_safe = upper - tolerance_mm
        if lower_safe >= upper_safe:
            W = round((lower + upper) / 2, 2)
            return W, f"{desc} W={W:.2f} [{lower:.2f}~{upper:.2f}] 无安全窗口"
        W = round((lower_safe + upper_safe) / 2, 2)
        return W, None

    # ── 智能目标计算（参考硬件联动项目 sort_by_measurements）─────────
    def calculate_sort_target(self, head_diameter: float, shaft_diameter: float):
        """
        根据测量值计算 V 型槽目标开合宽度。
        优先匹配数据库型号，用 diameter + 0.5 作为目标；
        匹配失败则回退到 shaft_diameter + 0.5 或 head_diameter + 0.3。

        Returns:
            (target_mm, screw_name)
        """
        target = (shaft_diameter + 0.5) if shaft_diameter > 0 else (head_diameter + 0.3)
        screw_name = "未知型号"

        match = self._db.match(shaft_diameter if shaft_diameter > 0 else head_diameter)
        if match.matched and match.screw:
            target = match.screw.diameter + 0.5
            screw_name = match.screw.name

        return target, screw_name

    # ── 批量分拣（参考硬件联动项目 batch_sort）───────────────────────
    def perform_batch_sorting(self, measurements):
        """
        批量分拣：根据多颗螺丝的测量值计算最优槽宽 W，然后执行分选。

        Args:
            measurements: list of (head_diameter, shaft_diameter) tuples

        Returns:
            bool: 分拣是否成功
        """
        if not measurements:
            logger.warning("[批量分选] 无测量数据，跳过")
            return False

        W, warning = self.compute_slot_width(measurements)
        self._slot_width = W
        self._slot_width_warning = warning or ""

        if W <= 0:
            logger.error("[批量分选] 无法计算有效槽宽")
            return False

        logger.info(f"[批量分选] W={W:.2f}mm, {len(measurements)}颗螺丝, {warning or ''}")
        return self.perform_sorting(W)

    def emergency_stop(self):
        logger.warning("[急停] 触发")
        self._stop_flag = True
        motor.emergency_stop()
        self._status = self.STATUS_DISCONNECTED

    def evaluate_status_text(self):
        mapping = {
            self.STATUS_DISCONNECTED: "硬件未连接",
            self.STATUS_CONNECTING: "连接中...",
            self.STATUS_CONNECTED: "硬件就绪",
            self.STATUS_HOMING: "归零中...",
            self.STATUS_SORTING: "分选中...",
            self.STATUS_COMPLETED: "分选完成",
            self.STATUS_ERROR: "硬件错误",
        }
        return mapping.get(self._status, "未知状态")

    @staticmethod
    def is_hardware_platform():
        return motor.is_hardware_available()
