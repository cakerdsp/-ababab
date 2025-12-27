#!/bin/bash

# 2D栅格地图机器人路径规划与跟踪系统停止脚本

echo "========================================"
echo "停止机器人路径规划与跟踪系统"
echo "========================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 停止特定节点
stop_nodes() {
    echo -e "${BLUE}正在停止ROS节点...${NC}"
    
    # 要停止的节点列表
    nodes_to_stop=(
        "/rrt_star_planner"
        "/path_tracking_controller"
        "/spawn_obstacles_node"
        "/map_server"
        "/robot_state_publisher"
        "/gazebo"
    )
    
    for node in "${nodes_to_stop[@]}"; do
        if rosnode list 2>/dev/null | grep -q "$node"; then
            echo -e "${YELLOW}停止节点: $node${NC}"
            rosnode kill "$node" 2>/dev/null
        else
            echo -e "${GREEN}节点 $node 未运行${NC}"
        fi
    done
}

# 停止Gazebo进程
stop_gazebo() {
    echo -e "${BLUE}停止Gazebo进程...${NC}"
    
    # 停止gazebo客户端
    pkill -f "gazebo" 2>/dev/null
    pkill -f "gzclient" 2>/dev/null
    pkill -f "gzserver" 2>/dev/null
    
    # 等待进程完全停止
    sleep 2
    
    # 强制杀死剩余进程
    pkill -9 -f "gazebo" 2>/dev/null
    pkill -9 -f "gzclient" 2>/dev/null  
    pkill -9 -f "gzserver" 2>/dev/null
    
    echo -e "${GREEN}✓ Gazebo进程已停止${NC}"
}

# 停止RViz
stop_rviz() {
    echo -e "${BLUE}停止RViz...${NC}"
    pkill -f "rviz" 2>/dev/null
    echo -e "${GREEN}✓ RViz已停止${NC}"
}

# 清理ROS环境
cleanup_ros() {
    echo -e "${BLUE}清理ROS环境...${NC}"
    
    # 停止所有launch进程
    pkill -f "roslaunch" 2>/dev/null
    
    # 停止roscore（可选，注释掉以保持roscore运行）
    # pkill -f "roscore" 2>/dev/null
    # pkill -f "rosmaster" 2>/dev/null
    
    # 清理参数服务器中的参数
    rosparam delete /pgm_path 2>/dev/null
    rosparam delete /yaml_path 2>/dev/null
    rosparam delete /obstacle_count 2>/dev/null
    rosparam delete /x_range 2>/dev/null
    rosparam delete /y_range 2>/dev/null
    
    echo -e "${GREEN}✓ ROS环境已清理${NC}"
}

# 显示剩余进程
show_remaining_processes() {
    echo -e "${BLUE}检查剩余进程...${NC}"
    
    remaining_gazebo=$(pgrep -f "gazebo" | wc -l)
    remaining_rviz=$(pgrep -f "rviz" | wc -l)
    remaining_python=$(pgrep -f "planner.py\|controller.py\|spawn_obstacles.py" | wc -l)
    
    if [ "$remaining_gazebo" -gt 0 ]; then
        echo -e "${YELLOW}⚠ 仍有 $remaining_gazebo 个Gazebo进程运行${NC}"
    fi
    
    if [ "$remaining_rviz" -gt 0 ]; then
        echo -e "${YELLOW}⚠ 仍有 $remaining_rviz 个RViz进程运行${NC}"
    fi
    
    if [ "$remaining_python" -gt 0 ]; then
        echo -e "${YELLOW}⚠ 仍有 $remaining_python 个Python脚本运行${NC}"
    fi
    
    if [ "$remaining_gazebo" -eq 0 ] && [ "$remaining_rviz" -eq 0 ] && [ "$remaining_python" -eq 0 ]; then
        echo -e "${GREEN}✓ 所有相关进程已停止${NC}"
    fi
}

# 主函数
main() {
    echo "开始停止系统..."
    echo
    
    # 检查是否有ROS节点在运行
    if ! command -v rosnode &> /dev/null; then
        echo -e "${YELLOW}ROS命令不可用，直接停止进程${NC}"
    else
        if ! rosnode list &> /dev/null; then
            echo -e "${YELLOW}无法连接到ROS Master，直接停止进程${NC}"
        else
            stop_nodes
        fi
    fi
    
    stop_gazebo
    stop_rviz
    cleanup_ros
    
    echo
    show_remaining_processes
    
    echo
    echo -e "${GREEN}🎉 系统停止完成！${NC}"
}

# 检查参数
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  --force        强制停止所有相关进程"
    echo
    echo "描述:"
    echo "  安全停止2D栅格地图机器人路径规划与跟踪系统"
    echo
    exit 0
fi

if [ "$1" = "--force" ]; then
    echo -e "${RED}强制停止模式${NC}"
    
    # 强制杀死所有相关进程
    pkill -9 -f "gazebo"
    pkill -9 -f "rviz"
    pkill -9 -f "roslaunch"
    pkill -9 -f "planner.py"
    pkill -9 -f "controller.py"
    pkill -9 -f "spawn_obstacles.py"
    
    echo -e "${GREEN}✓ 所有进程已强制停止${NC}"
    exit 0
fi

# 运行主程序
main 