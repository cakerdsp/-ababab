import cv2
import numpy as np
from matplotlib import pyplot as plt
import os
from stitching import ImageStitcher

class MultiImageStitcher:
    def __init__(self,ransac_threshold=2,sift_threshold_percent =0.95,sift_ratio = 0.65):
        self.ransac_threshold = ransac_threshold
        self.sift_threshold_percent = sift_threshold_percent
        self.sift_ratio = sift_ratio
        self.image_stitcher = ImageStitcher(ransac_threshold=self.ransac_threshold,sift_ratio=self.sift_ratio,sift_threshold_percent=self.sift_threshold_percent)

    def stitch_images(self,image_paths):
        c = 0
        while len(image_paths) !=1:
            l = []
            # 计算相邻的匹配点数量
            for i in range(len(image_paths)-1):
                k,d1 = self.image_stitcher.sift_matcher.extract_features(image_paths[i])
                k,d2 = self.image_stitcher.sift_matcher.extract_features(image_paths[i+1])
                l.append(len(self.image_stitcher.sift_matcher.match_features(d1,d2)))
            # 选择匹配点最多的两张图像进行拼接
            j = l.index(max(l))
            tmp_path = f"results/tmp_{c}.jpg"
            # 拼接
            self.image_stitcher.stitch_images(image_paths[j],image_paths[j+1],tmp_path)
            # 替换
            image_paths[j] = tmp_path
            # 删除 
            del image_paths[j+1]
            c = c + 1

        # 删除中间结果,这个C要看看
        for i in range(c-1):
            tmp_path = f"results/tmp_{i}.jpg"
            os.remove(tmp_path)
        os.rename(image_paths[0], "results/yosemite_stitching.png")
        
if __name__ == "__main__":
    # 确保结果目录存在
    os.makedirs('results', exist_ok=True)
    
    # 读取所有输入图像
    image_paths = [
        'image/yosemite1.jpg',
        'image/yosemite2.jpg',
        'image/yosemite3.jpg',
        'image/yosemite4.jpg'
    ]
    
    
    
    # 创建拼接器并拼接图像
    stitcher = MultiImageStitcher()
    stitcher.stitch_images(image_paths)
    
    # # 保存结果
    # result_path = 'results/yosemite_stitching.png'
    # plt.imsave(result_path, cv2.cvtColor(panorama, cv2.COLOR_BGR2RGB))
    # print(f"拼接完成，结果已保存至 {result_path}")