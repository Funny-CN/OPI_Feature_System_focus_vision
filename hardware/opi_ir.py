#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红外传感器模块 (E18-D80NK) — Orange Pi 5 Pro 适配
"""

import time
import os as _os
import logging

logger = logging.getLogger(__name__)

_ON_ORANGE_PI = _os.path.exists("/sys/class/pwm/pwmchip2")

if _ON_ORANGE_PI:
    try:
        import board
        import digitalio
        IR_AVAILABLE = True
    except ImportError:
        IR_AVAILABLE = False
else:
    IR_AVAILABLE = False

if IR_AVAILABLE:
    _ir_pin = digitalio.DigitalInOut(board.D16)
    _ir_pin.direction = digitalio.Direction.INPUT
    _ir_pin.pull = digitalio.Pull.UP
    logger.info("红外传感器初始化完成")
else:
    logger.info("运行在红外传感器模拟模式")
    _sim_object_present = False

def is_object_present():
    if IR_AVAILABLE:
        return not _ir_pin.value
    else:
        return _sim_object_present

def is_clear():
    return not is_object_present()

def wait_clear(timeout=5.0):
    start = time.monotonic()
    while is_object_present():
        if time.monotonic() - start >= timeout:
            return False
        time.sleep(0.02)
    return True

def wait_object(timeout=5.0):
    start = time.monotonic()
    while not is_object_present():
        if time.monotonic() - start >= timeout:
            return False
        time.sleep(0.02)
    return True

def sim_set_object_present(present: bool = True):
    global _sim_object_present
    _sim_object_present = present

def is_ir_available():
    return IR_AVAILABLE
