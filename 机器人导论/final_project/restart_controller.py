#!/usr/bin/env python
# -*- coding: utf-8 -*-

import rospy
import subprocess
import time
import os
import signal

def restart_controller():
    """
    重启控制器节点
    """
    print("重启路径跟踪控制器...")
    
    # 1. 查找并杀死现有的控制器进程
    try:
        result = subprocess.run(['pgrep', '-f', 'controller.py'], 
                              capture_output=True, text=True)
        if result.stdout:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    print(f"停止控制器进程 PID: {pid}")
                    os.kill(int(pid), signal.SIGTERM)
            time.sleep(2)
    except Exception as e:
        print(f"停止进程时出错: {e}")
    
    # 2. 确保工作空间环境正确
    os.chdir('/home/cake/机器人导论/final_project')
    
    # 3. 重新启动控制器
    print("启动新的控制器实例...")
    env = os.environ.copy()
    
    # 设置ROS环境
    env['ROS_PACKAGE_PATH'] = '/home/cake/机器人导论/final_project/src:/opt/ros/noetic/share'
    env['CMAKE_PREFIX_PATH'] = '/home/cake/机器人导论/final_project/devel:/opt/ros/noetic'
    env['PKG_CONFIG_PATH'] = '/home/cake/机器人导论/final_project/devel/lib/pkgconfig:/opt/ros/noetic/lib/pkgconfig'
    
    # 启动控制器
    subprocess.Popen(['python3', 'src/Robot-Planner/scripts/controller.py'], 
                    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    print("控制器已重启")
    print("您现在可以在RViz中设置新的目标点进行测试")

if __name__ == '__main__':
    restart_controller() 