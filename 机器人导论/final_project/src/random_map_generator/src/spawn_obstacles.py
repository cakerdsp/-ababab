#!/usr/bin/env python3
import rospy
import random
import numpy as np
import os
from PIL import Image
import yaml
from gazebo_msgs.srv import SpawnModel, SpawnModelRequest
from geometry_msgs.msg import Pose, Point, Quaternion

# ================== 配置参数 ==================
MAP_WIDTH = 20.0    # 地图宽度（米）
MAP_HEIGHT = 20.0   # 地图高度（米）
RESOLUTION = 0.1     # 地图分辨率（米/像素）
OCCUPANCY_THRESHOLD = 0.65  # 占据阈值
ppgm=rospy.get_param('pgm_path')
pyaml=rospy.get_param('yaml_path')

# ================== 障碍物生成模块 ==================
class ObstacleGenerator:
    def __init__(self):
        self.obstacles = []  # 存储障碍物信息 (x, y, size_x, size_y)
        
    def generate_in_gazebo(self, num_obstacles=10):
        """在 Gazebo 中生成障碍物并记录参数"""
        rospy.init_node('spawn_random_obstacles')
        rospy.wait_for_service('/gazebo/spawn_sdf_model')
        spawn_model = rospy.ServiceProxy('/gazebo/spawn_sdf_model', SpawnModel)

        # 设置随机种子以保证每次生成相同的障碍物布局
        random.seed(42)
        np.random.seed(42)

        for i in range(num_obstacles):
            # 随机生成障碍物参数
            x = random.uniform(-MAP_WIDTH/2 + 1, MAP_WIDTH/2 - 1)  # 留边界
            y = random.uniform(-MAP_HEIGHT/2 + 1, MAP_HEIGHT/2 - 1)  # 留边界
            size_x = random.uniform(0.8, 2.5)
            size_y = random.uniform(0.8, 2.5)
            size_z = random.uniform(0.5, 2.0)
            
            half_x = size_x / 2
            half_y = size_y / 2
            near_threshold = 3.0

            # 检查障碍物是否太靠近原点
            distance_to_origin = np.sqrt(x**2 + y**2)
            if distance_to_origin < (max(half_x, half_y) + near_threshold):
                continue
                
            # 检查是否与已有障碍物重叠
            overlap = False
            for existing_x, existing_y, existing_sx, existing_sy in self.obstacles:
                dx = abs(x - existing_x)
                dy = abs(y - existing_y)
                if dx < (half_x + existing_sx/2 + 0.5) and dy < (half_y + existing_sy/2 + 0.5):
                    overlap = True
                    break
            
            if overlap:
                continue
                
            self.obstacles.append((x, y, size_x, size_y))

            # 生成 Gazebo 模型
            model_name = f"obstacle_{i}"
            model_xml = self._create_sdf_model(size_x, size_y, size_z)
            pose = Pose(position=Point(x, y, size_z/2), orientation=Quaternion(0,0,0,1))
            
            try:
                req = SpawnModelRequest()
                req.model_name = model_name
                req.model_xml = model_xml
                req.initial_pose = pose
                req.reference_frame = "world"
                spawn_model(req)
                rospy.loginfo(f"Spawned {model_name} at ({x:.2f}, {y:.2f}) size:({size_x:.2f}, {size_y:.2f})")
            except rospy.ServiceException as e:
                rospy.logerr(f"Failed to spawn model: {e}")

    def _create_sdf_model(self, size_x, size_y, size_z):
        """生成障碍物 SDF 模型"""
        return f"""
        <sdf version="1.6">
          <model>
            <static>true</static>
            <link name="link">
              <collision name="collision">
                <geometry>
                  <box>
                    <size>{size_x} {size_y} {size_z}</size>
                  </box>
                </geometry>
              </collision>
              <visual name="visual">
                <geometry>
                  <box>
                    <size>{size_x} {size_y} {size_z}</size>
                  </box>
                </geometry>
                <material>
                  <ambient>0.7 0.5 0.3 1</ambient>
                  <diffuse>0.7 0.5 0.3 1</diffuse>
                </material>
              </visual>
            </link>
          </model>
        </sdf>
        """

