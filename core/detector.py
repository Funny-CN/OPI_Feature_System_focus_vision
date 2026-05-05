"""
视觉检测器模块
包含螺丝特征提取和比对的核心算法
"""
       
import cv2
import numpy as np
from typing import Union, List, Optional

class ScrewDetector:
    def __init__(self, coin_real_diameter_mm: float = 25.0):
        """
        初始化检测器
        :param coin_real_diameter_mm: 参照物硬币的实际直径（默认一元硬币25.0mm）
        """
        self.coin_real_diameter_mm = coin_real_diameter_mm
        self.target_diameter_mm = None  # 存放采样出来的标准螺丝直径
        
        # 提取自你队友代码中的霍夫圆参数
        self.hough_params = {
            'dp': 1,
            'min_dist': 350,
            'param1': 100,
            'param2': 40,
            'min_radius': 60,
            'max_radius': 300
        }

    def target_sampling(self, image_path: str):
        """
        第一步：目标采样
        从一张标准图片里学习螺丝的直径，并返回直径和标注后的图片
        """
        img = cv2.imread(image_path)
        if img is None:
            print(f"错误：无法读取采样图片 {image_path}")
            return None, None
        
        # 这里的返回值对应你刚刚修改好的 _calculate_real_diameters
        diameters, processed_img = self._calculate_real_diameters(img)
        
        if diameters:
            # 记录第一个检测到的螺丝直径作为标准（通常采样图里只有一个螺丝）
            self.target_diameter_mm = diameters[0]
            # 返回直径数值和处理后的图片对象
            return self.target_diameter_mm, processed_img
            
        return None, None
        

    def real_time_comparison(self, img: np.ndarray, tolerance: float = 1.0):
        """
        核心功能：比对当前图片中的螺丝是否合格
        返回：(是否合格, 标注后的图片)
        """
        # 接收两个返回值：直径列表和标注后的图片
        diameters, processed_img = self._calculate_real_diameters(img)
        
        if not diameters:
            return False, processed_img
            
        # 检查是否有任何一个圆的直径在容差范围内
        is_match = False
        for d in diameters:
            if abs(d - self.target_diameter_mm) <= tolerance:
                is_match = True
                break
                
        return is_match, processed_img

    def _calculate_real_diameters(self, img: np.ndarray) -> List[float]:
        """
        核心算法：计算直径并在图上标注
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)
        
        circles = cv2.HoughCircles(
            image=blurred, 
            method=cv2.HOUGH_GRADIENT, 
            dp=self.hough_params['dp'],
            minDist=float(self.hough_params['min_dist']),
            param1=float(self.hough_params['param1']),
            param2=float(self.hough_params['param2']),
            minRadius=int(self.hough_params['min_radius']),
            maxRadius=int(self.hough_params['max_radius'])
        )
        
        real_diameters = []
        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
            ref_circle = max(circles, key=lambda c: c[2])
            pixel_per_mm = (2 * ref_circle[2]) / self.coin_real_diameter_mm
            
            # --- 绘图逻辑开始 ---
            for circ in circles:
                # 画圆心和圆周 (绿色)
                cv2.circle(img, (circ[0], circ[1]), circ[2], (0, 255, 0), 2)
                cv2.circle(img, (circ[0], circ[1]), 2, (0, 0, 255), 3)
                
                if np.array_equal(circ, ref_circle):
                    label = f"REF: {self.coin_real_diameter_mm}mm"
                else:
                    d_mm = (2 * circ[2]) / pixel_per_mm
                    real_diameters.append(d_mm)
                    label = f"{d_mm:.2f}mm"
                
                # 在圆旁边写上数值
                # 在圆旁边写上数值
                cv2.putText(
                    img, 
                    label, 
                    (circ[0] - 40, circ[1] - circ[2] - 20), # 坐标稍微往上移一点，避免压到圆
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1.5,           # <--- 这里的 0.8 改成 1.5 (这是字号，越大字越大)
                    (255, 0, 0),   # 颜色 (蓝色)
                    3              # <--- 这里的 2 改成 3 (这是粗细，越大字越粗)
                )
            # --- 绘图逻辑结束 ---
            
            # 显示标注后的图片
            # cv2.imshow("Detection Result", img)
            
        # 2. 修改返回值，把处理过的 img 也传出去
        return real_diameters, img  # 原来只返回 real_diameters