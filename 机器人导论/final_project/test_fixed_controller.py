#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import Float32MultiArray
from nav_msgs.msg import Odometry
import time

current_pos = None

def odom_callback(data):
    global current_pos
    current_pos = (data.pose.pose.position.x, data.pose.pose.position.y)

def test_fixed_controller():
    """
    测试修复后的控制器
    """
    rospy.init_node('test_fixed_controller', anonymous=True)
    
    # 订阅odom获取当前位置
    odom_sub = rospy.Subscriber('/odom', Odometry, odom_callback)
    
    # 等待获取当前位置
    rospy.loginfo("等待获取机器人当前位置...")
    while current_pos is None and not rospy.is_shutdown():
        rospy.sleep(0.1)
    
    if current_pos is None:
        rospy.logerr("无法获取机器人位置")
        return
        
    rospy.loginfo("机器人当前位置: (%.3f, %.3f)" % (current_pos[0], current_pos[1]))
    
    # 创建发布器
    path_pub = rospy.Publisher('/path', Float32MultiArray, queue_size=10)
    
    # 等待发布器连接
    rospy.sleep(2.0)
    
    # 创建简单的直线路径进行测试
    test_path = Float32MultiArray()
    
    # 简单的正方形路径
    start_x, start_y = current_pos
    
    path_points = [
        (start_x, start_y),                    # 起点
        (start_x + 0.5, start_y),             # 右移0.5米
        (start_x + 1.0, start_y),             # 右移1.0米
        (start_x + 1.0, start_y + 0.5),       # 上移0.5米
        (start_x + 1.0, start_y + 1.0),       # 上移1.0米
        (start_x + 0.5, start_y + 1.0),       # 左移0.5米
        (start_x, start_y + 1.0),             # 回到左边
        (start_x, start_y + 0.5),             # 下移0.5米
        (start_x, start_y)                    # 回到起点
    ]
    
    # 填充路径数据
    for point in path_points:
        test_path.data.extend([point[0], point[1]])
    
    rospy.loginfo("发布正方形测试路径，包含 %d 个点" % len(path_points))
    rospy.loginfo("路径: 从 (%.2f, %.2f) 开始的1x1米正方形" % (start_x, start_y))
    
    # 发布路径
    path_pub.publish(test_path)
    
    rospy.loginfo("路径已发布，观察机器人是否能正确跟踪每个路径点...")
    rospy.loginfo("检查终端输出中的'目标[X]'是否正确显示各个坐标点")
    rospy.loginfo("预期机器人应该走一个正方形路径")
    
    # 保持运行
    rospy.sleep(30.0)  # 运行30秒观察

if __name__ == '__main__':
    try:
        test_fixed_controller()
    except rospy.ROSInterruptException:
        pass 