# ================== PGM 地图生成模块 ==================
class PGMMapGenerator:
    def __init__(self):
        self.grid_height = int(MAP_HEIGHT / RESOLUTION)
        self.grid_width = int(MAP_WIDTH / RESOLUTION)
        # 初始化为白色(自由空间, 值为254，map_server会转换为100)
        self.grid = np.ones((self.grid_height, self.grid_width), dtype=np.uint8) * 254

    def world_to_grid(self, x, y):
        """世界坐标转像素坐标 - 修复Y轴翻转问题"""
        # X轴：从左到右，-MAP_WIDTH/2 到 +MAP_WIDTH/2 映射到 0 到 grid_width
        grid_x = int((x + MAP_WIDTH/2) / RESOLUTION)
        # Y轴：ROS地图中Y轴向上为正，但图像中Y轴向下为正
        # 世界坐标的+Y对应图像的顶部（较小的索引）
        grid_y = int((MAP_HEIGHT/2 - y) / RESOLUTION)
        
        # 确保索引在有效范围内
        grid_x = max(0, min(grid_x, self.grid_width - 1))
        grid_y = max(0, min(grid_y, self.grid_height - 1))
        
        return grid_x, grid_y

    def add_obstacle(self, x, y, size_x, size_y):
        """添加矩形障碍物到地图"""
        # 计算障碍物的四个角点
        half_x = size_x / 2
        half_y = size_y / 2
        
        # 获取障碍物边界的网格坐标
        x_min_grid, y_max_grid = self.world_to_grid(x - half_x, y - half_y)  # 左下角
        x_max_grid, y_min_grid = self.world_to_grid(x + half_x, y + half_y)  # 右上角
        
        # 确保边界有效
        x_min_grid = max(0, x_min_grid)
        x_max_grid = min(self.grid_width - 1, x_max_grid)
        y_min_grid = max(0, y_min_grid)
        y_max_grid = min(self.grid_height - 1, y_max_grid)
        
        # 在地图上标记障碍物为黑色(0)
        if x_max_grid > x_min_grid and y_max_grid > y_min_grid:
            self.grid[y_min_grid:y_max_grid+1, x_min_grid:x_max_grid+1] = 0
            rospy.loginfo(f"Added obstacle to map: world({x:.2f}, {y:.2f}) -> grid({x_min_grid}:{x_max_grid}, {y_min_grid}:{y_max_grid})")

    def save(self, pgm_path=ppgm, yaml_path=pyaml):
        """保存PGM和YAML文件"""
        # 直接保存原始网格数据，不进行转换
        # 0=黑色(障碍物)，254=白色(自由空间)
        # map_server会根据occupied_thresh和free_thresh自动转换
        
        # 保存为标准PGM图像格式
        Image.fromarray(self.grid, mode='L').save(pgm_path)
        
        # 生成YAML元数据，使用相对路径
        pgm_filename = os.path.basename(pgm_path)
        yaml_data = {
            "image": pgm_filename,  # 使用相对路径
            "resolution": RESOLUTION,
            "origin": [-MAP_WIDTH/2, -MAP_HEIGHT/2, 0.0],  # 地图左下角的世界坐标
            "occupied_thresh": OCCUPANCY_THRESHOLD,
            "free_thresh": 0.25,
            "negate": 0
        }
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False)
        
        rospy.loginfo(f"Map saved: {pgm_path} ({self.grid_width}x{self.grid_height} pixels)")
        rospy.loginfo(f"Obstacle pixels: {np.sum(self.grid == 0)}, Free pixels: {np.sum(self.grid == 254)}")

# ================== 主流程 ==================
if __name__ == "__main__":
    try:
        # 步骤1: 生成 Gazebo 障碍物
        rospy.loginfo("开始生成障碍物...")
        obstacle_gen = ObstacleGenerator()
        obstacle_gen.generate_in_gazebo(num_obstacles=15)  # 生成15个障碍物
        
        # 步骤2: 生成 PGM 地图
        rospy.loginfo("开始生成地图...")
        map_gen = PGMMapGenerator()
        for obs in obstacle_gen.obstacles:
            x, y, size_x, size_y = obs
            map_gen.add_obstacle(x, y, size_x, size_y)
        
        # 保存文件
        map_gen.save()
        rospy.loginfo(f"PGM地图已生成: {ppgm} 和 {pyaml}")
        rospy.loginfo(f"总共生成了 {len(obstacle_gen.obstacles)} 个障碍物")
    except Exception as e:
        rospy.logerr(f"生成地图时出错: {e}")
        import traceback
        traceback.print_exc()