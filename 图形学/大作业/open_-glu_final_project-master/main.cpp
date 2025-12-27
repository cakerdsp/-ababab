#include "myglwidget.h"
#include"ball.h"
#include"Object.h"
#include "AABB.h"
#include <QApplication>
#include <GL/freeglut.h>
#include <random>
#include <vector>
#include <iostream>
#include <chrono>


std::chrono::time_point<std::chrono::high_resolution_clock> startTime;



Ball ball = Ball();
AABB_detect aabb_detect = AABB_detect();
Objects obj = Objects();
// 检查是否相撞的标志
bool check = false;

unsigned long long time_ = 0;
//障碍物
// 存放障碍物的参数队列
std::vector<std::vector<float>> objs;
//生成障碍物的概率
float obj_factor = 0.3;
//每次检测的时间间隔
int obj_delta = 100;
int obj_count = obj_delta;
int obj_size = 2;

// 障碍物生成在前方的距离
float front = 10;
// 障碍物留存时间
float keep_time = 140;

//游戏开始标志
bool gameStarted = false;
//游戏开始页面的纹理
GLuint startPageTexture;
//游戏结束页面的纹理
GLuint overPageTextture;
//小球纹理
GLuint ballTexture;
// 添加重新开始游戏的标志
bool gameOver = false;


float direct[2] = { ball.velocityX,ball.velocityY };
int ter_size = 10;
int ter_delta = 50;
int ter_count = ter_delta;
float ter_front = 150;
int edge = 15;
float ter_keep_time = 10000;
float margin = 15;
float check_y = ball.ballY;
float check_x = ball.ballX;
float check_dis = 60;
float camera_back = 5;
float factor_camera = 0.1;



std::random_device rd;  // 随机数设备，用于获取随机种子
std::mt19937 gen(rd()); // 以随机设备作为种子的Mersenne Twister生成器
std::uniform_real_distribution<> dis(0.0, 1.0);// 均匀分布的实数，范围0到1
std::uniform_int_distribution<> dis_int(0, 2);// 均匀分布的整数，范围从0到向量大小减1
std::uniform_int_distribution<> dis_int2(0, 3);
std::vector<std::vector<float>> ters;


float AtX = 0.0f, AtY = ball.ballY + camera_back, AtZ = 6.0f;//摄像机位置
float LX = 0.0f, LY = 0.0f, LZ = 50.0f;
float factor_light = 0.1;
float light_back = 20;
float targetX = ball.ballX, targetY = ball.ballY, targetZ = ball.ballZ;//摄像机看向位置，要跟随小球的移动变化
float deltaTime = 5; //5ms刷新一次，定时器频率，每隔多久刷新一次小球位置，模拟运动
float Change_delete = 0;//为了更好的视觉体验，小球转方向时，延迟更新跟随摄像机位置，体现转弯过程

void resetGame() {
    ball.Ball_reset();
    aabb_detect.clear();
    objs.clear();
    ters.clear();
    direct[0] = ball.velocityX;
    direct[1] = ball.velocityY;
    check_x = ball.ballX;
    check_y = ball.ballY;
    // 重置摄像机位置
    AtX = 0.0f;
    AtY = ball.ballY + camera_back;
    AtZ = 6.0f;

    // 重置光源位置
    LX = 0.0f;
    LY = 0.0f;
    LZ = 50.0f;

    time_ = 0;
    check = false;

}


void renderOverPage() {

    glDisable(GL_LIGHTING);
    glClear(GL_COLOR_BUFFER_BIT);
    glClear(GL_DEPTH_BUFFER_BIT);
    float w = glutGet(GLUT_WINDOW_WIDTH);
    float h = glutGet(GLUT_WINDOW_HEIGHT);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    glOrtho(0.0, w, 0.0, h, -1.0, 10.0);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    gluLookAt(0.0, 0.0, 6.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0);

    // 启用纹理功能并绑定纹理
    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, overPageTextture);

    glBegin(GL_QUADS);
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0);
    glTexCoord2f(1.0, 0.0); glVertex2f(w, 0.0);
    glTexCoord2f(1.0, 1.0); glVertex2f(w, h);
    glTexCoord2f(0.0, 1.0); glVertex2f(0.0, h);
    glEnd();

    // 禁用纹理功能
    glDisable(GL_TEXTURE_2D);

    glutSwapBuffers();
}

