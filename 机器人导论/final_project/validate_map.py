#!/usr/bin/env python3
"""
地图验证脚本
用于验证Gazebo中的障碍物与PGM地图的一致性
"""
import rospy
import numpy as np
from PIL import Image
import yaml
from nav_msgs.msg import OccupancyGrid
import matplotlib.pyplot as plt

class MapValidator:
    def __init__(self):
        rospy.init_node('map_validator', anonymous=True)
        self.map_data = None
        
        # 订阅地图话题
        rospy.Subscriber('/map', OccupancyGrid, self.map_callback)
        rospy.loginfo("地图验证器已启动，等待地图数据...")
        
    def map_callback(self, msg):
        """接收地图数据回调"""
        self.map_data = msg
        rospy.loginfo(f"接收到地图数据: {msg.info.width}x{msg.info.height}, 分辨率: {msg.info.resolution}")
        
    def load_pgm_map(self, yaml_path):
        """加载PGM地图文件"""
        try:
            with open(yaml_path, 'r') as f:
                map_info = yaml.safe_load(f)
                
            pgm_path = map_info['image']
            if not pgm_path.startswith('/'):
                # 相对路径，转换为绝对路径
                import os
                yaml_dir = os.path.dirname(yaml_path)
                pgm_path = os.path.join(yaml_dir, pgm_path)
                
            image = Image.open(pgm_path)
            pgm_data = np.array(image)
            
            rospy.loginfo(f"加载PGM地图: {pgm_path}")
            rospy.loginfo(f"PGM地图尺寸: {pgm_data.shape}")
            rospy.loginfo(f"地图信息: 分辨率={map_info['resolution']}, 原点={map_info['origin']}")
            
            return pgm_data, map_info
            
        except Exception as e:
            rospy.logerr(f"加载PGM地图失败: {e}")
            return None, None
    
    def compare_maps(self, pgm_path="src/Robot-Planner/maps/gazebo_map.yaml"):
        """比较ROS地图与PGM地图"""
        if self.map_data is None:
            rospy.logwarn("未接收到ROS地图数据")
            return False
            
        # 加载PGM地图
        pgm_data, map_info = self.load_pgm_map(pgm_path)
        if pgm_data is None:
            return False
            
        # 转换ROS地图数据
        ros_width = self.map_data.info.width
        ros_height = self.map_data.info.height
        ros_data = np.array(self.map_data.data).reshape((ros_height, ros_width))
        
        # 翻转ROS地图以匹配PGM格式
        ros_data_flipped = np.flipud(ros_data)
        
        # 比较尺寸
        if pgm_data.shape != ros_data_flipped.shape:
            rospy.logerr(f"地图尺寸不匹配: PGM={pgm_data.shape}, ROS={ros_data_flipped.shape}")
            return False
            
        # 转换数据格式进行比较
        # PGM: 0=障碍物, 100=自由空间
        # ROS: 0=自由空间, 100=障碍物, -1=未知
        pgm_obstacles = (pgm_data == 0)
        ros_obstacles = (ros_data_flipped == 100)
        
        # 计算差异
        differences = np.logical_xor(pgm_obstacles, ros_obstacles)
        diff_count = np.sum(differences)
        total_pixels = pgm_data.size
        consistency_rate = (total_pixels - diff_count) / total_pixels * 100
        
        rospy.loginfo(f"地图一致性检查结果:")
        rospy.loginfo(f"  总像素数: {total_pixels}")
        rospy.loginfo(f"  差异像素数: {diff_count}")
        rospy.loginfo(f"  一致性率: {consistency_rate:.2f}%")
        
        if consistency_rate > 95:
            rospy.loginfo("✓ 地图一致性良好")
            return True
        else:
            rospy.logwarn("✗ 地图存在较大差异")
            
            # 保存差异图像用于调试
            self.save_comparison_images(pgm_data, ros_data_flipped, differences)
            return False
    
    def save_comparison_images(self, pgm_data, ros_data, differences):
        """保存比较图像"""
        try:
            fig, axes = plt.subplots(1, 3, figsize=(15, 5))
            
            axes[0].imshow(pgm_data, cmap='gray')
            axes[0].set_title('PGM Map')
            axes[0].axis('off')
            
            axes[1].imshow(ros_data, cmap='gray')
            axes[1].set_title('ROS Map')
            axes[1].axis('off')
            
            axes[2].imshow(differences, cmap='Reds')
            axes[2].set_title('Differences')
            axes[2].axis('off')
            
            plt.tight_layout()
            plt.savefig('map_comparison.png', dpi=150, bbox_inches='tight')
            rospy.loginfo("差异图像已保存为: map_comparison.png")
            
        except Exception as e:
            rospy.logerr(f"保存比较图像失败: {e}")
    
    def wait_for_map(self, timeout=30):
        """等待地图数据"""
        start_time = rospy.Time.now()
        rate = rospy.Rate(10)
        
        while not rospy.is_shutdown():
            if self.map_data is not None:
                return True
                
            if (rospy.Time.now() - start_time).to_sec() > timeout:
                rospy.logerr("等待地图数据超时")
                return False
                
            rate.sleep()
        
        return False

def main():
    try:
        validator = MapValidator()
        
        # 等待地图数据
        if not validator.wait_for_map():
            rospy.logerr("未能获取地图数据")
            return
            
        # 等待一段时间确保地图完全加载
        rospy.sleep(2.0)
        
        # 执行比较
        if validator.compare_maps():
            rospy.loginfo("地图验证通过！")
        else:
            rospy.logwarn("地图验证失败，请检查地图生成过程")
            
    except rospy.ROSInterruptException:
        rospy.loginfo("地图验证器已停止")
    except Exception as e:
        rospy.logerr(f"地图验证出错: {e}")

if __name__ == '__main__':
    main() 