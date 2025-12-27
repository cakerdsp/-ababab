import cv2
import numpy as np
from matplotlib import pyplot as plt
from corner_detection import CornerDetector

class SIFTFeatureMatcher:
    def __init__(self, k=0.04, threshold_percent=0.98, ratio_threshold=0.75):
        self.detector = CornerDetector(k=k, threshold_percent=threshold_percent)
        self.ratio_threshold = ratio_threshold
    
    def extract_features(self, image_path):
        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Image {image_path} could not be loaded.")
            return None, None
            
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        corners = self.detector.detect_corners(image_path)
        
        if len(corners) == 0:
            print(f"Warning: No corners detected in {image_path}")
            return None, None
            
        keypoints = [cv2.KeyPoint(x=float(pt[0]), y=float(pt[1]), size=20) for pt in corners]
        sift = cv2.SIFT_create()
        keypoints, descriptors = sift.compute(gray, keypoints)
        
        return keypoints, descriptors
    
    def match_features(self, des1, des2):
        if des1 is None or des2 is None:
            return []
            
        matches = []
        for i in range(len(des1)):
            distances = []
            for j in range(len(des2)):
                dist = np.sqrt(np.sum((des1[i] - des2[j])**2))
                distances.append((j, dist))
            distances.sort(key=lambda x: x[1])
            matches.append((i, distances[0][0], distances[0][1], distances[1][0], distances[1][1]))
        
        good = []
        for match in matches:
            if match[2] < self.ratio_threshold * match[4]:
                good.append(cv2.DMatch(_queryIdx=match[0], _trainIdx=match[1], _distance=match[2]))
        
        return good
    
    def visualize_matches(self, img1, kp1, img2, kp2, good_matches, output_path):
        # 将每个DMatch对象包装成列表形式
        matches = [[m] for m in good_matches]
        img3 = cv2.drawMatchesKnn(img1, kp1, img2, kp2, matches, None, 
                                 flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        img3 = cv2.cvtColor(img3, cv2.COLOR_BGR2RGB)
        plt.imsave(output_path, img3)
        print(f"Matching result saved to {output_path}")


def extract_and_match_sift(image1_path, image2_path, output_path):
    matcher = SIFTFeatureMatcher()
    
    kp1, des1 = matcher.extract_features(image1_path)
    kp2, des2 = matcher.extract_features(image2_path)
    
    if kp1 is None or kp2 is None:
        return
        
    good_matches = matcher.match_features(des1, des2)
    
    if len(good_matches) == 0:
        print("Warning: No good matches found.")
        return
    
    img1 = cv2.imread(image1_path)
    img2 = cv2.imread(image2_path)
    matcher.visualize_matches(img1, kp1, img2, kp2, good_matches, output_path)

if __name__ == "__main__":
    image1 = "image/uttower1.jpg"
    image2 = "image/uttower2.jpg"
    output = "results/uttower_match_sift.png"
    extract_and_match_sift(image1, image2, output)