void drawBall() {

    //1. 设置小球的材料属性

    glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, ball.mat_ambient);
    glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, ball.mat_diffuse);
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, ball.mat_specular);
    glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, ball.mat_shininess);

    //2. 设置光源 体现立体感
    // 启用光源0
    glEnable(GL_LIGHT0);
    // 设置光源的漫反射和镜面反射颜色（这里使用白色光和白色高光作为示例）
    GLfloat light_diffuse_ball[] = { 1.0f, 1.0f, 1.0f, 1.0f };
    GLfloat light_specular_ball[] = { 1.0f, 1.0f, 1.0f, 1.0f };
    // 设置光源属性
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse_ball);
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular_ball);

    // 启用纹理并绑定纹理
    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, ballTexture);

    //3. 绘制小球
    glColor3f(0.7f, 0.4f, 0.4f);
    glPushMatrix();
    glTranslatef(ball.ballX, ball.ballY, ball.ballZ);
    if (ball.if_rotationX == 1) {
        glRotatef(ball.rotationX, 1.0f, 0.0f, 0.0f); // 绕X轴旋转
    }
    else {
        glRotatef(ball.rotationY, 0.0f, 1.0f, 0.0f); // 绕y轴旋转
    }

    // 绘制带纹理的球体
    GLUquadric* quadric = gluNewQuadric();
    gluQuadricTexture(quadric, GL_TRUE); // 启用纹理坐标生成
    gluSphere(quadric, ball.ballRadius, 40, 40); // 绘制球体
    gluDeleteQuadric(quadric);

    glPopMatrix();

    // 禁用纹理
    glDisable(GL_TEXTURE_2D);
}

//切换摄像头方向，假设在XY平面上运动，摄像机的所在位置的z轴坐标不用
void update_camera_Direction() {
    // 计算目标点的偏移量（小球前方一段距离）
    float lookAheadDistance=3.0f; // 看向小球前方多远的位置，可以根据需要调整
    if (ball.velocityX != 0) {
        //不在X轴上运动
        float sign = (ball.velocityX > 0) ? -1.0f : 1.0f;
        AtX = AtX + factor_camera * (ball.ballX + sign * camera_back - AtX);
        AtY = AtY + factor_camera * (ball.ballY - AtY);
        // 目标点在小球前方
        targetX = ball.ballX - sign * lookAheadDistance;
        targetY = ball.ballY;

    }
    else {
        float sign = (ball.velocityY > 0) ? -1.0f : 1.0f;
        AtY = AtY + factor_camera * (ball.ballY + sign * camera_back - AtY);
        AtX = AtX + factor_camera * (ball.ballX - AtX);
        // 目标点在小球前方
        targetX = ball.ballX;
        targetY = ball.ballY - sign * lookAheadDistance;

    }

    targetZ = ball.ballZ;
}

//切换追随小球的光源位置
void update_light_Position() {
    ////沿x轴运动时：在物体x运动方向的后方打光，因为视角跟随是从后往前看。y轴打光方向无所谓
    ////沿y轴运动时：在物体y运动方向的后方打光，因为视角跟随是从后往前看。x轴打光方向无所谓
    //if (ball.velocityX != 0) {
    //    //不在X轴上运动
    //    float sign = (ball.velocityX > 0) ? -1.0f : 1.0f;
    //    LX = LX + factor_light * (ball.ballX + sign * light_back - LX);
    //    LY = LY + factor_light * (ball.ballY - LY);

    //}
    //else {
    //    float sign = (ball.velocityY > 0) ? -1.0f : 1.0f;
    //    LY = LY + factor_light * (ball.ballY + sign * light_back - LY);
    //    LX = LX + factor_light * (ball.ballX - LX);
    //}
    ///*AtZ = ball.ballZ + 2 * ball.ballRadius;*/
    // 光源的偏移量
    float light_offsetX = 0.0f;
    float light_offsetY = 0.0f;
    float light_offsetZ = 10.0f; // 光源在 Z 轴上方 10 个单位

    // 根据小球的运动方向调整光源的位置
    if (ball.velocityX != 0) {
        float sign = (ball.velocityX > 0) ? -1.0f : 1.0f;
        light_offsetX = sign * 20.0f; // 光源在运动方向的后方 20 个单位
    }
    else if (ball.velocityY != 0) {
        float sign = (ball.velocityY > 0) ? -1.0f : 1.0f;
        light_offsetY = sign * 20.0f; // 光源在运动方向的后方 20 个单位
    }

    //光源源的位置
    LX = ball.ballX + light_offsetX;
    LY = ball.ballY + light_offsetY;
    LZ = ball.ballZ + light_offsetZ;

    // 设置光源的位置
    GLfloat light_position_ball[] = { LX, LY, LZ, 1.0f }; // 光源的位置
    glLightfv(GL_LIGHT0, GL_POSITION, light_position_ball);

    // 设置光源的方向
    GLfloat light_direction[] = { ball.ballX - LX, ball.ballY - LY, ball.ballZ - LZ, 0.0f };
    glLightfv(GL_LIGHT0, GL_SPOT_DIRECTION, light_direction);

}


