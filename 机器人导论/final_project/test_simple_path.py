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
    rospy.loginfo("当前机器人位置: (%.3f, %.3f)" % (current_pos[0], current_pos[1]))

def test_simple_path():
    """
    发布一个简单的测试路径
    """
    rospy.init_node('simple_path_test', anonymous=True)
    
    # 订阅odom获取当前位置
    odom_sub = rospy.Subscriber('/odom', Odometry, odom_callback)
    
    # 等待获取当前位置
    rospy.loginfo("等待获取机器人当前位置...")
    while current_pos is None:
        rospy.sleep(0.1)
    
    rospy.loginfo("机器人当前位置: (%.3f, %.3f)" % (current_pos[0], current_pos[1]))
    
    # 创建发布器
    path_pub = rospy.Publisher('/path', Float32MultiArray, queue_size=10)
    
    # 等待发布器连接
    rospy.sleep(2.0)
    
    # 创建简单的测试路径：向前移动1米
    test_path = Float32MultiArray()
    
    # 从当前位置向右移动1米
    target_x = current_pos[0] + 1.0
    target_y = current_pos[1]
    
    path_points = [
        current_pos,  # 起点
        (current_pos[0] + 0.3, current_pos[1]),  # 中间点1
        (current_pos[0] + 0.7, current_pos[1]),  # 中间点2
        (target_x, target_y)  # 终点
    ]
    
    # 填充路径数据
    for point in path_points:
        test_path.data.extend([point[0], point[1]])
    
    rospy.loginfo("发布简单测试路径，包含 %d 个点" % len(path_points))
    rospy.loginfo("从 (%.3f, %.3f) 到 (%.3f, %.3f)" % 
                 (current_pos[0], current_pos[1], target_x, target_y))
    
    # 发布路径
    path_pub.publish(test_path)
    
    rospy.loginfo("路径已发布，观察机器人运动...")
    
    # 保持运行
    rospy.sleep(15.0)

if __name__ == '__main__':
    try:
        test_simple_path()
    except rospy.ROSInterruptException:
        pass 