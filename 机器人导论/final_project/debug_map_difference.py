#!/usr/bin/env python3
"""
地图差异调试脚本
用于详细分析rviz显示的地图和Gazebo中障碍物的差异
"""
import rospy
import numpy as np
from PIL import Image
import yaml
import cv2
from nav_msgs.msg import OccupancyGrid
from gazebo_msgs.msg import ModelStates
import matplotlib.pyplot as plt
import os

class MapDebugger:
    def __init__(self):
        rospy.init_node('map_debugger', anonymous=True)
        
        self.map_data = None
        self.gazebo_models = None
        
        # 订阅话题
        rospy.Subscriber('/map', OccupancyGrid, self.map_callback)
        rospy.Subscriber('/gazebo/model_states', ModelStates, self.models_callback)
        
        rospy.loginfo("地图调试器已启动...")
        
    def map_callback(self, msg):
        """接收ROS地图数据"""
        self.map_data = msg
        rospy.loginfo(f"接收到ROS地图: {msg.info.width}x{msg.info.height}, 分辨率: {msg.info.resolution}")
        rospy.loginfo(f"地图原点: {msg.info.origin.position.x}, {msg.info.origin.position.y}")
        
    def models_callback(self, msg):
        """接收Gazebo模型状态"""
        self.gazebo_models = msg
        obstacle_count = 0
        for name in msg.name:
            if 'obstacle' in name:
                obstacle_count += 1
        rospy.loginfo(f"Gazebo中发现 {obstacle_count} 个障碍物模型")
        
    def load_pgm_file(self, yaml_path):
        """加载PGM地图文件"""
        try:
            with open(yaml_path, 'r') as f:
                map_info = yaml.safe_load(f)
                
            pgm_path = map_info['image'] 
            if not os.path.isabs(pgm_path):
                # 相对路径转绝对路径
                yaml_dir = os.path.dirname(yaml_path)
                pgm_path = os.path.join(yaml_dir, pgm_path)
                
            # 读取PGM图像
            image = Image.open(pgm_path)
            pgm_data = np.array(image)
            
            rospy.loginfo(f"加载PGM文件: {pgm_path}")
            rospy.loginfo(f"PGM尺寸: {pgm_data.shape}")
            rospy.loginfo(f"PGM值范围: {pgm_data.min()} - {pgm_data.max()}")
            
            return pgm_data, map_info
            
        except Exception as e:
            rospy.logerr(f"加载PGM文件失败: {e}")
            return None, None
    
    def get_gazebo_obstacles(self):
        """获取Gazebo中的障碍物位置"""
        if self.gazebo_models is None:
            return []
            
        obstacles = []
        for i, name in enumerate(self.gazebo_models.name):
            if 'obstacle' in name:
                pos = self.gazebo_models.pose[i].position
                obstacles.append({
                    'name': name,
                    'x': pos.x,
                    'y': pos.y,
                    'z': pos.z
                })
        return obstacles
    
    def analyze_differences(self):
        """分析地图差异"""
        if self.map_data is None:
            rospy.logwarn("未接收到ROS地图数据")
            return
            
        # 1. 转换ROS地图数据
        ros_width = self.map_data.info.width
        ros_height = self.map_data.info.height
        ros_resolution = self.map_data.info.resolution
        ros_origin_x = self.map_data.info.origin.position.x
        ros_origin_y = self.map_data.info.origin.position.y
        
        ros_data = np.array(self.map_data.data).reshape((ros_height, ros_width))
        
        rospy.loginfo("=== ROS地图信息 ===")
        rospy.loginfo(f"尺寸: {ros_width}x{ros_height}")
        rospy.loginfo(f"分辨率: {ros_resolution}")
        rospy.loginfo(f"原点: ({ros_origin_x}, {ros_origin_y})")
        rospy.loginfo(f"数据范围: {ros_data.min()} - {ros_data.max()}")
        
        # 统计ROS地图中的值
        unique_values, counts = np.unique(ros_data, return_counts=True)
        rospy.loginfo("ROS地图值分布:")
        for val, count in zip(unique_values, counts):
            percentage = count / ros_data.size * 100
            rospy.loginfo(f"  值 {val}: {count} 像素 ({percentage:.1f}%)")
        
        # 2. 加载PGM文件
        pgm_data, map_info = self.load_pgm_file("src/Robot-Planner/maps/gazebo_map.yaml")
        if pgm_data is not None:
            rospy.loginfo("=== PGM文件信息 ===")
            rospy.loginfo(f"尺寸: {pgm_data.shape}")
            rospy.loginfo(f"分辨率: {map_info['resolution']}")
            rospy.loginfo(f"原点: {map_info['origin']}")
            rospy.loginfo(f"数据范围: {pgm_data.min()} - {pgm_data.max()}")
            
            # 统计PGM中的值
            unique_values, counts = np.unique(pgm_data, return_counts=True)
            rospy.loginfo("PGM文件值分布:")
            for val, count in zip(unique_values, counts):
                percentage = count / pgm_data.size * 100
                rospy.loginfo(f"  值 {val}: {count} 像素 ({percentage:.1f}%)")
        
        # 3. 获取Gazebo障碍物信息
        obstacles = self.get_gazebo_obstacles()
        rospy.loginfo("=== Gazebo障碍物信息 ===")
        rospy.loginfo(f"障碍物数量: {len(obstacles)}")
        for i, obs in enumerate(obstacles):
            rospy.loginfo(f"  {i+1}. {obs['name']}: ({obs['x']:.2f}, {obs['y']:.2f})")
        
        # 4. 比较分析
        if pgm_data is not None:
            # 计算障碍物在地图中的理论位置
            rospy.loginfo("=== 障碍物地图位置分析 ===")
            map_width = 20.0
            map_height = 20.0
            resolution = 0.1
            
            for obs in obstacles:
                # 世界坐标转网格坐标
                grid_x = int((obs['x'] + map_width/2) / resolution)
                grid_y = int((map_height/2 - obs['y']) / resolution)  # Y轴翻转
                
                grid_x = max(0, min(grid_x, pgm_data.shape[1] - 1))
                grid_y = max(0, min(grid_y, pgm_data.shape[0] - 1))
                
                pgm_value = pgm_data[grid_y, grid_x] if 0 <= grid_y < pgm_data.shape[0] and 0 <= grid_x < pgm_data.shape[1] else "越界"
                ros_value = ros_data[grid_y, grid_x] if 0 <= grid_y < ros_data.shape[0] and 0 <= grid_x < ros_data.shape[1] else "越界"
                
                rospy.loginfo(f"  {obs['name']}: 世界({obs['x']:.2f}, {obs['y']:.2f}) -> 网格({grid_x}, {grid_y})")
                rospy.loginfo(f"    PGM值: {pgm_value}, ROS值: {ros_value}")
        
        # 5. 保存比较图像
        self.save_debug_images(ros_data, pgm_data, obstacles)
    
    def save_debug_images(self, ros_data, pgm_data, obstacles):
        """保存调试图像"""
        try:
            # 创建调试目录
            debug_dir = "debug_images"
            os.makedirs(debug_dir, exist_ok=True)
            
            # 保存ROS地图图像
            ros_img = ros_data.copy().astype(np.uint8)
            # 将ROS地图转换为可视化格式：0=黑色(障碍物), 100=白色(自由), -1=灰色(未知)
            ros_visual = np.where(ros_img == -1, 127, ros_img)  # 未知区域设为灰色
            ros_visual = np.where(ros_visual == 100, 255, ros_visual)  # 自由空间设为白色
            ros_visual = np.where(ros_visual == 0, 0, ros_visual)  # 障碍物设为黑色
            
            cv2.imwrite(f"{debug_dir}/ros_map.png", ros_visual)
            rospy.loginfo(f"保存ROS地图图像: {debug_dir}/ros_map.png")
            
            if pgm_data is not None:
                # 保存PGM地图图像
                cv2.imwrite(f"{debug_dir}/pgm_map.png", pgm_data)
                rospy.loginfo(f"保存PGM地图图像: {debug_dir}/pgm_map.png")
                
                # 创建对比图像
                fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                
                axes[0].imshow(pgm_data, cmap='gray', origin='upper')
                axes[0].set_title('PGM文件地图')
                axes[0].set_xlabel('X (像素)')
                axes[0].set_ylabel('Y (像素)')
                
                axes[1].imshow(ros_visual, cmap='gray', origin='upper')
                axes[1].set_title('ROS /map话题')
                axes[1].set_xlabel('X (像素)')
                axes[1].set_ylabel('Y (像素)')
                
                # 差异图
                if pgm_data.shape == ros_data.shape:
                    # 将两个地图都转换为相同格式进行比较
                    pgm_binary = (pgm_data == 0).astype(np.uint8) * 255
                    ros_binary = (ros_data == 0).astype(np.uint8) * 255
                    diff = np.abs(pgm_binary.astype(int) - ros_binary.astype(int))
                    
                    axes[2].imshow(diff, cmap='hot', origin='upper')
                    axes[2].set_title('差异图 (红色=不同)')
                    axes[2].set_xlabel('X (像素)')
                    axes[2].set_ylabel('Y (像素)')
                else:
                    axes[2].text(0.5, 0.5, '尺寸不匹配', transform=axes[2].transAxes, 
                               ha='center', va='center', fontsize=16)
                    axes[2].set_title('差异图')
                
                # 标记障碍物位置
                for obs in obstacles:
                    grid_x = int((obs['x'] + 10) / 0.1)
                    grid_y = int((10 - obs['y']) / 0.1)
                    
                    if 0 <= grid_x < 200 and 0 <= grid_y < 200:
                        axes[0].plot(grid_x, grid_y, 'ro', markersize=8, alpha=0.7)
                        axes[1].plot(grid_x, grid_y, 'ro', markersize=8, alpha=0.7)
                
                plt.tight_layout()
                plt.savefig(f"{debug_dir}/map_comparison.png", dpi=150, bbox_inches='tight')
                plt.close()
                rospy.loginfo(f"保存对比图像: {debug_dir}/map_comparison.png")
                
        except Exception as e:
            rospy.logerr(f"保存调试图像时出错: {e}")

if __name__ == "__main__":
    try:
        debugger = MapDebugger()
        
        # 等待数据
        rospy.loginfo("等待地图和模型数据...")
        rate = rospy.Rate(1)  # 1Hz
        
        for i in range(10):  # 等待10秒
            if debugger.map_data is not None and debugger.gazebo_models is not None:
                break
            rate.sleep()
        
        if debugger.map_data is None:
            rospy.logerr("未接收到地图数据！")
        elif debugger.gazebo_models is None:
            rospy.logerr("未接收到Gazebo模型数据！")
        else:
            # 开始分析
            debugger.analyze_differences()
            
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        rospy.logerr(f"调试过程中出错: {e}")
        import traceback
        traceback.print_exc() 