//整体屏幕渲染
void renderGamePage() {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    float w = glutGet(GLUT_WINDOW_WIDTH);

    float h = glutGet(GLUT_WINDOW_HEIGHT);
    GLfloat ratio = (GLfloat)w / (GLfloat)h;
    gluPerspective(70.0, ratio, 0.1, 1000.0); // 根据宽高比例设置透视投影

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    // 设置相机位置等...
    //gluLookAt(0.0, -6.0, 6.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0); //全局固定视角
    gluLookAt(AtX, AtY, AtZ, targetX, targetY, targetZ, 0.0, 0.0, 1.0); //高一点的视角 //假设球初始位置在1.0，1.0，1.0，要从一个较高的角度看见球，摄像机位置要在球后方和上方



    // 设置光源属性
    GLfloat light_position[] = { LX, LY, LZ, 1.0f };
    GLfloat light_diffuse[] = { 1.0f, 1.0f, 1.0f, 1.0f };
    GLfloat light_ambient[] = { 0.0f, 0.0f, 0.0f, 1.0f };
    //GLfloat light_direction[] = { ball.ballX, ball.ballY, ball.ballZ }; 
    //glLightfv(GL_LIGHT1, GL_SPOT_DIRECTION, light_direction);
    //GLfloat spot_cutoff = 45.0; // 以度为单位的聚光角度
    //glLightf(GL_LIGHT1, GL_SPOT_CUTOFF, spot_cutoff);
    //GLfloat light_attenuation[] = { 1.0, 0.0, 0.0 }; // 常数衰减，没有线性或二次衰减
    //glLightfv(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, light_attenuation);
    glLightfv(GL_LIGHT2, GL_AMBIENT, light_ambient);
    glLightfv(GL_LIGHT2, GL_POSITION, light_position);
    glLightfv(GL_LIGHT2, GL_DIFFUSE, light_diffuse);



    //这个想要用来模拟太阳光


    //GLfloat sun_position[] = { -0.5f, 0.3f, -1.0f, 0.0f }; // 夕阳方向性光源的位置（W为0表示方向性光源）
    //GLfloat sun_color_diffuse[] = { 1.0f, 1.0f, 0.0f, 1.0f }; // 夕阳的漫反射颜色（橙色）

    //glLightfv(GL_LIGHT3, GL_POSITION, sun_position);
    //glLightfv(GL_LIGHT3, GL_DIFFUSE, sun_color_diffuse);




    drawGround(0.0, 0.0, -1.0, 1000.0f, 1000.0f, 0.0f);
    //绘制小球的阴影
    ball.drawShadow();
    drawBall();
    aabb_detect.Init_AABB_ball(ball.ballX - ball.ballRadius, ball.ballY - ball.ballRadius, ball.ballZ - ball.ballRadius,
        ball.ballX + ball.ballRadius, ball.ballY + ball.ballRadius, ball.ballZ + ball.ballRadius);

    // 地形
    //ter_count--;
    if (ters.size() == 0 || abs(check_x - ball.ballX) + abs(check_y - ball.ballY) < check_dis) {
        /*ter_count = ter_delta;*/
        float x, y, z, size;
        if (ball.velocityX != 0) {
            float sign = (ball.velocityX > 0) ? 1.0f : -1.0f;
            for (float i = check_x; abs(i - check_x) < ter_front; i += sign * margin) {
                x = i;
                float left_or_right = dis(gen) > 0.5 ? 1.0f : -1.0f;
                y = ball.ballY + left_or_right * edge;
                z = ball.ballZ;
                size = ter_size;
                float current = time_ + ter_keep_time;
                //std::vector<float> tmp = { x,y,z,size,current,float(dis_int(gen)) };
                ters.push_back({ x,y,z,size,current,float(dis_int(gen)) });
            }
            check_x = check_x + sign * ter_front;

        }
        else {
            float sign = (ball.velocityY > 0) ? 1.0f : -1.0f;
            for (float i = check_y; abs(i - check_y) < ter_front; i += sign * margin) {
                y = i;
                float left_or_right = dis(gen) > 0.5 ? 1.0f : -1.0f;
                x = ball.ballX + left_or_right * edge;
                z = ball.ballZ;
                size = ter_size;
                float current = time_ + ter_keep_time;
                //std::vector<float> tmp = { x,y,z,size,current,float(dis_int(gen)) };
                ters.push_back({ x,y,z,size,current,float(dis_int(gen)) });
            }
            check_y = check_y + sign * ter_front;
        }
        //float current = time_ + ter_keep_time;
    }

    // 生成障碍物
    obj_count--;
    float number = dis(gen);
    if (number < obj_factor && obj_count == 0) {
        obj_count = obj_delta;
        float x, y, z, size;
        if (ball.velocityX != 0) {
            y = ball.ballY;
            float sign = (ball.velocityX > 0) ? 1.0f : -1.0f;
            x = ball.ballX + sign * front;
            z = ball.ballZ;
            size = obj_size;
        }
        else {
            x = ball.ballX;
            float sign = (ball.velocityY > 0) ? 1.0f : -1.0f;
            y = ball.ballY + sign * front;
            z = ball.ballZ;
            size = obj_size;
        }
        float current = time_ + keep_time;
        std::vector<float> tmp = { x,y,z,size,current,float(dis_int2(gen)) };
        objs.push_back(tmp);

    }
    else if (obj_count == 0) {
        obj_count = obj_delta;
    }


    while (!objs.empty()) {
        if (time_ > (*objs.begin())[4]) {
            objs.erase(objs.begin());
        }
        else {
            break;
        }
    }
    if (direct[0] != ball.velocityX || direct[1] != ball.velocityY) {
        ters.clear();
        direct[0] = ball.velocityX;
        direct[1] = ball.velocityY;
        check_x = ball.ballX;
        check_y = ball.ballY;
    }
    while (!ters.empty()) {
        if (time_ > (*ters.begin())[4]) {
            ters.erase(ters.begin());
        }
        else {
            break;
        }
    }
    for (int i = 0; i < objs.size(); ++i) {
        if (objs[i][5] == 0) {
            // 交通灯
            obj.TrafficLight(objs[i][0], objs[i][1], objs[i][2], objs[i][3] * 0.5);
            aabb_detect.Add_Channel(
                objs[i][0] - objs[i][3] / 4,  // min_x
                objs[i][1] - objs[i][3] / 4,  // min_y
                objs[i][2] - 7.3 * objs[i][3] * 0.5 / 2,  // min_z (交通灯高度为 7.3，缩放比例为 objs[i][3] * 0.5)
                objs[i][0] + objs[i][3] / 4,  // max_x
                objs[i][1] + objs[i][3] / 4,  // max_y
                objs[i][2] + 7.3 * objs[i][3] * 0.5 / 2   // max_z
            );
        }
        else if (objs[i][5] == 1) {
            // 箱子
            obj.Box(objs[i][0], objs[i][1], objs[i][2], objs[i][3]);
            aabb_detect.Add_Channel(
                objs[i][0] - objs[i][3] / 2,  // min_x
                objs[i][1] - objs[i][3] / 2,  // min_y
                objs[i][2] - objs[i][3] / 2,  // min_z
                objs[i][0] + objs[i][3] / 2,  // max_x
                objs[i][1] + objs[i][3] / 2,  // max_y
                objs[i][2] + objs[i][3] / 2   // max_z
            );
        }
        else if (objs[i][5] == 2) {
            // 垃圾桶
            obj.TrashCan(objs[i][0], objs[i][1], objs[i][2], objs[i][3] * 0.5);
            aabb_detect.Add_Channel(
                objs[i][0] - objs[i][3] / 4,  // min_x
                objs[i][1] - objs[i][3] / 4,  // min_y
                objs[i][2] - 2.75 * objs[i][3] * 0.5 / 2,  // min_z (垃圾桶高度为 2.75，缩放比例为 objs[i][3] * 0.5)
                objs[i][0] + objs[i][3] / 4,  // max_x
                objs[i][1] + objs[i][3] / 4,  // max_y
                objs[i][2] + 2.75 * objs[i][3] * 0.5 / 2   // max_z
            );
        }
        else if (objs[i][5] == 3) {
            // 锥形路障
            obj.ConeRoadblock(objs[i][0], objs[i][1], objs[i][2], objs[i][3] * 0.25);
            aabb_detect.Add_Channel(
                objs[i][0] - objs[i][3] / 8,  // min_x
                objs[i][1] - objs[i][3] / 8,  // min_y
                objs[i][2] - 5.8 * objs[i][3] * 0.25 / 2,  // min_z (锥形路障高度为 5.8，缩放比例为 objs[i][3] * 0.25)
                objs[i][0] + objs[i][3] / 8,  // max_x
                objs[i][1] + objs[i][3] / 8,  // max_y
                objs[i][2] + 5.8 * objs[i][3] * 0.25 / 2   // max_z
            );
        }
    }
    check = false;
    check = aabb_detect.detect_channel_ball();
    aabb_detect.clear();

    if (check) {
        printf("hhh  ");
        gameStarted = false;
        gameOver = true;
        glutDisplayFunc(renderOverPage);

    }
    for (int i = 0; i < ters.size(); ++i) {
        //obj.House1(ters[i][0], ters[i][1], ters[i][2], ters[i][3]);
        if (ters[i][5] == 0) {
            obj.House1(ters[i][0], ters[i][1], ters[i][2], ters[i][3]);
            //aabb_detect.Add_Channel(objs[i][0] - objs[i][3] / 2, objs[i][1] - objs[i][3] / 2, objs[i][0] + objs[i][3] / 2, objs[i][1] + objs[i][3] / 2);
        }
        else if (ters[i][5] == 1) {
            obj.House2(ters[i][0], ters[i][1], ters[i][2], ters[i][3]);
            //aabb_detect.Add_Channel(objs[i][0] - objs[i][3] / 2, objs[i][1] - objs[i][3] / 2, objs[i][0] + objs[i][3] / 2, objs[i][1] + objs[i][3] / 2);
        }
        else if (ters[i][5] == 2) {
            obj.House3(ters[i][0], ters[i][1], ters[i][2], ters[i][3],ters[i][3],ters[i][3]);
            //aabb_detect.Add_Channel(objs[i][0] - objs[i][3] / 2, objs[i][1] - objs[i][3] / 2, objs[i][0] + objs[i][3] / 2, objs[i][1] + objs[i][3] / 2);
        }
    }


    glutSwapBuffers();
    time_++;
}



