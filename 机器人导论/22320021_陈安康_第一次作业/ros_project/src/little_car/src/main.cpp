#include <ros/ros.h>
#include "parser.h"

int main(int argc, char **argv) {
  ros::init(argc, argv, "little_car");
  ros::NodeHandle nh;
  little_car car;
  car.joint_pub = nh.advertise<sensor_msgs::JointState>("joint_states", 1);
  car.posSub = nh.subscribe("/gazebo/model_states", 1000, &little_car::posCallBack, &car);
  ros::Rate rate(100); // 控制频率 100Hz
  while (ros::ok()) {
    car.update_();	
    rate.sleep(); // 控制频率
    ros::spinOnce(); // 处理回调函数
  }

  return 0;
}
