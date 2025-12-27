#!/bin/bash

# 改进的TurtleBot3路径规划系统启动脚本
# 包含地图一致性修复和位置重置功能

echo "======================================"
echo "启动TurtleBot3路径规划系统（修复版）"
echo "======================================"

# 设置TurtleBot3模型
export TURTLEBOT3_MODEL=burger

# 清理之前的运行
echo "清理之前的进程..."
pkill -f "gazebo"
pkill -f "rviz"
pkill -f "roscore"
pkill -f "planner.py"
pkill -f "controller.py"
pkill -f "spawn_obstacles.py"
pkill -f "map_server"
sleep 2

# 清理Gazebo临时文件
echo "清理Gazebo临时文件..."
rm -rf ~/.gazebo/log/*
rm -rf /tmp/.gazebo*

# 删除旧的地图文件以强制重新生成
echo "清理旧地图文件..."
rm -f src/Robot-Planner/maps/gazebo_map.pgm
rm -f src/Robot-Planner/maps/gazebo_map.yaml

# 确保目录存在
mkdir -p src/Robot-Planner/maps

# 设置环境变量
source /opt/ros/noetic/setup.bash
source devel/setup.bash

# 启动roscore
echo "启动ROS核心..."
roscore &
sleep 3

# 启动系统
echo "启动路径规划系统..."
echo "注意：系统将按以下顺序启动："
echo "1. Gazebo世界 (5秒后)"
echo "2. 机器人模型 (2秒后)"
echo "3. 障碍物生成和地图创建 (5秒后)"
echo "4. 地图服务器 (15秒后)"
echo "5. RViz可视化 (18秒后)"
echo "6. 路径规划器 (20秒后)"
echo "7. 控制器 (25秒后)"
echo "8. 位置重置服务 (30秒后)"

roslaunch Robot-Planner obs_world.launch

echo "系统启动完成！"
echo "======================================"
echo "使用说明："
echo "1. 等待所有组件加载完成（约30秒）"
echo "2. 在RViz中使用'2D Nav Goal'工具设置目标点"
echo "3. 观察机器人路径规划和跟踪过程"
echo "4. 地图显示与Gazebo中的障碍物现在应该完全一致"
echo "5. 机器人每次启动都从(0,0)位置开始"
echo "======================================" 