//键盘回调函数
void handleKeys(unsigned char key, int x, int y) {
    int Left_or_Right = 0;
    switch (key) {
    case 'a':
    case 'A':
        Left_or_Right = 1;
        ball.rotationX = 0.0f;
        ball.rotationY = 0.0f;
        ball.update_ball_Direction(Left_or_Right);
        Change_delete = 10;
        break; // 左移
    case 'd':
    case 'D':
        Left_or_Right = -1;
        ball.rotationX = 0.0f;
        ball.rotationY = 0.0f;
        ball.update_ball_Direction(Left_or_Right);
        Change_delete = 10;
        break; // 右移
    case 'w':
    case 'W':
        Left_or_Right = 0;
        ball.update_ball_Direction(Left_or_Right);
        Change_delete = 20;
        break; // 上跳
    }

}

//定时器的回调函数，每隔5ms重新渲染display，且更新小球位置，模拟小球运动，更新小球光源，更新摄像机位置
void update(int value) {
    auto currentTime = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> elapsedTime = currentTime - startTime;
    double elapsedSeconds = elapsedTime.count();
	obj_factor = 0.3 + 10 * elapsedSeconds / 3600;
    //std::cout << obj_factor << std::endl;
    if (gameStarted) {
        //更新小球的位置
        ball.updatePosition(0.1 * deltaTime);
        if (Change_delete == 0) {
            //更新摄像机追随小球的参数
            update_camera_Direction();
            //更新给小球打光的光源位置
            update_light_Position();
        }
        else {
            Change_delete -= 1;
        }
        deltaTime = 5;
        glutTimerFunc(deltaTime, update, 0); // 大约每 60 帧（1000/60 = 16.67ms）调用一次
    }
    // 请求重新显示
    glutPostRedisplay();

}

