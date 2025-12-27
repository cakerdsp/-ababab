#ifndef __PARSER_H
#define __PARSER_H
#include "parser.h"
#include <urdf/model.h>
#include <string>
#include <sensor_msgs/JointState.h>
#include <gazebo_msgs/ModelStates.h>
#include <tf/transform_broadcaster.h>
#include <geometry_msgs/Point.h>
#include <ros/ros.h>
#include <random>

typedef struct
{
	float x = 0.0;
	float y = 0.0;
	float z = 0.0;
}SVector3;
class little_car
{
	private:
		tf::TransformBroadcaster broadcaster;//坐标变换广播
		sensor_msgs::JointState joint_state;
		geometry_msgs::TransformStamped odom_trans;
 		std::string car_name = "little_car";  
		geometry_msgs::Pose car_pose;
		void update_position(); //更新位置
	public:
		ros::Publisher joint_pub;
		ros::Subscriber posSub;
		little_car();			//构造函数
		void update_();			//小车状态更新
		void posCallBack(const gazebo_msgs::ModelStates::ConstPtr& msg);
};

#endif
