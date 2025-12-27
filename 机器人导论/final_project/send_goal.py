#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry

current_pos = None

def odom_callback(data):
    global current_pos
    current_pos = (data.pose.pose.position.x, data.pose.pose.position.y)

def send_goal():
    """
    发送目标点来测试修复的控制器
    """
    rospy.init_node('goal_sender', anonymous=True)
    
    # 订阅odom获取当前位置
    odom_sub = rospy.Subscriber('/odom', Odometry, odom_callback)
    
    # 创建目标点发布器
    goal_pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=1)
    
    # 等待获取当前位置
    rospy.loginfo("等待获取机器人当前位置...")
    while current_pos is None and not rospy.is_shutdown():
        rospy.sleep(0.1)
    
    if current_pos is None:
        rospy.logerr("无法获取机器人位置")
        return
        
    rospy.loginfo("机器人当前位置: (%.3f, %.3f)" % (current_pos[0], current_pos[1]))
    
    # 等待发布器连接
    rospy.sleep(2.0)
    
    # 创建目标点
    goal = PoseStamped()
    goal.header.frame_id = "map"
    goal.header.stamp = rospy.Time.now()
    
    # 设置目标点为当前位置右侧2米
    goal.pose.position.x = current_pos[0] + 2.0
    goal.pose.position.y = current_pos[1]
    goal.pose.position.z = 0.0
    
    # 设置朝向
    goal.pose.orientation.x = 0.0
    goal.pose.orientation.y = 0.0
    goal.pose.orientation.z = 0.0
    goal.pose.orientation.w = 1.0
    
    rospy.loginfo("发送目标点: (%.2f, %.2f)" % (goal.pose.position.x, goal.pose.position.y))
    
    # 发布目标点
    goal_pub.publish(goal)
    
    rospy.loginfo("目标点已发送，检查控制器是否正确响应...")
    rospy.loginfo("观察终端输出，查看'目标[X]'是否正确显示")
    
    # 保持运行
    rospy.spin()

if __name__ == '__main__':
    try:
        send_goal()
    except rospy.ROSInterruptException:
        pass 