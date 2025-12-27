import cv2
import numpy as np
from matplotlib import pyplot as plt
from hog_feature import HOGFeatureMatcher
from sift_feature import SIFTFeatureMatcher

class ImageStitcher:
    def __init__(self, ransac_threshold=2.5, sift_threshold_percent =0.98,sift_ratio = 0.75, hog_threshold_persent=0.98,hog_ratio = 0.75):
        self.ransac_threshold = ransac_threshold
        self.sift_threshold_percent = sift_threshold_percent
        self.sift_ratio = sift_ratio
        self.hog_threshold_persent = hog_threshold_persent
        self.hog_ratio = hog_ratio
        self.sift_matcher = SIFTFeatureMatcher(threshold_percent=self.sift_threshold_percent, ratio_threshold=self.sift_ratio)
        self.hog_matcher = HOGFeatureMatcher(threshold_percent=self.hog_threshold_persent, ratio_threshold=self.hog_ratio)
    
    def compute_homography(self, kp1, kp2, good_matches):
        # 这一部分和之前的代码保持一致
        if hasattr(good_matches[0], 'queryIdx'):  # SIFT 匹配格式
            src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        else:  # HOG 匹配格式 (列表元组)
            src_pts = np.float32([kp1[m[0]].pt for m in good_matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m[1]].pt for m in good_matches]).reshape(-1, 1, 2)
        
        # 使用 RANSAC 计算单应性矩阵
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, self.ransac_threshold)
        return M
    
    def stitch_images(self, image1_path, image2_path, output_path, feature_type='sift'):
        img1 = cv2.imread(image1_path)
        img2 = cv2.imread(image2_path)

        if img1 is None or img2 is None:
            raise FileNotFoundError("无法读取输入图像，请检查文件路径是否正确！")

        if feature_type == 'hog':
            _, des1, kp1 = self.hog_matcher.extract_features(image1_path)
            _, des2, kp2 = self.hog_matcher.extract_features(image2_path)
            good_matches = self.hog_matcher.match_features(des1, des2)
        else:
            kp1, des1 = self.sift_matcher.extract_features(image1_path)
            kp2, des2 = self.sift_matcher.extract_features(image2_path)
            good_matches = self.sift_matcher.match_features(des1, des2)
            
        if len(good_matches) < 4:
            raise ValueError("匹配点不足，无法计算单应性矩阵，请尝试其他图像或调整特征匹配参数。")
            
        M = self.compute_homography(kp1, kp2, good_matches)
        
        # 计算拼接后的全景图尺寸
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # 计算变换后的图像角点
        corners1 = np.float32([[0,0], [0,h1-1], [w1-1,h1-1], [w1-1,0]]).reshape(-1,1,2)
        corners2 = np.float32([[0,0], [0,h2-1], [w2-1,h2-1], [w2-1,0]]).reshape(-1,1,2)
        transformed_corners = cv2.perspectiveTransform(corners1, M)
        
        # 计算新的宽度和高度
        all_corners = np.concatenate((transformed_corners, corners2), axis=0)
        x_min = min(0, all_corners[:,0,0].min())
        x_max = max(w2, all_corners[:,0,0].max())
        y_min = min(0, all_corners[:,0,1].min())
        y_max = max(h2, all_corners[:,0,1].max())
        
        # 计算平移矩阵
        tx = -x_min
        ty = -y_min
        translation = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]])
        
        # 应用变换
        panorama = cv2.warpPerspective(img1, translation @ M, (int(x_max - x_min), int(y_max - y_min)))
        panorama[int(ty):int(ty)+h2, int(tx):int(tx)+w2] = img2
        
        # 保存结果
        cv2.imwrite(output_path, panorama)
        print(f"拼接完成，结果已保存至 {output_path}")

if __name__ == "__main__":
    # 确保结果目录存在
    import os
    os.makedirs('results', exist_ok=True)
    
    image1 = "image/uttower1.jpg"
    image2 = "image/uttower2.jpg"
    
    stitcher = ImageStitcher()
    
    # 使用 SIFT 特征拼接
    stitcher.stitch_images(image1, image2, "results/uttower_stitching_sift.png", 'sift')
    
    # 使用 HOG 特征拼接
    stitcher.stitch_images(image1, image2, "results/uttower_stitching_hog.png", 'hog')
