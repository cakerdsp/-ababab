#include <ros/ros.h>
#include <std_msgs/Float64.h>
#include <unistd.h>
#include <termios.h>
#include <csignal>
#include <iostream>
#include <cmath>

void setNonBlockingInput()
{
    struct termios t;
    tcgetattr(STDIN_FILENO, &t);
    t.c_lflag &= ~(ICANON | ECHO);
    t.c_cc[VMIN] = 0;
    t.c_cc[VTIME] = 0;
    tcsetattr(STDIN_FILENO, TCSANOW, &t);
}

void restoreTerminal()
{
    struct termios t;
    tcgetattr(STDIN_FILENO, &t);
    t.c_lflag |= (ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &t);
}

bool checkKeyPress()
{
    fd_set readfds;
    FD_ZERO(&readfds);
    FD_SET(STDIN_FILENO, &readfds);
    struct timeval timeout;
    timeout.tv_sec = 0;
    timeout.tv_usec = 0;
    return select(1, &readfds, NULL, NULL, &timeout) > 0;
}

void signalHandler(int signum)
{
    restoreTerminal();
    exit(signum);
}

int main(int argc, char **argv)
{
    ros::init(argc, argv, "little_car_ctrl");
    ros::NodeHandle nh;

    setNonBlockingInput();
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);

    ros::Publisher wheel1_pub = nh.advertise<std_msgs::Float64>("/wheel_1_controller/command", 10);
    ros::Publisher wheel2_pub = nh.advertise<std_msgs::Float64>("/wheel_2_controller/command", 10);
    ros::Publisher wheel3_pub = nh.advertise<std_msgs::Float64>("/wheel_3_controller/command", 10);
    ros::Publisher wheel4_pub = nh.advertise<std_msgs::Float64>("/wheel_4_controller/command", 10);

    ros::Rate rate(20);

    std::cout << "Control keys:\n"
              << "  w: forward\n"
              << "  s: backward\n"
              << "  a: turn left\n"
              << "  d: turn right\n"
              << "  q: quit\n"
              << "  e: rotation clockwise\n"
              << "  f: rotate counterclockwise\n";

    std_msgs::Float64 w1, w2, w3, w4;
    w1.data = 0;
    w2.data = 0;
    w3.data = 0;
    w4.data = 0;

    while (ros::ok())
    {
        char lastKey = 0;
        // 清空缓冲区，只保留最后一个键
        while (checkKeyPress()) {
            lastKey = getchar();
        }

        // 默认停止
        w1.data = 0;
        w2.data = 0;
        w3.data = 0;
        w4.data = 0;

        switch (lastKey)
        {
            case 'w':
                w1.data = 4;
                w2.data = 4;
                w3.data = 4;
                w4.data = 4;
                break;
            case 's':
                w1.data = -4;
                w2.data = -4;
                w3.data = -4;
                w4.data = -4;
                break;
            case 'a':
                w1.data = 4;
                w2.data = 4;
                w3.data = 2;
                w4.data = 2;
                break;
            case 'd':
                w1.data = 2;
                w2.data = 2;
                w3.data = 4;
                w4.data = 4;
                break;
            case 'e':
                w1.data = -4;
                w2.data = -4;
                w3.data = 4;
                w4.data = 4;
                break;
            case 'f':
                w1.data = 4;
                w2.data = 4;
                w3.data = -4;
                w4.data = -4;
                break;
            case 'q':
                restoreTerminal();
                return 0;
            default:
                break;
        } 

        wheel1_pub.publish(w1);
        wheel2_pub.publish(w2);
        wheel3_pub.publish(w3);
        wheel4_pub.publish(w4);

        rate.sleep();
    }

    restoreTerminal();
    return 0;
}