void initGame() {
    ballTexture = loadTexture("./images/ball.jpg");
    // 设置清除颜色为黑色
    glClearColor(0.53f, 0.81f, 0.98f, 1.0f);
    // 启用深度测试
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_LIGHTING);//启用光照功能
    //glEnable(GL_LIGHT0); // 启用光源
    glEnable(GL_LIGHT2);
    glEnable(GL_LIGHT3);
    glEnable(GL_COLOR_MATERIAL);   // 启用颜色材质
    //glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE); // 设置颜色控制的材质属性
    glutTimerFunc(deltaTime, update, 0);//
}

// 鼠标点击事件处理函数
void mouseClick(int button, int state, int x, int y) {
    if (button == GLUT_LEFT_BUTTON && state == GLUT_DOWN) {
        int winWidth = glutGet(GLUT_WINDOW_WIDTH);  // 窗口宽度
        int winHeight = glutGet(GLUT_WINDOW_HEIGHT); // 窗口高度

        // 将点击坐标转换为相对坐标（0到1之间）
        float clickX = (float)x / winWidth;
        float clickY = (float)y / winHeight;

        if (!gameStarted) {
            if (gameOver) {
                // 判断是否点击了重新开始按钮
                if (clickX >= 0.36f && clickX <= 0.6f && clickY >= 0.7f && clickY <= 0.84f) {
                    resetGame();
                    gameStarted = true;
                    initGame();
                    glutDisplayFunc(renderGamePage);
                    return;
                }
            }
            else if (clickX >= 0.38f && clickX <= 0.6f && clickY >= 0.6f && clickY <= 0.78f) {
                // 判断是否点击了开始按钮
                gameStarted = true;
            }
        }

        std::cout << "Mouse clicked at (" << x << ", " << y << ")" << std::endl;
    }
}


