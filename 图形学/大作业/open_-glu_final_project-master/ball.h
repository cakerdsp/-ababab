#pragma once
#ifndef BALL_H
#define BALL_H
#include <GL/glew.h>
#include <GL/freeglut.h>

class Ball {
public:
    // 小球半径
    float ballRadius;

    // 初始位置
    float ballX, ballY, ballZ;
    //运动速度
    float velocity = 0.2f;
    //不同方向的运动速度，假设初始运动方向沿x轴
    float velocityX, velocityY, velocityZ;
    //是否处于上跳过程,为0时不起跳；不为0是跳跃过程的时间
    int Jump_time = 0;
    //上跳过程的初始z速度
    float Jump_init_vz = 1.6f;
    //小球的材料
    GLfloat mat_ambient[4] = { 0.7f, 0.4f, 0.4f, 1.0f };;//环境光的反射
    GLfloat mat_diffuse[4] = { 0.7f, 0.4f, 0.4f, 1.0f };//漫射光的反射
    GLfloat mat_specular[4] = { 0.5f, 0.5f, 0.5f, 0.3f };//镜面光的反射,前3个是颜色，最后是程度
    GLfloat mat_shininess[4] = { 20.0f };//物体光泽度

    // 旋转角度
    float rotationX = 0.0f;
    float rotationY = 0.0f;
    float rotationSpeed = 10.0f; // 旋转速度
    int if_rotationX = 1;

    //速度和角速度变换
    float maxSpeed = 0.6f; // 最大速度
    float acc = 0.01f; // 加速度


    // 构造函数，用于初始化小球的所有属性//初始沿y轴运动
    Ball(float radius = 1.0f, float x = 1.0f, float y = 1.0f, float z = 0.0f,
        float vx = 0.0f, float vy = 0.2f, float vz = 0.0f)
        : ballRadius(radius), ballX(x), ballY(y), ballZ(z),
        velocityX(vx), velocityY(vy), velocityZ(vz) {

    }
    void Ball_reset(float radius = 1.0f, float x = 1.0f, float y = 1.0f, float z = 0.0f,
        float vx = 0.0f, float vy = 0.2f, float vz = 0.0f) {
        ballRadius = radius;
        ballX = x;
        ballY = y;
        ballZ = z;
        velocityX = vx;
        velocityY = vy;
        velocityZ = vz;
        rotationX = 0.0f;
        rotationY = 0.0f;
        if_rotationX = 1;
        velocity = 0.2;
    }

    // 更新位置的方法
    void updatePosition(float deltaTime) {

        if (Jump_time != 0) {
            //现在设置的是在5s起跳过程中，高度是4（4个球的大小），水平位移也是4
            ballX += velocityX * deltaTime;
            ballY += velocityY * deltaTime;
            if (velocityX == 0) {//在y轴上运动，旋转轴为X
                rotationX += rotationSpeed * deltaTime;
                if_rotationX = 1;
            }
            else {
                rotationY += rotationSpeed * deltaTime;
                if_rotationX = 0;
            }
            velocityZ = Jump_init_vz;
            Jump_init_vz -= 0.64 * deltaTime; //加速度为1.28
            ballZ += (Jump_init_vz + velocityZ) / 2 * deltaTime;
            Jump_time -= 1;
            if (ballZ <= 0) {
                // 球落地后恢复未起跳的所有设置
                ballZ = 0.0f;
                Jump_time = 0;
                velocityZ = 0;
                Jump_init_vz = 1.6f;
            }
            //调试用
           //std::cout << Jump_time << " " << velocityZ << " " << velocityY << " " << ballZ <<" " <<ballY<< "\n";
        }

        else {
            ballX += velocityX * deltaTime;
            ballY += velocityY * deltaTime;
            ballZ += velocityZ * deltaTime;
            if (velocityX == 0) {//在y轴上运动，旋转轴为X
                rotationX += rotationSpeed * deltaTime * (velocityY > 0 ? -1 : 1);
                if_rotationX = 1;
            }
            else {
                rotationY += rotationSpeed * deltaTime * (velocityX > 0 ? 1 : -1);
                if_rotationX = 0;
            }
        }
    }

    //转换小球的运动方向
    void update_ball_Direction(int Left_or_Right_or_Jump) {
        // 根据时间增加速度，但不超过最大速度
        if (velocity < maxSpeed) {
            velocity += acc;
        }
        // 更新角速度，使其与速度匹配
        rotationSpeed += acc * 50.0f; // 角速度与速度成正比
        //左转
        if (Left_or_Right_or_Jump == 1) {
            //在x轴方向运动
            if (velocityX != 0.0f) {
                float sign_X = (velocityX > 0) ? 1.0f : -1.0f;
                velocityY = sign_X * velocity;
                velocityX = 0.0f;
            }
            //在y轴上运动
            else if (velocityY != 0.0) {
                float sign_Y = (velocityY > 0) ? -1.0f : 1.0f;
                velocityX = sign_Y * velocity;
                velocityY = 0;
            }
        }
        //右转
        else if (Left_or_Right_or_Jump == -1) {
            //在x轴方向运动
            if (velocityX != 0.0f) {
                float sign_X = (velocityX > 0) ? -1.0f : 1.0f;
                velocityY = sign_X * velocity;
                velocityX = 0.0f;
            }
            //在y轴上运动
            else if (velocityY != 0.0) {
                float sign_Y = (velocityY > 0) ? 1.0f : -1.0f;
                velocityX = sign_Y * velocity;
                velocityY = 0.0f;
            }
        }
        //上跳
        else if (Left_or_Right_or_Jump == 0) {
            Jump_time = 22;
        }

    }
    void drawShadow() {
        glDisable(GL_LIGHTING); 
        glDisable(GL_DEPTH_TEST); 
        glColor3f(0.0f, 0.0f, 0.0f); // 设置阴影颜色为黑色

        glPushMatrix();
        // 将阴影投影到地面上
        glTranslatef(ballX, ballY, -1.0f);
        glScalef(1.0f, 1.0f, 0.0f); // 将z轴缩放为 0，使阴影扁平
        glutSolidSphere(ballRadius, 20, 20); // 绘制阴影
        glPopMatrix();
        glEnable(GL_DEPTH_TEST); //重新启用深度测试 防止频闪
        glEnable(GL_LIGHTING);
    }

};
#endif // BALL_H