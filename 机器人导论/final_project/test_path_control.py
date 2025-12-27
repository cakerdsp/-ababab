#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist
import time

def test_path_publishing():
    """
    测试路径发布和控制器响应
    """
    rospy.init_node('path_test_node', anonymous=True)
    
    # 创建发布器
    path_pub = rospy.Publisher('/path', Float32MultiArray, queue_size=10)
    
    # 等待发布器连接
    rospy.sleep(2.0)
    
    # 创建简单的测试路径
    test_path = Float32MultiArray()
    
    # 简单的直线路径: 从(0,0)到(2,0)到(2,2)
    path_points = [
        (0.0, 0.0),
        (0.5, 0.0),
        (1.0, 0.0),
        (1.5, 0.0),
        (2.0, 0.0),
        (2.0, 0.5),
        (2.0, 1.0),
        (2.0, 1.5),
        (2.0, 2.0)
    ]
    
    # 填充路径数据
    for point in path_points:
        test_path.data.extend([point[0], point[1]])
    
    rospy.loginfo("发布测试路径，包含 %d 个点" % len(path_points))
    rospy.loginfo("路径: %s" % str(path_points))
    
    # 发布路径
    path_pub.publish(test_path)
    
    rospy.loginfo("路径已发布，监听控制器响应...")
    
    # 订阅cmd_vel来验证控制器是否响应
    def cmd_vel_callback(data):
        rospy.loginfo("检测到控制命令: 线速度=%.3f, 角速度=%.3f" % 
                     (data.linear.x, data.angular.z))
    
    cmd_vel_sub = rospy.Subscriber('/cmd_vel', Twist, cmd_vel_callback)
    
    # 保持运行一段时间
    rospy.sleep(10.0)
    
    rospy.loginfo("测试完成")

if __name__ == '__main__':
    try:
        test_path_publishing()
    except rospy.ROSInterruptException:
        pass 