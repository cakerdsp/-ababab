#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import subprocess
import time
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist, PoseStamped
from nav_msgs.msg import Odometry
from nav_msgs.msg import Path

class SystemDiagnostic:
    def __init__(self):
        rospy.init_node('system_diagnostic', anonymous=True)
        self.odom_received = False
        self.cmd_vel_received = False
        self.path_received = False
        self.rrt_path_received = False
        
        # 订阅话题
        self.odom_sub = rospy.Subscriber('/odom', Odometry, self.odom_callback)
        self.cmd_vel_sub = rospy.Subscriber('/cmd_vel', Twist, self.cmd_vel_callback)
        self.path_sub = rospy.Subscriber('/path', Float32MultiArray, self.path_callback)
        self.rrt_path_sub = rospy.Subscriber('/rrt_path', Path, self.rrt_path_callback)
        
        self.current_pos = None
        self.current_vel = None
        
    def odom_callback(self, data):
        self.odom_received = True
        self.current_pos = (data.pose.pose.position.x, data.pose.pose.position.y)
        
    def cmd_vel_callback(self, data):
        self.cmd_vel_received = True
        self.current_vel = (data.linear.x, data.angular.z)
        
    def path_callback(self, data):
        self.path_received = True
        rospy.loginfo("收到控制路径，包含 %d 个数据点" % (len(data.data)//2))
        
    def rrt_path_callback(self, data):
        self.rrt_path_received = True
        rospy.loginfo("收到可视化路径，包含 %d 个位姿" % len(data.poses))
        
    def check_topics(self):
        """检查话题状态"""
        print("\n=== 话题状态检查 ===")
        
        try:
            # 检查话题列表
            result = subprocess.run(['rostopic', 'list'], 
                                  capture_output=True, text=True, timeout=5)
            topics = result.stdout.strip().split('\n')
            
            required_topics = ['/odom', '/cmd_vel', '/path', '/rrt_path', '/move_base_simple/goal']
            
            for topic in required_topics:
                if topic in topics:
                    print(f"✓ {topic} - 存在")
                else:
                    print(f"✗ {topic} - 缺失")
                    
        except Exception as e:
            print(f"检查话题时出错: {e}")
            
    def check_nodes(self):
        """检查节点状态"""
        print("\n=== 节点状态检查 ===")
        
        try:
            result = subprocess.run(['rosnode', 'list'], 
                                  capture_output=True, text=True, timeout=5)
            nodes = result.stdout.strip().split('\n')
            
            required_nodes = ['planner', 'controller', 'gazebo', 'map_server']
            
            for node_name in required_nodes:
                found = False
                for node in nodes:
                    if node_name in node:
                        print(f"✓ {node_name} - 运行中 ({node})")
                        found = True
                        break
                if not found:
                    print(f"✗ {node_name} - 未运行")
                    
        except Exception as e:
            print(f"检查节点时出错: {e}")
            
    def check_message_flow(self):
        """检查消息流"""
        print("\n=== 消息流检查 ===")
        print("等待消息...")
        
        start_time = time.time()
        while time.time() - start_time < 5.0:
            rospy.sleep(0.1)
            
        print(f"Odom消息: {'✓ 接收到' if self.odom_received else '✗ 未接收到'}")
        print(f"Cmd_vel消息: {'✓ 接收到' if self.cmd_vel_received else '✗ 未接收到'}")
        print(f"Path消息: {'✓ 接收到' if self.path_received else '✗ 未接收到'}")
        print(f"RRT Path消息: {'✓ 接收到' if self.rrt_path_received else '✗ 未接收到'}")
        
        if self.current_pos:
            print(f"当前位置: ({self.current_pos[0]:.3f}, {self.current_pos[1]:.3f})")
            
        if self.current_vel:
            print(f"当前速度: 线速度={self.current_vel[0]:.3f}, 角速度={self.current_vel[1]:.3f}")
            
    def test_goal_publishing(self):
        """测试目标点发布"""
        print("\n=== 测试目标点发布 ===")
        
        goal_pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=1)
        rospy.sleep(1.0)
        
        # 发布一个测试目标点
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = rospy.Time.now()
        goal.pose.position.x = 2.0
        goal.pose.position.y = 2.0
        goal.pose.orientation.w = 1.0
        
        print("发布测试目标点: (2.0, 2.0)")
        goal_pub.publish(goal)
        
        # 等待响应
        start_time = time.time()
        path_before = self.path_received
        
        while time.time() - start_time < 3.0:
            rospy.sleep(0.1)
            if self.path_received and not path_before:
                print("✓ 路径规划器响应正常")
                return
                
        print("✗ 路径规划器无响应")
        
    def run_diagnostic(self):
        """运行完整诊断"""
        print("=" * 50)
        print("机器人路径规划系统诊断")
        print("=" * 50)
        
        self.check_topics()
        self.check_nodes()
        self.check_message_flow()
        self.test_goal_publishing()
        
        print("\n=== 诊断完成 ===")
        print("如果发现问题，请检查相应的节点或重启系统")

if __name__ == '__main__':
    try:
        diagnostic = SystemDiagnostic()
        diagnostic.run_diagnostic()
    except rospy.ROSInterruptException:
        pass 