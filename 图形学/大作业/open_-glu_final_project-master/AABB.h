#pragma once
#ifndef AABB_H
#define AABB_H

#include <vector>
#include<iostream>
struct AABB {
    float min_x, min_y, min_z; // AABB 的最小坐标
    float max_x, max_y, max_z; // AABB 的最大坐标
};

class AABB_detect {
public:

    std::vector<struct AABB> Channel;//可供小球通过的通道AABB的定义
    struct AABB ball;
    float ballz; //用于上跳检测
    float obj_size = 2;
    // 构造函数，用于初始化AABB
    AABB_detect() {};
    // 初始化小球的 AABB
    void Init_AABB_ball(float min_x, float min_y, float min_z, float max_x, float max_y, float max_z) {
        ball.min_x = min_x;
        ball.min_y = min_y;
        ball.min_z = min_z;
        ball.max_x = max_x;
        ball.max_y = max_y;
        ball.max_z = max_z;
    }
    //添加地图中可供小球通过的通道的AABB，为矩形
    void Add_Channel(float min_x, float min_y, float min_z, float max_x, float max_y, float max_z) {
        AABB new_channel = { min_x, min_y, min_z, max_x, max_y, max_z };
        Channel.push_back(new_channel);
    }
    bool detect_single_Channel(int i) {
        // 检查 x 轴是否重叠
        if (ball.min_x > Channel[i].max_x || ball.max_x < Channel[i].min_x) {
            return false; // x 轴不重叠，不相交
        }
        // 检查 y 轴是否重叠
        if (ball.min_y > Channel[i].max_y || ball.max_y < Channel[i].min_y) {
            return false; // y 轴不重叠，不相交
        }
        // 检查 z 轴是否重叠
        if (ball.min_z > Channel[i].max_z || ball.max_z < Channel[i].min_z) {
            return false; // z 轴不重叠，不相交
        }
        return true; // x、y、z 轴都重叠，相交
    }
    bool detect_channel_ball() {
        for (int i = 0;i < Channel.size();i++) {
            if (detect_single_Channel(i) == 1)return 1;//相交出界
        }
        return 0;
    }
    void clear() {
        Channel.clear();
    }
};

#endif // AABB_H