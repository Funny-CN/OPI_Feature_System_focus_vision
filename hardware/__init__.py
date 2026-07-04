"""
Orange Pi 5 Pro 硬件适配层

提供电机控制、电阻尺/微动开关传感器、红外传感器的 Python 接口，
自动检测硬件环境，若 Orange Pi 专属库不可用则回退到模拟模式。

用法:
    from hardware.hardware_manager import HardwareManager
    hw = HardwareManager()
    hw.connect()
    hw.perform_sorting(target_mm=12.5)
"""

from hardware.hardware_manager import HardwareManager

__all__ = ["HardwareManager"]
