#include "myglwidget.h"
#include<iostream>
#include <QApplication>
#include <GL/freeglut.h>
int maze[10][10] = {
    {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
    {1, 0, 0, 0, 1, 0, 0, 1, 0, 1},
    {1, 0, 1, 0, 1, 0, 1, 1, 0, 1},
    {1, 0, 1, 0, 0, 0, 1, 0, 0, 1},
    {1, 1, 1, 0, 1, 1, 1, 0, 1, 1},
    {1, 0, 0, 0, 0, 0, 0, 0, 0, 1},
    {1, 1, 1, 1, 1, 1, 1, 1, 1, 1},
    {1, 0, 0, 0, 0, 0, 0, 0, 0, 1},
    {1, 0, 1, 1, 1, 1, 1, 1, 0, 1},
    {1, 1, 1, 1, 1, 1, 1, 1, 1, 1}
};
const int width = 10;  // 迷宫的宽度
const int height = 10; // 迷宫的高度
const float blockSize = 1.0f; // 每个立方体的大小
const float zPosition = 0.0f; // 所有立方体在z轴上的位置（深度）


float ballX = 1.0f, ballY = 1.0f, ballZ = 0.0f; // 初始位置
float AtX = ballX, AtY = ballY - 1.5, AtZ = ballZ + 1;//摄像机位置
float targetX = 1, targetY = 10, targetZ = ballZ;//摄像机看向位置，要跟随小球的移动变化
float ballRadius = 0.3f; // 小球半径
const float stepSize = 0.2f; // 移动步长

// 假设的方向常量
const int FRONT = 0;
const int BACK = 1;
const int LEFT = 2;
const int RIGHT = 3;
int Y_or_X = 1;//当前小球的正方向视野是平行于y轴的，还是平行于x轴的（迷宫初始化小球正方向视野平行于x轴，Y_or_X=-1）
int front_or_back = 1;//当前球视角的正方向相对于世界坐标的正方向，1为相同，-1为相反


void drawCube(float x, float y, float z, float size) {

    //填充模式
    glColor3f(0.0f, 0.0f, 1.0f);
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
    glBegin(GL_QUADS);
    // 前面
    glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y + size / 2, z + size / 2);
    glVertex3f(x - size / 2, y + size / 2, z + size / 2);

    // 后面
    glVertex3f(x - size / 2, y - size / 2, z - size / 2);
    glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z - size / 2);

    // 左面
    glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glVertex3f(x - size / 2, y - size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z + size / 2);

    // 右面
    glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glVertex3f(x + size / 2, y + size / 2, z + size / 2);

    // 上面
    glVertex3f(x - size / 2, y + size / 2, z + size / 2);
    glVertex3f(x + size / 2, y + size / 2, z + size / 2);
    glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z - size / 2);

    // 下面
    glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glVertex3f(x - size / 2, y - size / 2, z - size / 2);

    glEnd(); // 结束绘制四边形（面）

    glColor3f(1.0f, 1.0f, 1.0f);
    glLineWidth(2.0f);
    // 启用线框模式来绘制立方体的边
    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);

    // 绘制立方体的六个面
    glBegin(GL_QUADS); // 开始绘制一组四边形（面）

    // 前面
    glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y + size / 2, z + size / 2);
    glVertex3f(x - size / 2, y + size / 2, z + size / 2);

    // 后面
    glVertex3f(x - size / 2, y - size / 2, z - size / 2);
    glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z - size / 2);

    // 左面
    glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glVertex3f(x - size / 2, y - size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z + size / 2);

    // 右面
    glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glVertex3f(x + size / 2, y + size / 2, z + size / 2);

    // 上面
    glVertex3f(x - size / 2, y + size / 2, z + size / 2);
    glVertex3f(x + size / 2, y + size / 2, z + size / 2);
    glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glVertex3f(x - size / 2, y + size / 2, z - size / 2);

    // 下面
    glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glVertex3f(x - size / 2, y - size / 2, z - size / 2);

    glEnd(); // 结束绘制四边形（面）

    // 禁用线框模式（如果需要绘制填充的多边形）
    // glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
}

void drawBall() {
    glColor3f(0.0f, 1.0f, 0.0f);
    glPushMatrix();
    glTranslatef(ballX, ballY, ballZ);
    glutSolidSphere(ballRadius, 20, 20); // 绘制球体，20x20 细分
    glPopMatrix();
}


