from skimage.feature import hog
import cv2
import numpy as np
from matplotlib import pyplot as plt
from corner_detection import CornerDetector

class HOGFeatureMatcher:
    def __init__(self, k=0.04, threshold_percent=0.98, patch_size=16, orientations=8, pixels_per_cell=(8,8), cells_per_block=(2,2), ratio_threshold=0.75):
        self.detector = CornerDetector(k=k, threshold_percent=threshold_percent)
        self.patch_size = patch_size
        self.orientations = orientations
        self.pixels_per_cell = pixels_per_cell
        self.cells_per_block = cells_per_block
        self.ratio_threshold = ratio_threshold
    
    def get_valid_patch(self, img, pt):
        x, y = int(pt[0]), int(pt[1])
        y1, y2 = max(0, y-self.patch_size//2), min(img.shape[0], y+self.patch_size//2)
        x1, x2 = max(0, x-self.patch_size//2), min(img.shape[1], x+self.patch_size//2)
        patch = img[y1:y2, x1:x2]
        return patch if patch.shape == (self.patch_size, self.patch_size) else None
    
    def extract_features(self, image_path):
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        

        corners = self.detector.detect_corners(image_path)
        

        descriptors, keypoints = [], []
        for pt in corners:
            patch = self.get_valid_patch(gray, pt)
            if patch is not None:
                descriptor = hog(patch, orientations=self.orientations, 
                               pixels_per_cell=self.pixels_per_cell,
                               cells_per_block=self.cells_per_block, 
                               visualize=False)
                descriptors.append(descriptor)
                keypoints.append(cv2.KeyPoint(float(pt[0]), float(pt[1]), self.patch_size))
        
        return img, np.array(descriptors, dtype=np.float32), keypoints
    
    def match_features(self, descriptors1, descriptors2):
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        matches = bf.knnMatch(descriptors1, descriptors2, k=2)
        
        good_matches = []
        for m, n in matches:
            if m.distance < self.ratio_threshold * n.distance:
                good_matches.append(m)
        return good_matches
    
    def visualize_matches(self, img1, kp1, img2, kp2, good_matches, output_path):
        img_matches = cv2.drawMatchesKnn(img1, kp1, img2, kp2, [[m] for m in good_matches], None,
                                       flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
        
        plt.figure(figsize=(12, 6))
        plt.imshow(cv2.cvtColor(img_matches, cv2.COLOR_BGR2RGB))
        plt.title(f"HOG Feature Matching with BFMatcher\nGood Matches: {len(good_matches)}")
        plt.axis('off')
        plt.savefig(output_path)
        plt.close()
    
    def match_images(self, image1_path, image2_path, output_path):
        img1, descriptors1, kp1 = self.extract_features(image1_path)
        img2, descriptors2, kp2 = self.extract_features(image2_path)
        
        if len(descriptors1) == 0 or len(descriptors2) == 0:
            raise ValueError("No valid HOG features extracted!")
        
        good_matches = self.match_features(descriptors1, descriptors2)
        self.visualize_matches(img1, kp1, img2, kp2, good_matches, output_path)

if __name__ == "__main__":
    matcher = HOGFeatureMatcher()
    image1 = "image/uttower1.jpg"
    image2 = "image/uttower2.jpg"
    output = "results/uttower_match_hog.png"
    matcher.match_images(image1, image2, output)