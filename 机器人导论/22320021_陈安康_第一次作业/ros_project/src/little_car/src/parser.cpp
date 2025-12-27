#include "parser.h"
little_car::little_car()
{
}

void little_car::posCallBack(const gazebo_msgs::ModelStates::ConstPtr& msg) {
	// 遍历模型列表
    for (int i = 0; i < msg->name.size(); i++)
    {
        if (msg->name[i] == car_name)
        {
            // 获取模型的位置和姿态
            geometry_msgs::Pose pose = msg->pose[i];
            // 处理信息
            car_pose.position = pose.position;
            
			car_pose.orientation = pose.orientation;

        }
    }
}


void little_car::update_position()
{
	odom_trans.header.frame_id = "map";		//坐标变换的父坐标系
	odom_trans.child_frame_id = "base_link";	//子坐标系
    odom_trans.header.stamp = ros::Time::now();
    odom_trans.transform.translation.x = car_pose.position.x;//小车 x 方向的位置设置
    odom_trans.transform.translation.y = car_pose.position.y;
    odom_trans.transform.translation.z = car_pose.position.z;
	odom_trans.transform.rotation = car_pose.orientation;
	return;
}
void little_car::update_()
{
	
	joint_state.header.stamp = ros::Time::now();
   	joint_state.name.resize(4);
   	joint_state.position.resize(4);
   	joint_state.name[0] ="base_to_wheel_1";
   	joint_state.position[0] = 0;
    joint_state.name[1] ="base_to_wheel_2";
    joint_state.position[1] = 0;
    joint_state.name[2] ="base_to_wheel_3";
    joint_state.position[2] = 0;
	joint_state.name[3] ="base_to_wheel_4";
	joint_state.position[3] = 0;
	
	update_position();//更新位置信息
	joint_pub.publish(joint_state);
	broadcaster.sendTransform(odom_trans);//坐标变换广播
	return;
}