void renderStartPage() {
    if (gameStarted) {
        // 初始化 OpenGL 状态
        initGame();
        glutDisplayFunc(renderGamePage);
    }
    glClear(GL_COLOR_BUFFER_BIT);
    glClear(GL_DEPTH_BUFFER_BIT);
    float w = glutGet(GLUT_WINDOW_WIDTH);
    float h = glutGet(GLUT_WINDOW_HEIGHT);
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    glOrtho(0.0, w, 0.0, h, -1.0, 10.0);

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    gluLookAt(0.0, 0.0, 6.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0);

    // 启用纹理功能并绑定纹理
    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, startPageTexture);

    glBegin(GL_QUADS);
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0);
    glTexCoord2f(1.0, 0.0); glVertex2f(w, 0.0);
    glTexCoord2f(1.0, 1.0); glVertex2f(w, h);
    glTexCoord2f(0.0, 1.0); glVertex2f(0.0, h);
    glEnd();

    // 禁用纹理功能
    glDisable(GL_TEXTURE_2D);

    glutSwapBuffers();
}


void reshape(GLsizei w, GLsizei h) {
    GLfloat ratio = (GLfloat)w / (GLfloat)h;
    glViewport(0, 0, w, h);
}


int main(int argc, char** argv) {
    // 初始化 GLUT
    glutInit(&argc, argv);
    // 设置显示模式为双缓冲、RGB 颜色和深度测试
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    // 设置窗口大小
    glutInitWindowSize(1000, 500);
    // 设置窗口变形函数
    glutReshapeFunc(reshape);
    // 创建窗口并设置标题
    glutCreateWindow("3D Maze");
    //加载开始页面纹理
    startPageTexture = loadTexture("./images/start.png");
    overPageTextture = loadTexture("./images/gameover.png");
    startTime = std::chrono::high_resolution_clock::now();
    // 注册显示回调函数
    glutDisplayFunc(renderStartPage);
    glutKeyboardFunc(handleKeys); // 注册键盘回调函数
    glutMouseFunc(mouseClick); // 注册鼠标点击事件处理函数
    // 进入 GLUT 事件处理循环
    glutMainLoop();

    return 0;
}