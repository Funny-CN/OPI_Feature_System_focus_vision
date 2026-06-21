"""
硬件接口模块（Orange Pi 5 Pro 适配版）
基于 OPi.GPIO / python3-gpiod 实现步进电机和舵机控制
封装硬件底层差异，上层调用无需关心引脚映射

Orange Pi 5 Pro 引脚说明（RK3585 SoC）：
  物理引脚号遵循 OPi.GPIO BOARD 模式
  步进电机: 物理引脚 11(GPIO4_A5), 13(GPIO4_A6), 15(GPIO4_A7), 16(GPIO4_B0)
  舵机信号: 物理引脚 12(GPIO4_B1) — 需软件 PWM
  限位开关: 物理引脚 18(GPIO4_B2)
"""

import time
import logging

logger = logging.getLogger(__name__)

# ---- GPIO 后端选择 ----
try:
    import OPi.GPIO as GPIO
    GPIO_BACKEND = "OPi.GPIO"
    GPIO.setmode(GPIO.BOARD)        # 使用物理引脚编号
except ImportError:
    try:
        import gpiod
        GPIO_BACKEND = "gpiod"
    except ImportError:
        GPIO_BACKEND = None


class HardwareController:
    """
    硬件控制器类
    提供步进电机和舵机的控制接口，适配 Orange Pi 5 Pro
    """

    # ---- Orange Pi 5 Pro 引脚映射（BOARD 物理编号） ----
    PIN_STEPPER_IN1 = 11   # GPIO4_A5
    PIN_STEPPER_IN2 = 13   # GPIO4_A6
    PIN_STEPPER_IN3 = 15   # GPIO4_A7
    PIN_STEPPER_IN4 = 16   # GPIO4_B0
    PIN_SERVO_SIG  = 12   # GPIO4_B1
    PIN_LIMIT_SW   = 18   # GPIO4_B2

    STEP_SEQUENCE = [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
    ]

    def __init__(self):
        """初始化硬件控制器"""
        self.motor_connected = False
        self.servo_connected = False
        self._gpio_available = GPIO_BACKEND is not None
        self._step_index = 0

        if self._gpio_available:
            logger.info(f"使用 GPIO 后端: {GPIO_BACKEND}")
        else:
            logger.warning("未检测到 GPIO 库，运行在模拟模式")

    # ── 初始化与清理 ──────────────────────────

    def connect_motor(self) -> bool:
        """连接步进电机（设置 GPIO 引脚为推挽输出）"""
        logger.info("步进电机连接中...")
        if self._gpio_available:
            pins = [
                self.PIN_STEPPER_IN1, self.PIN_STEPPER_IN2,
                self.PIN_STEPPER_IN3, self.PIN_STEPPER_IN4,
                self.PIN_LIMIT_SW,
            ]
            if GPIO_BACKEND == "OPi.GPIO":
                for pin in pins:
                    GPIO.setup(pin, GPIO.OUT)
        self.motor_connected = True
        return True

    def connect_servo(self) -> bool:
        """连接舵机（设置 PWM 引脚）"""
        logger.info("舵机连接中...")
        if self._gpio_available:
            if GPIO_BACKEND == "OPi.GPIO":
                from OPi import PWM
                self._servo_pwm = PWM.pwm_init(self.PIN_SERVO_SIG, 0, 50)  # 50 Hz
        self.servo_connected = True
        return True

    def disconnect_all(self) -> None:
        """断开所有硬件连接"""
        logger.info("断开所有硬件连接")
        if self._gpio_available and GPIO_BACKEND == "OPi.GPIO":
            GPIO.cleanup()
        self.motor_connected = False
        self.servo_connected = False

    # ── 步进电机控制 ──────────────────────────

    def move_motor(self, steps: int, direction: str = "forward") -> bool:
        """
        控制步进电机移动

        参数:
            steps:     移动步数（正数）
            direction: "forward" 或 "backward"

        返回:
            bool: 移动是否成功
        """
        if not self.motor_connected:
            logger.error("步进电机未连接")
            return False

        logger.info(f"步进电机向 {direction} 移动 {steps} 步")
        if not self._gpio_available:
            return True  # 模拟模式

        step_dir = 1 if direction == "forward" else -1
        pins_4 = [self.PIN_STEPPER_IN1, self.PIN_STEPPER_IN2,
                  self.PIN_STEPPER_IN3, self.PIN_STEPPER_IN4]

        for _ in range(steps):
            self._step_index = (self._step_index + step_dir) % len(self.STEP_SEQUENCE)
            seq = self.STEP_SEQUENCE[self._step_index]
            for pin, val in zip(pins_4, seq):
                GPIO.output(pin, val)
            time.sleep(0.002)  # 2 ms 步进脉冲

        # 断电释放线圈
        for pin in pins_4:
            GPIO.output(pin, 0)
        return True

    def move_to_limit(self, direction: str = "backward") -> bool:
        """
        向限位开关回零

        参数:
            direction: 回零方向

        返回:
            bool: 是否成功碰到限位
        """
        logger.info(f"向 {direction} 回零")
        if not self._gpio_available:
            return True

        # TODO: 循环读取限位开关引脚，碰到后停止
        # if GPIO_BACKEND == "OPi.GPIO":
        #     GPIO.setup(self.PIN_LIMIT_SW, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        #     while GPIO.input(self.PIN_LIMIT_SW) == 1:
        #         self.move_motor(1, direction)
        return True

    # ── 舵机控制 ──────────────────────────────

    def control_servo(self, angle: int) -> bool:
        """
        控制舵机角度

        参数:
            angle: 目标角度 (0-180)

        返回:
            bool: 控制是否成功
        """
        if not self.servo_connected:
            logger.error("舵机未连接")
            return False

        if not (0 <= angle <= 180):
            logger.warning(f"舵机角度 {angle} 超出 0-180 范围")
            return False

        logger.info(f"舵机设置 {angle} 度")
        if self._gpio_available:
            if GPIO_BACKEND == "OPi.GPIO" and hasattr(self, '_servo_pwm'):
                # 50 Hz → 20 ms 周期，占空比 0.5~2.5 ms → 2.5%~12.5%
                duty = 2.5 + (angle / 180.0) * 10.0
                PWM.pwm_set_duty_cycle(self._servo_pwm, duty)

        return True

    # ── 状态查询 ──────────────────────────────

    def is_connected(self) -> bool:
        """检查硬件是否已连接"""
        return self.motor_connected and self.servo_connected

    def get_gpio_backend(self) -> str:
        """返回当前 GPIO 后端名称"""
        return GPIO_BACKEND or "simulation"