void updateDirection(int moveDirection) {
    // 临时变量存储新方向
    int new_Y_or_X = Y_or_X;
    int new_front_or_back = front_or_back;

    // 根据当前方向和移动方向更新新方向
    if (Y_or_X == 1) { // 视野平行于Y轴
        if (front_or_back == 1) { // 正方向与世界坐标一致
            if (moveDirection == FRONT) {
                // 不改变方向
                ballY += stepSize;
            }
            else if (moveDirection == BACK) {
                new_front_or_back = -1;
                ballY -= stepSize;
            }
            else if (moveDirection == LEFT) {
                new_Y_or_X = 0;
                new_front_or_back = -1; // 旋转后正方向与世界坐标的X轴正方向一致
                ballX -= stepSize;
            }
            else if (moveDirection == RIGHT) {
                new_Y_or_X = 0;
                new_front_or_back = 1; // 旋转后正方向与世界坐标的X轴负方向一致
                ballX += stepSize;
            }
        }
        else { // front_or_back == -1，即反方向与世界坐标一致
            // ...（与上面类似，但方向相反）
            if (moveDirection == FRONT) {
                ballY -= stepSize;
            }
            else if (moveDirection == BACK) {
                new_front_or_back = 1;
                ballY += stepSize;
            }
            else if (moveDirection == LEFT) {
                new_Y_or_X = 0;
                new_front_or_back = 1;
                ballX += stepSize;
            }
            else if (moveDirection == RIGHT) {
                new_Y_or_X = 0;
                new_front_or_back = -1;
                ballX -= stepSize;
            }
        }
    }
    else { // Y_or_X == 0，即视野平行于X轴
        // ...（与Y_or_X == 1类似，但处理X轴和Y轴的交换）
        if (front_or_back == 1) {
            if (moveDirection == FRONT) {
                // 不改变方向
                ballX += stepSize;
            }
            else if (moveDirection == BACK) {
                new_front_or_back = -1;
                ballX -= stepSize;
            }
            else if (moveDirection == LEFT) {
                new_Y_or_X = 1;
                new_front_or_back = 1;
                ballY += stepSize;
            }
            else if (moveDirection == RIGHT) {
                new_Y_or_X = 1;
                new_front_or_back = -1;
                ballY -= stepSize;
            }
        }
        else {
            // ...（与上面类似，但方向相反）
            if (moveDirection == FRONT) {
                ballX -= stepSize;
            }
            else if (moveDirection == BACK) {
                new_front_or_back = 1;
                ballX += stepSize;
                // 不改变方向
            }
            else if (moveDirection == LEFT) {
                new_Y_or_X = 1;
                new_front_or_back = -1;
                ballY -= stepSize;
            }
            else if (moveDirection == RIGHT) {
                new_Y_or_X = 1;
                new_front_or_back = 1;
                ballY += stepSize;
            }
        }
    }

    // 更新原始变量
    Y_or_X = new_Y_or_X;
    front_or_back = new_front_or_back;
}

void display() {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(70.0, 1, 0.1, 1000.0); //透视投影矩阵

    glMatrixMode(GL_MODELVIEW);
    glLoadIdentity();
    // 设置相机位置等...
    //gluLookAt(1.0, 1.0, 0.0, 1.0, 10.0, 0.0, 0.0, 0.0, 1.0); //迷宫视角
    gluLookAt(AtX, AtY, AtZ, targetX, targetY, targetZ, 0.0, 0.0, 1.0); //高一点的视角 //假设球初始位置在1.0，1.0，1.0，要从一个较高的角度看见球，摄像机位置要在球后方和上方

    // 遍历迷宫数组并绘制每个立方体
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            if (maze[x][y]) { // 如果是墙壁
                // 计算立方体的位置
                float cubeX = x * blockSize;
                float cubeY = y * blockSize;
                // 使用固定的z值
                drawCube(cubeX, cubeY, zPosition, blockSize);
            }
            // 注意：在这个例子中，我们假设路径是“空气”或“透明”的，因此不绘制它们。
        }
    }
    drawBall();
    glutSwapBuffers();

}

void handleKeys(unsigned char key, int x, int y) {


    switch (key) {
    case 'w': updateDirection(FRONT);break; // 前进 
    case 's': updateDirection(BACK); break; // 后退
        //左右移动会切换当前是在x轴还是y轴上运动，也就是在行还是在列上运动
    case 'a': updateDirection(LEFT); break; // 左移
    case 'd': updateDirection(RIGHT); break; // 右移
        // 可以添加更多按键来处理上移（'e'）、下移（'c'）、旋转视角等
    }
    std::cout << Y_or_X << " " << front_or_back << "\n";
    if (Y_or_X == 1) {
        if (front_or_back == 1) {
            targetX = ballX;
            targetY = 10.0f;
        }
        else {
            targetX = ballX;
            targetY = -10.0f;
        }
        AtX = ballX;
        AtY = ballY - 1.5;
        AtZ = ballZ + 1;//摄像机位置
    }
    else {
        if (front_or_back == 1) {
            targetY = ballY;
            targetX = 10.0f;
        }
        else {
            targetY = ballY;
            targetX = -10.f;
        }
        AtX = ballX - 1.5;
        AtY = ballY;
        AtZ = ballZ + 1;//摄像机位置
    }
    std::cout << AtX << " " << AtY << " " << targetX << " " << targetY << "\n";
    // 强制重新绘制
    display();
}



void initOpenGL() {
    // 设置清除颜色为黑色
    glClearColor(0.0, 0.0, 0.0, 1.0);
    // 启用深度测试
    glEnable(GL_DEPTH_TEST);
    // 设置合适的投影矩阵（您已经在 display() 中设置了）
}

// 主函数
int main2(int argc, char** argv) {
    // 初始化 GLUT
    glutInit(&argc, argv);
    // 设置显示模式为双缓冲、RGB 颜色和深度测试
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    // 设置窗口大小
    glutInitWindowSize(350, 350);
    // 创建窗口并设置标题
    glutCreateWindow("3D Maze");

    // 初始化 OpenGL 状态
    initOpenGL();

    // 注册显示回调函数
    glutDisplayFunc(display);
    glutKeyboardFunc(handleKeys); // 注册键盘回调函数
    // 进入 GLUT 事件处理循环
    glutMainLoop();

    return 0;
}
