#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
机器人路径规划与跟踪系统测试脚本
用于验证系统各个模块是否正常工作
"""

import rospy
import time
import subprocess
import os
from nav_msgs.msg import OccupancyGrid, Path
from geometry_msgs.msg import PoseStamped, Point, Twist
from std_msgs.msg import Float32MultiArray

class SystemTester:
    """
    系统测试类，用于验证各个模块的功能
    """
    def __init__(self):
        rospy.init_node('system_tester', anonymous=True)
        self.test_results = {}
        
        # 订阅各种话题以监控系统状态
        self.map_received = False
        self.path_received = False
        self.rrt_path_received = False
        
        rospy.Subscriber('/map', OccupancyGrid, self.map_callback)
        rospy.Subscriber('/path', Float32MultiArray, self.path_callback)
        rospy.Subscriber('/rrt_path', Path, self.rrt_path_callback)
        
        # 发布者
        self.goal_pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=1)
        
    def map_callback(self, msg):
        """地图回调函数"""
        self.map_received = True
        rospy.loginfo("✓ 地图数据接收成功")
        
    def path_callback(self, msg):
        """路径回调函数"""
        self.path_received = True
        path_length = len(msg.data) / 2
        rospy.loginfo("✓ 控制路径接收成功，包含 %d 个点" % path_length)
        
    def rrt_path_callback(self, msg):
        """RRT路径回调函数"""
        self.rrt_path_received = True
        rospy.loginfo("✓ RRT路径接收成功，包含 %d 个点" % len(msg.poses))
        
    def test_ros_environment(self):
        """测试ROS环境"""
        rospy.loginfo("=" * 50)
        rospy.loginfo("测试 1: ROS环境检查")
        rospy.loginfo("=" * 50)
        
        try:
            # 检查ROS_MASTER_URI
            ros_master = os.environ.get('ROS_MASTER_URI', None)
            if ros_master:
                rospy.loginfo("✓ ROS_MASTER_URI: %s" % ros_master)
                self.test_results['ros_master'] = True
            else:
                rospy.logerr("✗ ROS_MASTER_URI 未设置")
                self.test_results['ros_master'] = False
                
            # 检查roscore
            try:
                subprocess.check_output(['rostopic', 'list'], timeout=5)
                rospy.loginfo("✓ roscore 运行正常")
                self.test_results['roscore'] = True
            except subprocess.CalledProcessError:
                rospy.logerr("✗ roscore 未运行或不可访问")
                self.test_results['roscore'] = False
                
        except Exception as e:
            rospy.logerr("ROS环境测试失败: %s" % str(e))
            self.test_results['ros_environment'] = False
            return False
            
        return True
        
    def test_node_status(self):
        """测试节点状态"""
        rospy.loginfo("=" * 50)
        rospy.loginfo("测试 2: 节点状态检查")
        rospy.loginfo("=" * 50)
        
        expected_nodes = [
            '/gazebo',
            '/robot_state_publisher',
            '/map_server',
            '/spawn_obstacles_node'
        ]
        
        try:
            # 获取当前运行的节点
            output = subprocess.check_output(['rosnode', 'list'], timeout=10)
            running_nodes = output.decode('utf-8').strip().split('\n')
            
            for node in expected_nodes:
                if node in running_nodes:
                    rospy.loginfo("✓ 节点 %s 运行正常" % node)
                    self.test_results[node] = True
                else:
                    rospy.logwarn("⚠ 节点 %s 未运行" % node)
                    self.test_results[node] = False
                    
        except subprocess.CalledProcessError as e:
            rospy.logerr("获取节点列表失败: %s" % str(e))
            return False
            
        return True
        
    def test_topic_status(self):
        """测试话题状态"""
        rospy.loginfo("=" * 50)
        rospy.loginfo("测试 3: 话题状态检查")
        rospy.loginfo("=" * 50)
        
        expected_topics = [
            '/map',
            '/odom',
            '/cmd_vel',
            '/move_base_simple/goal'
        ]
        
        try:
            # 获取当前话题列表
            output = subprocess.check_output(['rostopic', 'list'], timeout=10)
            available_topics = output.decode('utf-8').strip().split('\n')
            
            for topic in expected_topics:
                if topic in available_topics:
                    rospy.loginfo("✓ 话题 %s 可用" % topic)
                    self.test_results[topic] = True
                else:
                    rospy.logwarn("⚠ 话题 %s 不可用" % topic)
                    self.test_results[topic] = False
                    
        except subprocess.CalledProcessError as e:
            rospy.logerr("获取话题列表失败: %s" % str(e))
            return False
            
        return True
        
    def test_map_generation(self):
        """测试地图生成"""
        rospy.loginfo("=" * 50)
        rospy.loginfo("测试 4: 地图生成测试")
        rospy.loginfo("=" * 50)
        
        # 等待地图数据
        rospy.loginfo("等待地图数据...")
        timeout = 30  # 30秒超时
        start_time = time.time()
        
        while not self.map_received and (time.time() - start_time) < timeout:
            rospy.sleep(1)
            
        if self.map_received:
            rospy.loginfo("✓ 地图生成测试通过")
            self.test_results['map_generation'] = True
            return True
        else:
            rospy.logerr("✗ 地图生成测试失败（超时）")
            self.test_results['map_generation'] = False
            return False
            
    def test_path_planning(self):
        """测试路径规划"""
        rospy.loginfo("=" * 50)
        rospy.loginfo("测试 5: 路径规划测试")
        rospy.loginfo("=" * 50)
        
        if not self.map_received:
            rospy.logerr("✗ 无法测试路径规划：地图未加载")
            self.test_results['path_planning'] = False
            return False
            
        # 发送测试目标点
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = rospy.Time.now()
        goal.pose.position.x = 5.0
        goal.pose.position.y = 5.0
        goal.pose.position.z = 0.0
        goal.pose.orientation.w = 1.0
        
        rospy.loginfo("发送测试目标点: (5.0, 5.0)")
        self.goal_pub.publish(goal)
        
        # 等待路径规划结果
        timeout = 30  # 30秒超时
        start_time = time.time()
        
        while not (self.path_received and self.rrt_path_received) and (time.time() - start_time) < timeout:
            rospy.sleep(1)
            
        if self.path_received and self.rrt_path_received:
            rospy.loginfo("✓ 路径规划测试通过")
            self.test_results['path_planning'] = True
            return True
        else:
            rospy.logerr("✗ 路径规划测试失败（超时）")
            self.test_results['path_planning'] = False
            return False
            
    def test_file_generation(self):
        """测试文件生成"""
        rospy.loginfo("=" * 50)
        rospy.loginfo("测试 6: 文件生成检查")
        rospy.loginfo("=" * 50)
        
        # 检查地图文件
        map_files = [
            'src/Robot-Planner/maps/gazebo_map.pgm',
            'src/Robot-Planner/maps/gazebo_map.yaml'
        ]
        
        for file_path in map_files:
            if os.path.exists(file_path):
                rospy.loginfo("✓ 文件存在: %s" % file_path)
                self.test_results[file_path] = True
            else:
                rospy.logwarn("⚠ 文件不存在: %s" % file_path)
                self.test_results[file_path] = False
                
        return True
        
    def generate_test_report(self):
        """生成测试报告"""
        rospy.loginfo("=" * 50)
        rospy.loginfo("测试报告")
        rospy.loginfo("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        rospy.loginfo("总测试项: %d" % total_tests)
        rospy.loginfo("通过测试: %d" % passed_tests)
        rospy.loginfo("失败测试: %d" % (total_tests - passed_tests))
        rospy.loginfo("通过率: %.1f%%" % (passed_tests / total_tests * 100 if total_tests > 0 else 0))
        
        rospy.loginfo("\n详细结果:")
        for test_name, result in self.test_results.items():
            status = "✓ 通过" if result else "✗ 失败"
            rospy.loginfo("  %s: %s" % (test_name, status))
            
        if passed_tests == total_tests:
            rospy.loginfo("\n🎉 所有测试通过！系统运行正常。")
        elif passed_tests > total_tests * 0.8:
            rospy.logwarn("\n⚠ 大部分测试通过，但有少数问题需要解决。")
        else:
            rospy.logerr("\n❌ 多项测试失败，需要检查系统配置。")
            
    def run_all_tests(self):
        """运行所有测试"""
        rospy.loginfo("开始系统测试...")
        
        # 等待系统初始化
        rospy.loginfo("等待系统初始化（10秒）...")
        rospy.sleep(10)
        
        # 运行测试
        self.test_ros_environment()
        self.test_node_status()
        self.test_topic_status()
        self.test_file_generation()
        self.test_map_generation()
        self.test_path_planning()
        
        # 生成报告
        self.generate_test_report()

def main():
    """主函数"""
    try:
        # 检查roscore是否运行
        import subprocess
        try:
            subprocess.check_output(['rostopic', 'list'], timeout=5, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print("错误: ROS Master未运行!")
            print("请先启动系统: ./start_system.sh")
            print("或手动启动: roscore")
            return
        
        tester = SystemTester()
        tester.run_all_tests()
    except rospy.ROSInterruptException:
        rospy.loginfo("测试被中断")
    except Exception as e:
        rospy.logerr("测试过程中发生错误: %s" % str(e))

if __name__ == '__main__':
    main() 