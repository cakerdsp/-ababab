# 2D栅格地图机器人路径规划与跟踪系统

## 项目概述

本项目实现了一个完整的2D栅格地图机器人路径规划与跟踪系统，包含以下核心功能：

1. **随机地图生成**：在Gazebo中随机生成障碍物，并生成对应的占据栅格地图
2. **RRT*路径规划**：基于占据栅格地图，使用RRT*算法进行路径规划
3. **PID路径跟踪**：实现基于PID控制的路径跟踪，包含速度平滑和前瞻控制

## 系统架构

### 核心模块

```
├── src/
│   ├── random_map_generator/          # 地图生成模块
│   │   ├── src/spawn_obstacles.py     # 障碍物生成器
│   │   ├── launch/spawn_obstacles.launch
│   │   └── final.rviz                 # RViz配置文件
│   └── Robot-Planner/                 # 路径规划与控制模块
│       ├── scripts/
│       │   ├── planner.py            # RRT*路径规划器
│       │   ├── controller.py         # PID控制器
│       │   └── gazebo_to_tf.py       # 坐标转换
│       ├── launch/obs_world.launch   # 主启动文件
│       └── maps/                     # 地图文件存储
```

### 数据流程

```
[Gazebo障碍物] → [占据栅格地图] → [RRT*路径规划] → [PID路径跟踪] → [机器人运动]
```

## 技术实现

### 1. 地图生成模块 (`spawn_obstacles.py`)

#### 功能描述
- 在Gazebo仿真环境中随机生成障碍物
- 将障碍物信息转换为PGM格式的占据栅格地图
- 生成对应的YAML元数据文件

#### 核心算法
```python
# 障碍物生成参数
MAP_WIDTH = 20.0     # 地图宽度（米）
MAP_HEIGHT = 20.0    # 地图高度（米）
RESOLUTION = 0.1     # 地图分辨率（米/像素）
```

#### 关键特性
- **安全区域保护**：确保机器人起始位置（原点）周围3米范围内无障碍物
- **随机性**：障碍物位置、大小随机生成，保证每次运行的多样性
- **实时同步**：Gazebo中的障碍物与栅格地图实时同步

### 2. RRT*路径规划器 (`planner.py`)

#### 算法原理
RRT*（Rapidly-exploring Random Tree Star）是RRT算法的优化版本，具有渐近最优性：

1. **随机采样**：在配置空间中随机采样点
2. **最近邻搜索**：找到树中距离采样点最近的节点
3. **扩展**：从最近节点向采样点扩展固定步长
4. **碰撞检测**：检查扩展路径是否与障碍物碰撞
5. **父节点选择**：在邻域内选择代价最小的父节点
6. **重连接**：优化邻域内节点的连接，降低路径代价

#### 核心参数
```python
self.max_iter = 2000        # 最大迭代次数
self.step_size = 0.5        # 扩展步长
self.goal_threshold = 0.3   # 目标阈值
self.search_radius = 1.0    # 搜索半径
```

#### 碰撞检测
使用Bresenham直线算法进行高效的路径碰撞检测：
```python
def is_collision(self, p1, p2):
    """使用Bresenham算法检测路径碰撞"""
    # 转换为栅格坐标
    x1, y1 = self.world_to_map(p1)
    x2, y2 = self.world_to_map(p2)
    
    # Bresenham直线算法
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    # ... 算法实现
```

#### 性能优化
- **目标偏向采样**：10%概率直接采样目标点，提高收敛速度
- **动态搜索半径**：根据节点密度调整搜索半径
- **路径平滑**：通过重连接操作减少路径转折点

### 3. PID路径跟踪控制器 (`controller.py`)

#### 控制架构
采用分层控制结构：
- **上层**：路径跟踪控制，计算期望的线速度和角速度
- **下层**：PID控制器，将期望速度转换为电机控制信号

#### PID控制器设计
```python
class PIDController:
    def __init__(self, kp=0.0, ki=0.0, kd=0.0, integral_limit=1.0):
        self.kp = kp                    # 比例增益
        self.ki = ki                    # 积分增益  
        self.kd = kd                    # 微分增益
        self.integral_limit = integral_limit  # 积分限幅
```

#### 控制策略
1. **前瞻控制**：使用前瞻距离选择目标点，提高跟踪精度
2. **速度平滑**：使用滑动平均滤波器平滑速度指令
3. **自适应减速**：根据目标距离动态调整速度

#### 参数调优
```python
# 线速度PID参数
self.linear_pid = PIDController(kp=1.0, ki=0.1, kd=0.05)

# 角速度PID参数  
self.angular_pid = PIDController(kp=2.0, ki=0.5, kd=0.1)
```

## 📚 操作指南

### 📖 详细文档
- **[快速操作指南.md](快速操作指南.md)** - 3分钟快速上手
- **[操作说明书.md](操作说明书.md)** - 完整详细操作手册

### 🎯 三步快速使用
1. **启动** → `./start_system.sh`
2. **控制** → RViz中点击绿色箭头工具，在白色区域设置目标
3. **观察** → 看路径规划过程和机器人运动

## 使用方法

### 1. 环境配置

#### 依赖包安装
```bash
# ROS依赖
sudo apt-get install ros-noetic-turtlebot3-*
sudo apt-get install ros-noetic-map-server
sudo apt-get install ros-noetic-navigation

# Python依赖
pip install numpy matplotlib pillow pyyaml
```

#### 环境变量设置
```bash
export TURTLEBOT3_MODEL=burger
export GAZEBO_MODEL_PATH=$GAZEBO_MODEL_PATH:~/path/to/your/models
```

