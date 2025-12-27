#!/bin/bash

# 2D栅格地图机器人路径规划与跟踪系统启动脚本
# 作者: [您的姓名]
# 日期: $(date +%Y-%m-%d)

echo "========================================"
echo "2D栅格地图机器人路径规划与跟踪系统"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查ROS环境
check_ros_environment() {
    echo -e "${BLUE}[1/6] 检查ROS环境...${NC}"
    
    if [ -z "$ROS_DISTRO" ]; then
        echo -e "${RED}错误: ROS环境未设置${NC}"
        echo "请运行: source /opt/ros/noetic/setup.bash"
        exit 1
    fi
    
    echo -e "${GREEN}✓ ROS $ROS_DISTRO 环境已配置${NC}"
    
    # 检查TurtleBot3模型
    if [ -z "$TURTLEBOT3_MODEL" ]; then
        echo -e "${YELLOW}⚠ 设置TurtleBot3模型为burger${NC}"
        export TURTLEBOT3_MODEL=burger
    fi
    
    echo -e "${GREEN}✓ TurtleBot3模型: $TURTLEBOT3_MODEL${NC}"
}

# 编译工作空间
compile_workspace() {
    echo -e "${BLUE}[2/6] 编译工作空间...${NC}"
    
    # 保存当前目录
    CURRENT_DIR=$(pwd)
    
    # 切换到工作空间根目录
    WORKSPACE_DIR="/home/cake/机器人导论/final_project"
    cd "$WORKSPACE_DIR"
    
    # 编译
    if catkin_make; then
        echo -e "${GREEN}✓ 编译成功${NC}"
    else
        echo -e "${RED}✗ 编译失败${NC}"
        cd "$CURRENT_DIR"
        exit 1
    fi
    
    # 设置环境
    source devel/setup.bash
    echo -e "${GREEN}✓ 环境变量已设置${NC}"
    
    # 返回原目录
    cd "$CURRENT_DIR"
}

# 创建必要目录
create_directories() {
    echo -e "${BLUE}[3/6] 创建必要目录...${NC}"
    
    # 创建地图目录
    mkdir -p src/Robot-Planner/maps
    echo -e "${GREEN}✓ 地图目录已创建${NC}"
    
    # 创建日志目录
    mkdir -p logs
    echo -e "${GREEN}✓ 日志目录已创建${NC}"
}

# 启动系统
start_system() {
    echo -e "${BLUE}[4/6] 启动系统...${NC}"
    
    # 检查roscore
    if ! pgrep -x "roscore" > /dev/null; then
        echo -e "${YELLOW}启动roscore...${NC}"
        roscore &
        sleep 3
    else
        echo -e "${GREEN}✓ roscore已运行${NC}"
    fi
    
    # 启动主系统
    echo -e "${YELLOW}启动主系统（这可能需要几分钟）...${NC}"
    echo -e "${YELLOW}Gazebo、地图生成、路径规划器等将依次启动${NC}"
    
    # 启动launch文件
    roslaunch turtle obs_world.launch &
    LAUNCH_PID=$!
    
    echo -e "${GREEN}✓ 系统已启动，PID: $LAUNCH_PID${NC}"
    echo -e "${GREEN}✓ 查看Gazebo和RViz窗口${NC}"
}

# 等待系统初始化
wait_for_initialization() {
    echo -e "${BLUE}[5/6] 等待系统初始化...${NC}"
    
    echo -e "${YELLOW}正在等待各个组件启动...${NC}"
    echo "- Gazebo仿真环境"
    echo "- 随机障碍物生成 (3秒后)"
    echo "- 地图服务器 (10秒后)"
    echo "- RRT*路径规划器"
    echo "- PID控制器"
    echo "- RViz可视化"
    
    # 进度条
    for i in {1..15}; do
        echo -n "."
        sleep 1
    done
    echo
    
    echo -e "${GREEN}✓ 系统初始化完成${NC}"
}

# 显示使用说明
show_instructions() {
    echo -e "${BLUE}[6/6] 使用说明${NC}"
    echo "========================================"
    echo -e "${GREEN}系统已启动！${NC}"
    echo
    echo -e "${YELLOW}如何使用:${NC}"
    echo "1. 等待Gazebo和RViz窗口完全加载"
    echo "2. 在RViz中，使用 '2D Nav Goal' 工具设置目标点"
    echo "3. 观察机器人自动规划路径并移动到目标"
    echo
    echo -e "${YELLOW}可视化内容:${NC}"
    echo "- 绿色线条: RRT*搜索树"
    echo "- 红色路径: 规划的最优路径"
    echo "- 机器人轨迹: 实际运动路径"
    echo
    echo -e "${YELLOW}评估指标:${NC}"
    echo "- 路径规划时间: 查看终端日志"
    echo "- 路径长度: 在RViz中显示"
    echo "- 跟踪精度: 观察实际轨迹与规划路径的偏差"
    echo "- 速度平滑度: 观察机器人运动的平稳性"
    echo
    echo -e "${YELLOW}停止系统:${NC}"
    echo "按 Ctrl+C 停止系统，或运行: ./stop_system.sh"
    echo "========================================"
}

# 主函数
main() {
    echo "开始启动系统..."
    echo
    
    check_ros_environment
    compile_workspace
    create_directories
    start_system
    wait_for_initialization
    show_instructions
    
    echo
    echo -e "${GREEN}🎉 系统启动完成！${NC}"
    echo -e "${BLUE}按 Ctrl+C 退出此脚本（系统将继续运行）${NC}"
    
    # 保持脚本运行，直到用户中断
    trap 'echo -e "\n${YELLOW}退出启动脚本...${NC}"; exit 0' INT
    while true; do
        sleep 1
    done
}

# 检查参数
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  --test         运行系统测试"
    echo
    echo "描述:"
    echo "  启动2D栅格地图机器人路径规划与跟踪系统"
    echo
    exit 0
fi

if [ "$1" = "--test" ]; then
    echo "运行系统测试..."
    python3 test_system.py
    exit 0
fi

# 运行主程序
main 