"""
螺丝特征筛选视觉系统主程序
负责协调视觉检测和硬件控制
"""

import cv2
import json
import os
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
        if not os.path.exists('config.json'):
            print("错误: 找不到 config.json 配置文件")
            return
            
        with open('config.json', 'r') as f:
            config = json.load(f)
            
        # 3. 目标采样 (显示采样结果)
        print("开始目标采样...")
        target_path = 'samples/target.jpg'
        
        if not os.path.exists(target_path):
            print(f"错误: 找不到采样图片 {target_path}")
            return

        # 执行采样
        target_diameter = detector.target_sampling(target_path)
        
        if target_diameter is None:
            print("目标采样失败，未能在图中检测到足够的圆（硬币和螺丝）")
            return
        
        # --- 新增逻辑：展示采样预览 ---
        print(f"\n[采样完成] 识别到的标准直径为: {target_diameter:.2f} mm")
        print("请在弹出的图片窗口中检查标注是否准确，按键盘任意键开始批量检测测试图...")
        cv2.waitKey(0) 
        cv2.destroyAllWindows() # 关闭采样窗口，为接下来的检测腾出空间
        # ----------------------------
            
        # 4. 实时检测循环
        print("\n开始批量实时检测...")
        test_dir = 'test_mix/' 
        
        if not os.path.exists(test_dir):
            print(f"错误: 找不到测试文件夹 {test_dir}")
            return
            
        # 获取图片列表
        test_files = [f for f in os.listdir(test_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]

        if not test_files:
            print(f"警告: {test_dir} 文件夹内没有找到图片")
        else:
            print(f"检测到 {len(test_files)} 张测试图片，准备开始...")

            for file_name in test_files:
                img_path = os.path.join(test_dir, file_name)
                current_image = cv2.imread(img_path)
                
                if current_image is not None:
                    # 调用比对功能 (由于detector.py内部已写好绘图逻辑，会自动弹窗)
                    is_match = detector.real_time_comparison(current_image)
                    
                    status = "【合格】" if is_match else "【不合格】"
                    print(f"图片: {file_name} -> 结果: {status}")
                    
                    print("按任意键检测下一张 (或在图片窗口点关闭)...")
                    cv2.waitKey(0) 

        print("\n--- 所有图片检测完成 ---")
            
    except KeyboardInterrupt:
        print("\n程序由用户强制终止")
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        # 清理资源
        hardware.disconnect_all()
        cv2.destroyAllWindows()
        print("系统关闭")

if __name__ == "__main__":
    main()