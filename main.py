"""
螺丝特征筛选视觉系统主程序
负责协调视觉检测和硬件控制
"""

import json
from core.detector import ScrewDetector
from hardware.hardware_stub import HardwareController

def main():
    """主程序入口"""
    print("启动螺丝特征筛选视觉系统")
    
    # 初始化组件
    detector = ScrewDetector()
    hardware = HardwareController()
    
    try:
        # 1. 连接硬件
        hardware.connect_motor()
        hardware.connect_servo()
        
        # 2. 加载配置
        with open('config.json', 'r') as f:
            config = json.load(f)
            target_standard = config.get('target_standard', {})
            
        # 3. 目标采样
        print("开始目标采样...")
        target_features = detector.target_sampling(config.get('target_image', 'samples/target_screw.jpg'))
        if not target_features:
            print("目标采样失败")
            return
            
        # 4. 实时检测循环
        print("开始实时检测...")
        while True:
            # TODO: 实现实时图像获取
            # current_image = get_current_image()
            
            # 5. 特征比对
            is_match = detector.real_time_comparison(None)  # 传入当前图像
            
            # 6. 硬件控制
            if is_match:
                print("检测到匹配螺丝")
                # hardware.move_motor(steps=100, direction="forward")
                # hardware.control_servo(angle=90)
            else:
                print("检测到非匹配螺丝")
                # hardware.move_motor(steps=50, direction="backward")
                
            # 7. 延时
            # time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n程序终止")
    except Exception as e:
        print(f"程序出错: {e}")
    finally:
        # 8. 清理资源
        hardware.disconnect_all()
        print("系统关闭")

if __name__ == "__main__":
    main()