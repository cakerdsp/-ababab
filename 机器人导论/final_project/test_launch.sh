#!/bin/bash

echo "测试launch文件..."

# 设置环境
export TURTLEBOT3_MODEL=burger
source devel/setup.bash

# 检查包是否能找到
echo "检查包路径："
rospack find turtle

# 检查launch文件是否存在
echo "检查launch文件："
ls -la src/Robot-Planner/launch/obs_world.launch

# 验证launch文件语法
echo "验证launch文件语法："
roslaunch turtle obs_world.launch --test

echo "测试完成" 