### 2. 编译与运行

#### 编译工作空间
```bash
cd ~/机器人导论/final_project
catkin_make
source devel/setup.bash
```

#### 启动系统
```bash
# 启动完整系统（包含Gazebo、地图生成、路径规划、控制器）
roslaunch Robot-Planner obs_world.launch
```

#### 系统启动流程
1. **Gazebo仿真环境**启动
2. **TurtleBot3机器人**在原点生成
3. **随机障碍物**生成（3秒延迟）
4. **地图服务器**加载生成的栅格地图（10秒延迟）
5. **RRT*路径规划器**初始化
6. **PID控制器**准备就绪
7. **RViz可视化**界面启动

### 3. 操作步骤

1. **等待系统初始化**：观察终端输出，确保所有节点正常启动
2. **设置目标点**：在RViz中使用"2D Nav Goal"工具点击目标位置
3. **观察路径规划**：绿色线条显示RRT*生成的搜索树，红色路径显示最优路径
4. **观察路径跟踪**：机器人按照规划路径移动到目标点

## 评估指标

### 1. 路径规划时间（15分）
- **测量方法**：记录从接收目标点到生成完整路径的时间
- **优化策略**：
  - 限制最大迭代次数
  - 使用高效的碰撞检测算法
  - 优化数据结构和搜索算法

### 2. 路径长度（15分）
- **测量方法**：计算规划路径的总长度
- **优化策略**：
  - RRT*算法的重连接优化
  - 路径平滑后处理
  - 多次规划取最优解

### 3. 轨迹跟踪精度（15分）
- **测量方法**：计算机器人实际轨迹与规划路径的偏差
- **优化策略**：
  - PID参数调优
  - 前瞻控制算法
  - 自适应速度控制

### 4. 速度平滑度（15分）
- **测量方法**：分析速度指令的变化率和连续性
- **优化策略**：
  - 速度滤波器
  - 加速度限制
  - 渐进式速度调整

## 性能优化

### 1. 路径规划优化
```python
# 采样策略优化
if random.random() < 0.1:  # 10%概率采样目标点
    rand_point = Point(self.goal.x, self.goal.y, 0)
else:
    # 在地图范围内随机采样
    rand_point = self.sample_random_point()
```

### 2. 控制器优化
```python
# 前瞻控制
def get_target_point(self):
    """使用前瞻距离选择目标点"""
    for i in range(self.current_target_idx, self.num_of_points):
        distance = calc_distance(self.current_pos, self.path[i])
        if distance >= self.lookahead_distance:
            return self.path[i]
    return self.path[-1]
```

### 3. 速度平滑
```python
def smooth_velocity(self, linear_vel, angular_vel):
    """使用滑动平均滤波器平滑速度"""
    self.linear_velocity_filter.append(linear_vel)
    if len(self.linear_velocity_filter) > self.filter_size:
        self.linear_velocity_filter.pop(0)
    return sum(self.linear_velocity_filter) / len(self.linear_velocity_filter)
```

## 调试与故障排除

### 常见问题

1. **编译错误**
```bash
# 清理并重新编译
rm -rf build devel
catkin_make
```

2. **地图加载失败**
```bash
# 检查地图文件是否生成
ls -la src/Robot-Planner/maps/
```

3. **路径规划失败**
```bash
# 检查目标点是否在地图范围内
# 调整RRT*参数
```

4. **控制器无响应**
```bash
# 检查话题连接
rostopic list
rostopic echo /path
```

### 日志监控
```bash
# 查看节点状态
rosnode list
rosnode info /rrt_star_planner

# 监控话题
rostopic hz /cmd_vel
rostopic echo /odom
```

## 技术细节

### 坐标系统
- **世界坐标系**：Gazebo仿真环境坐标系，原点为机器人起始位置
- **地图坐标系**：占据栅格地图坐标系，与世界坐标系对齐
- **机器人坐标系**：以机器人为中心的局部坐标系

### 数据格式
- **路径数据**：Float32MultiArray，格式为[x1, y1, x2, y2, ...]
- **地图数据**：OccupancyGrid，值范围0-100，表示占据概率
- **控制指令**：Twist，包含线速度和角速度

### 通信机制
```python
# 发布者
self.vis_path_pub = rospy.Publisher('/rrt_path', Path, queue_size=10)
self.ctrl_path_pub = rospy.Publisher('/path', Float32MultiArray, queue_size=10)
self.cmd_vel_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

# 订阅者
rospy.Subscriber('/move_base_simple/goal', PoseStamped, self.goal_callback)
rospy.Subscriber('/odom', Odometry, self.odom_callback)
rospy.Subscriber('/map', OccupancyGrid, self.map_callback)
```

## 扩展功能

### 1. 多目标点规划
支持连续多个目标点的路径规划和跟踪

### 2. 动态避障
实时检测动态障碍物并重新规划路径

### 3. 路径平滑
使用贝塞尔曲线或样条插值平滑路径

### 4. 自适应参数
根据环境复杂度自动调整算法参数

## 参考文献

1. Karaman, S., & Frazzoli, E. (2011). Sampling-based algorithms for optimal motion planning. The international journal of robotics research, 30(7), 846-894.

2. LaValle, S. M. (1998). Rapidly-exploring random trees: A new tool for path planning. Computer Science Department, Iowa State University.

3. Siegwart, R., Nourbakhsh, I. R., & Scaramuzza, D. (2011). Introduction to autonomous mobile robots. MIT press.

## 许可证

本项目采用MIT许可证，详见LICENSE文件。

## 联系方式

如有问题或建议，请联系项目维护者。 