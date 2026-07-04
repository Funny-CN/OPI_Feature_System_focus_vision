#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双路电机驱动模块 — Orange Pi 5 Pro 适配
从 hardware 项目 motor_control.py 移植，增加模拟模式。
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
        GPIO_AVAILABLE = True
    except ImportError:
        GPIO_AVAILABLE = False
else:
    GPIO_AVAILABLE = False

PWM_CHIP_A = "/sys/class/pwm/pwmchip2"
PWM_CHANNEL_A = 0
PWM_CHIP_B = "/sys/class/pwm/pwmchip3"
PWM_CHANNEL_B = 0
PWM_PERIOD_NS = 1000000

PIN_AIN1 = 13
PIN_AIN2 = 22
PIN_BIN1 = 11
PIN_BIN2 = 29

_pwm_dirs = {}

def _pwm_init(chip, channel):
    if not _os.path.exists(chip):
        raise RuntimeError(f"PWM chip {chip} not found")
    pwm_dir = f"{chip}/pwm{channel}"
    if not _os.path.exists(pwm_dir):
        with open(f"{chip}/export", "w") as f:
            f.write(str(channel))
        time.sleep(0.1)
    with open(f"{pwm_dir}/period", "w") as f:
        f.write(str(PWM_PERIOD_NS))
    with open(f"{pwm_dir}/duty_cycle", "w") as f:
        f.write("0")
    with open(f"{pwm_dir}/enable", "w") as f:
        f.write("1")
    _pwm_dirs[chip] = pwm_dir

def _pwm_set_duty(chip, channel, percent):
    percent = max(0, min(100, percent))
    duty_ns = int(percent / 100.0 * PWM_PERIOD_NS)
    pwm_dir = _pwm_dirs.get(chip)
    if pwm_dir:
        with open(f"{pwm_dir}/duty_cycle", "w") as f:
            f.write(str(duty_ns))

if GPIO_AVAILABLE:
    _AIN1 = digitalio.DigitalInOut(getattr(board, f"D{PIN_AIN1}"))
    _AIN1.direction = digitalio.Direction.OUTPUT
    _AIN2 = digitalio.DigitalInOut(getattr(board, f"D{PIN_AIN2}"))
    _AIN2.direction = digitalio.Direction.OUTPUT
    _BIN1 = digitalio.DigitalInOut(getattr(board, f"D{PIN_BIN1}"))
    _BIN1.direction = digitalio.Direction.OUTPUT
    _BIN2 = digitalio.DigitalInOut(getattr(board, f"D{PIN_BIN2}"))
    _BIN2.direction = digitalio.Direction.OUTPUT
    _pwm_init(PWM_CHIP_A, PWM_CHANNEL_A)
    _pwm_init(PWM_CHIP_B, PWM_CHANNEL_B)
    logger.info("电机 GPIO 初始化完成")
else:
    logger.info("运行在电机模拟模式")

def motor_forward(speed=50):
    if GPIO_AVAILABLE:
        _AIN1.value = True
        _AIN2.value = False
        _pwm_set_duty(PWM_CHIP_A, PWM_CHANNEL_A, speed)
    logger.info(f"[电机] 正转 speed={speed}")

def motor_reverse(speed=50):
    if GPIO_AVAILABLE:
        _AIN1.value = False
        _AIN2.value = True
        _pwm_set_duty(PWM_CHIP_A, PWM_CHANNEL_A, speed)
    logger.info(f"[电机] 反转 speed={speed}")

def motor_stop():
    if GPIO_AVAILABLE:
        _AIN1.value = False
        _AIN2.value = False
        _pwm_set_duty(PWM_CHIP_A, PWM_CHANNEL_A, 0)
    logger.info("[电机] 停止")

def vibrator_on(speed=50):
    if GPIO_AVAILABLE:
        _BIN1.value = True
        _BIN2.value = False
        _pwm_set_duty(PWM_CHIP_B, PWM_CHANNEL_B, speed)
    logger.info(f"[振动] 开启 speed={speed}")

def vibrator_off():
    if GPIO_AVAILABLE:
        _BIN1.value = False
        _BIN2.value = False
        _pwm_set_duty(PWM_CHIP_B, PWM_CHANNEL_B, 0)
    logger.info("[振动] 停止")

def emergency_stop():
    motor_stop()
    vibrator_off()
    logger.warning("[急停] 所有电机已停止")

def is_hardware_available():
    return GPIO_AVAILABLE
