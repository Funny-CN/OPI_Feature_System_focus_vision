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

    @property
    def status(self): return self._status

    @property
    def current_displacement(self): return self._current_displacement

    @property
    def current_target(self): return self._current_target

    @property
    def hardware_available(self): return self._hardware_available

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
