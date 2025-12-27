import numpy as np
from PIL import Image
import cv2
import os

class CornerDetector:
    def __init__(self, k=0.04, threshold_percent=0.98):
        self.k = k
        self.threshold_percent = threshold_percent
    
    def detect_corners(self, image_path):

        image = Image.open(image_path).convert('L')
        image = np.array(image)
        

        Ix = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        Iy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        

        Ix2 = Ix ** 2
        Iy2 = Iy ** 2
        Ixy = Ix * Iy
        

        Sx2 = cv2.GaussianBlur(Ix2, (3, 3), 1)
        Sy2 = cv2.GaussianBlur(Iy2, (3, 3), 1)
        Sxy = cv2.GaussianBlur(Ixy, (3, 3), 1)
        

        rows, cols = image.shape
        

        R = np.zeros((rows, cols))
        for i in range(rows):
            for j in range(cols):
                det = Sx2[i, j] * Sy2[i, j] - Sxy[i, j] ** 2
                trace = Sx2[i, j] + Sy2[i, j]
                R[i, j] = det - self.k * trace ** 2
        

        sorted_R = np.sort(R.flatten())
        threshold = sorted_R[int(len(sorted_R) * self.threshold_percent)]
        

        corners = []
        for i in range(1, rows - 1):
            for j in range(1, cols - 1):
                if R[i, j] > threshold and R[i, j] == np.max(R[i - 1:i + 2, j - 1:j + 2]):
                    corners.append([j, i])  # OpenCV格式(x,y)
        
        return np.array(corners)
    
    def detect_and_mark_corners(self, image_path, output_path=None, radius=3, color=(0, 255, 0), thickness=-1):

        color_image = Image.open(image_path).convert('RGB')
        color_image = np.array(color_image)
        
        # 检测角点
        corners = self.detect_corners(image_path)
        

        if len(corners) > 0:
            for pt in corners:
                x, y = pt
                cv2.circle(color_image, (int(x), int(y)), radius, color, thickness)
        

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            marked_image = Image.fromarray(color_image)
            marked_image.save(output_path)
        else:
            return color_image


if __name__ == '__main__':
    detector = CornerDetector()
    input_path = r'C:\Users\86135\Desktop\trae\python\Pattern Recognition\image\uttower2.jpg'
    output_path = 'results/uttower2_keypoints.jpg'
    detector.detect_and_mark_corners(input_path, output_path)