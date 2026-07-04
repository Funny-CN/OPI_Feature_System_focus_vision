#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电阻尺 + 微动开关传感器模块 — Orange Pi 5 Pro 适配
"""

import time
import os as _os
import logging
import random

logger = logging.getLogger(__name__)

_ON_ORANGE_PI = _os.path.exists("/sys/class/pwm/pwmchip2")

if _ON_ORANGE_PI:
    try:
        import board
        import digitalio
        import busio
        from adafruit_ads1x15 import ads1115
        from adafruit_ads1x15.ads1x15 import Pin
        from adafruit_ads1x15.analog_in import AnalogIn
        ADS_AVAILABLE = True
    except ImportError:
        ADS_AVAILABLE = False
else:
    ADS_AVAILABLE = False

if ADS_AVAILABLE:
    _limit_switch = digitalio.DigitalInOut(board.D15)
    _limit_switch.direction = digitalio.Direction.INPUT
    _limit_switch.pull = digitalio.Pull.UP
    _i2c = busio.I2C(board.SCL, board.SDA)
    _ads = ads1115.ADS1115(_i2c)
    _chan = AnalogIn(_ads, 0)
    logger.info("ADS1115 传感器初始化完成")
else:
    logger.info("运行在传感器模拟模式")
    _sim_home_pressed = False

STROKE_MM = 25.0
V_MIN = 0.0
V_MAX = 3.3

_zero_voltage = None
_sim_current_mm = 0.0

def get_voltage():
    if ADS_AVAILABLE:
        return _chan.voltage
    else:
        v = V_MIN + (_sim_current_mm / STROKE_MM) * (V_MAX - V_MIN)
        v += random.gauss(0, 0.005)
        return max(V_MIN, min(V_MAX, v))

def get_raw():
    if ADS_AVAILABLE:
        return _chan.value
    else:
        return int(get_voltage() / V_MAX * 32767)

def is_home():
    if ADS_AVAILABLE:
        return not _limit_switch.value
    else:
        return _sim_home_pressed

def is_zeroed():
    return _zero_voltage is not None

def reset_zero(voltage=None):
    global _zero_voltage
    if voltage is None:
        _zero_voltage = get_voltage()
    else:
        _zero_voltage = voltage
    logger.info(f"[传感器] 归零完成，零点电压={_zero_voltage:.4f}V")

def get_displacement():
    global _zero_voltage, _sim_current_mm
    voltage = get_voltage()
    if is_home():
        _zero_voltage = voltage
        logger.info("[传感器] 触碰到微动开关，自动归零")
    if _zero_voltage is None:
        return None
    diff = voltage - _zero_voltage
    if diff < 0:
        diff = 0
    disp = (diff / (V_MAX - V_MIN)) * STROKE_MM
    if disp > STROKE_MM:
        disp = STROKE_MM
    if not ADS_AVAILABLE:
        _sim_current_mm = disp
    return disp

def sim_set_displacement(mm: float):
    global _sim_current_mm
    _sim_current_mm = max(0.0, min(STROKE_MM, mm))

def sim_press_home(pressed: bool = True):
    global _sim_home_pressed
    _sim_home_pressed = pressed
    if pressed:
        reset_zero()

def is_ads_available():
    return ADS_AVAILABLE
