#!/usr/bin/env python3
"""
测试当前位置路径规划
验证RRT规划器是否从机器人当前位置开始规划而不是总是从(0,0)
"""
import rospy
import time
from geometry_msgs.msg import PoseStamped, Point
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray

class PlanningTester:
    def __init__(self):
        rospy.init_node('planning_tester', anonymous=True)
        
        self.current_position = None
        self.path_received = False
        self.last_path_start = None
        
        # 订阅机器人位置和路径
        rospy.Subscriber('/odom', Odometry, self.odom_callback)
        rospy.Subscriber('/path', Float32MultiArray, self.path_callback)
        
        # 目标点发布器
        self.goal_pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=10)
        
        rospy.loginfo("路径规划测试器已启动")
        
    def odom_callback(self, msg):
        """更新机器人当前位置"""
        self.current_position = msg.pose.pose.position
        
    def path_callback(self, msg):
        """接收路径数据并分析起点"""
        if len(msg.data) >= 2:
            start_x = msg.data[0]
            start_y = msg.data[1]
            self.last_path_start = (start_x, start_y)
            self.path_received = True
            rospy.loginfo(f"接收到路径，起点: ({start_x:.3f}, {start_y:.3f})")
            
    def send_goal(self, x, y):
        """发送目标点"""
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = rospy.Time.now()
        goal.pose.position.x = x
        goal.pose.position.y = y
        goal.pose.position.z = 0
        goal.pose.orientation.w = 1.0
        
        self.goal_pub.publish(goal)
        rospy.loginfo(f"发送目标点: ({x}, {y})")
        
    def test_planning_from_current_position(self):
        """测试是否从当前位置开始规划"""
        rospy.loginfo("等待机器人位置信息...")
        while self.current_position is None and not rospy.is_shutdown():
            rospy.sleep(0.1)
            
        if self.current_position is None:
            rospy.logwarn("无法获取机器人位置")
            return False
            
        current_x = self.current_position.x
        current_y = self.current_position.y
        rospy.loginfo(f"当前机器人位置: ({current_x:.3f}, {current_y:.3f})")
        
        # 发送目标点
        goal_x, goal_y = 2.0, 2.0
        self.send_goal(goal_x, goal_y)
        
        # 等待路径规划结果
        rospy.loginfo("等待路径规划结果...")
        timeout = rospy.Time.now() + rospy.Duration(10.0)
        self.path_received = False
        
        while not self.path_received and rospy.Time.now() < timeout and not rospy.is_shutdown():
            rospy.sleep(0.1)
            
        if not self.path_received:
            rospy.logwarn("超时：未收到路径规划结果")
            return False
            
        # 检查路径起点是否接近机器人当前位置
        path_start_x, path_start_y = self.last_path_start
        distance_from_current = ((path_start_x - current_x)**2 + (path_start_y - current_y)**2)**0.5
        distance_from_origin = ((path_start_x)**2 + (path_start_y)**2)**0.5
        
        rospy.loginfo(f"路径起点: ({path_start_x:.3f}, {path_start_y:.3f})")
        rospy.loginfo(f"与当前位置的距离: {distance_from_current:.3f}m")
        rospy.loginfo(f"与原点(0,0)的距离: {distance_from_origin:.3f}m")
        
        # 判断测试结果
        if distance_from_current < 0.5:  # 容忍0.5米误差
            rospy.loginfo("✅ 测试通过：路径规划从机器人当前位置开始")
            return True
        elif distance_from_origin < 0.5:
            rospy.logerr("❌ 测试失败：路径规划仍然从原点(0,0)开始")
            return False
        else:
            rospy.logwarn(f"⚠️  测试结果不确定：路径起点既不在当前位置也不在原点附近")
            return False

def main():
    try:
        tester = PlanningTester()
        rospy.sleep(2)  # 等待所有话题连接
        
        # 运行测试
        result = tester.test_planning_from_current_position()
        
        if result:
            rospy.loginfo("🎉 修复成功！RRT规划器现在从机器人当前位置开始规划")
        else:
            rospy.logerr("💥 修复失败！需要进一步调试")
            
    except rospy.ROSInterruptException:
        rospy.loginfo("测试被中断")

if __name__ == '__main__':
    main() 