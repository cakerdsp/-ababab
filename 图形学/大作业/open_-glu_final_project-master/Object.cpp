#include"Object.h"
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define PI 3.14159265358979323846

// 纹理加载函数
GLuint loadTexture(const char* filename) {
    GLuint textureID;
    int width, height, nrChannels;
    stbi_set_flip_vertically_on_load(true);
    unsigned char* image = stbi_load(filename, &width, &height, &nrChannels, 0);  // 使用stb_image加载图像



    if (image == nullptr) {
        printf("stb_image could not load image %s\n", filename);
        return 0;  // 返回0表示加载失败
    }

    //显式设置字节对齐方式为 1
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
    glGenTextures(1, &textureID);  // 生成纹理ID
    glBindTexture(GL_TEXTURE_2D, textureID);  // 绑定纹理

    // 设置纹理参数（包装模式和过滤模式）
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

    // 根据图像的通道数确定内部格式
    GLenum internalFormat;
    if (nrChannels == 3)
        internalFormat = GL_RGB;
    else if (nrChannels == 4)
        internalFormat = GL_RGBA;
    else {
        printf("Image format not supported!\n");
        stbi_image_free(image);  // 释放图像数据
        return 0;  // 加载失败
    }

    // 将图像数据上传到GPU
    glTexImage2D(GL_TEXTURE_2D, 0, internalFormat, width, height, 0, internalFormat, GL_UNSIGNED_BYTE, image);

    // 释放加载的图像数据（由stb_image分配）
    stbi_image_free(image);



    // 取消绑定纹理
    glBindTexture(GL_TEXTURE_2D, 0);

    return textureID;  // 返回纹理ID
}



// #####################    基本元    #######################
void drawCube(float x, float y, float z, float size, GLint texture) {
    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, texture);
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);

    glBegin(GL_QUADS);

    // 前面
    glNormal3f(0.0f, 0.0f, 1.0f); // 法线
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + size / 2, y + size / 2, z + size / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(x - size / 2, y + size / 2, z + size / 2);

    // 后面
    glNormal3f(0.0f, 0.0f, -1.0f);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x - size / 2, y - size / 2, z - size / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(x - size / 2, y + size / 2, z - size / 2);

    // 左面
    glNormal3f(-1.0f, 0.0f, 0.0f);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x - size / 2, y + size / 2, z + size / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(x - size / 2, y + size / 2, z - size / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x - size / 2, y - size / 2, z - size / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(x - size / 2, y - size / 2, z + size / 2);

    // 右面
    glNormal3f(1.0f, 0.0f, 0.0f);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x + size / 2, y + size / 2, z + size / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(x + size / 2, y - size / 2, z + size / 2);

    // 上面
    glNormal3f(0.0f, 1.0f, 0.0f);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(x - size / 2, y + size / 2, z + size / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + size / 2, y + size / 2, z + size / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(x + size / 2, y + size / 2, z - size / 2);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x - size / 2, y + size / 2, z - size / 2);

    // 下面
    glNormal3f(0.0f, -1.0f, 0.0f);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(x - size / 2, y - size / 2, z + size / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + size / 2, y - size / 2, z + size / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(x + size / 2, y - size / 2, z - size / 2);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x - size / 2, y - size / 2, z - size / 2);

    glEnd();
    glDisable(GL_TEXTURE_2D);
}

void drawCone(float x, float y, float z, float baseRadius, float height, int slices, GLint texture) {
    float angleStep = 2.0f * PI / slices;

    glPushMatrix();
    glTranslatef(x, y, z);

    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, texture);

    // 绘制圆锥表面
    glBegin(GL_TRIANGLES);
    for (int i = 0; i < slices; i++) {
        float angle = i * angleStep;
        float nextAngle = (i + 1) * angleStep;

        // 顶点
        glNormal3f(0.0f, height, 0.0f); // 顶点法线
        glTexCoord2f(0.5f, 1.0f);
        glVertex3f(0.0f, height, 0.0f);

        // 边上第一个点
        glNormal3f(cos(angle), 0.0f, sin(angle)); // 边法线
        glTexCoord2f((float)i / slices, 0.0f);
        glVertex3f(baseRadius * cos(angle), 0.0f, baseRadius * sin(angle));

        // 边上第二个点
        glNormal3f(cos(nextAngle), 0.0f, sin(nextAngle));
        glTexCoord2f((float)(i + 1) / slices, 0.0f);
        glVertex3f(baseRadius * cos(nextAngle), 0.0f, baseRadius * sin(nextAngle));
    }
    glEnd();

    glDisable(GL_TEXTURE_2D);
    glPopMatrix();
}




// 绘制圆柱体
void drawCylinder(float x, float y, float z, float radius, float height, int slices, GLint texture) {
    float angleStep = 2.0f * PI / slices;

    glPushMatrix();
    glTranslatef(x, y, z);

    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, texture);

    // 绘制侧面
    glBegin(GL_QUAD_STRIP);
    for (int i = 0; i <= slices; i++) {
        float angle = i * angleStep;
        float nx = cos(angle);
        float nz = sin(angle);
        float u = (float)i / slices; // 纹理 U 坐标

        glNormal3f(nx, 0.0f, nz); // 法线
        glTexCoord2f(u, 0.0f); // 纹理底部
        glVertex3f(radius * nx, 0.0f, radius * nz); // 底面

        glTexCoord2f(u, 1.0f); // 纹理顶部
        glVertex3f(radius * nx, height, radius * nz); // 顶面
    }
    glEnd();

    // 绘制底面
    glBegin(GL_TRIANGLE_FAN);
    glNormal3f(0.0f, -1.0f, 0.0f); // 法线向下
    glTexCoord2f(0.5f, 0.5f); // 圆心纹理坐标
    glVertex3f(0.0f, 0.0f, 0.0f); // 圆心
    for (int i = 0; i <= slices; i++) {
        float angle = i * angleStep;
        float u = 0.5f + 0.5f * cos(angle); // 极坐标 U
        float v = 0.5f + 0.5f * sin(angle); // 极坐标 V
        glTexCoord2f(u, v);
        glVertex3f(radius * cos(angle), 0.0f, radius * sin(angle));
    }
    glEnd();

    // 绘制顶面
    glBegin(GL_TRIANGLE_FAN);
    glNormal3f(0.0f, 1.0f, 0.0f); // 法线向上
    glTexCoord2f(0.5f, 0.5f); // 圆心纹理坐标
    glVertex3f(0.0f, height, 0.0f); // 圆心
    for (int i = 0; i <= slices; i++) {
        float angle = i * angleStep;
        float u = 0.5f + 0.5f * cos(angle); // 极坐标 U
        float v = 0.5f + 0.5f * sin(angle); // 极坐标 V
        glTexCoord2f(u, v);
        glVertex3f(radius * cos(angle), height, radius * sin(angle));
    }
    glEnd();

    glDisable(GL_TEXTURE_2D);
    glPopMatrix();
}

// 绘制长方体 width x, height y,depth z
void drawCuboid(float x, float y, float z, float width, float height, float depth, GLuint texture) {
    glPushMatrix();
    glTranslatef(x, y, z);

    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, texture);

    glBegin(GL_QUADS);

    // 前面
    glNormal3f(0.0f, 0.0f, 1.0f); // 法线
    glTexCoord2f(0.0f, 0.0f); glVertex3f(-width / 2, -height / 2, depth / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(width / 2, -height / 2, depth / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(width / 2, height / 2, depth / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(-width / 2, height / 2, depth / 2);

    // 后面
    glNormal3f(0.0f, 0.0f, -1.0f);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(-width / 2, -height / 2, -depth / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(width / 2, -height / 2, -depth / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(width / 2, height / 2, -depth / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(-width / 2, height / 2, -depth / 2);

    // 左面
    glNormal3f(-1.0f, 0.0f, 0.0f);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(-width / 2, -height / 2, -depth / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(-width / 2, -height / 2, depth / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(-width / 2, height / 2, depth / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(-width / 2, height / 2, -depth / 2);

    // 右面
    glNormal3f(1.0f, 0.0f, 0.0f);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(width / 2, -height / 2, -depth / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(width / 2, -height / 2, depth / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(width / 2, height / 2, depth / 2);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(width / 2, height / 2, -depth / 2);

    // 上面
    glNormal3f(0.0f, 1.0f, 0.0f);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(-width / 2, height / 2, -depth / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(width / 2, height / 2, -depth / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(width / 2, height / 2, depth / 2);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(-width / 2, height / 2, depth / 2);

    // 下面
    glNormal3f(0.0f, -1.0f, 0.0f);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(-width / 2, -height / 2, -depth / 2);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(width / 2, -height / 2, -depth / 2);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(width / 2, -height / 2, depth / 2);
    glTexCoord2f(0.0f, 0.0f); glVertex3f(-width / 2, -height / 2, depth / 2);

    glEnd();

    glDisable(GL_TEXTURE_2D);
    glPopMatrix();
}


// 绘制半球体
void drawHemisphere(float x, float y, float z, float radius, int slices, int stacks, GLint texture) {
    float stackStep = PI / 2.0f / stacks;  // 半球体的纬度步长
    float sliceStep = 2.0f * PI / slices;  // 半球体的经度步长

    glPushMatrix();
    glTranslatef(x, y, z);    // 将半球移动到指定位置
    glRotatef(90.0f, 1.0f, 0.0f, 0.0f);   // 旋转 -90 度，使底面朝向 -z 轴

    glBegin(GL_TRIANGLES);
    for (int i = 0; i < stacks; i++) {
        float phi = i * stackStep;         // 当前纬度角
        float nextPhi = (i + 1) * stackStep; // 下一纬度角

        for (int j = 0; j < slices; j++) {
            float theta = j * sliceStep;         // 当前经度角
            float nextTheta = (j + 1) * sliceStep; // 下一经度角

            // 当前纬度圈上的点
            float x1 = radius * sin(phi) * cos(theta);
            float y1 = radius * cos(phi);
            float z1 = radius * sin(phi) * sin(theta);

            float x2 = radius * sin(phi) * cos(nextTheta);
            float y2 = radius * cos(phi);
            float z2 = radius * sin(phi) * sin(nextTheta);

            // 下一纬度圈上的点
            float x3 = radius * sin(nextPhi) * cos(theta);
            float y3 = radius * cos(nextPhi);
            float z3 = radius * sin(nextPhi) * sin(theta);

            float x4 = radius * sin(nextPhi) * cos(nextTheta);
            float y4 = radius * cos(nextPhi);
            float z4 = radius * sin(nextPhi) * sin(nextTheta);

            // 法线计算（向量归一化）
            float nx1 = x1 / radius, ny1 = y1 / radius, nz1 = z1 / radius;
            float nx2 = x2 / radius, ny2 = y2 / radius, nz2 = z2 / radius;
            float nx3 = x3 / radius, ny3 = y3 / radius, nz3 = z3 / radius;
            float nx4 = x4 / radius, ny4 = y4 / radius, nz4 = z4 / radius;

            // 纹理坐标计算
            float u1 = theta / (2.0f * PI);
            float v1 = phi / (PI / 2.0f);

            float u2 = nextTheta / (2.0f * PI);
            float v2 = phi / (PI / 2.0f);

            float u3 = theta / (2.0f * PI);
            float v3 = nextPhi / (PI / 2.0f);

            float u4 = nextTheta / (2.0f * PI);
            float v4 = nextPhi / (PI / 2.0f);

            // 绘制两个三角形组成的矩形面
            glNormal3f(nx1, ny1, nz1); glTexCoord2f(u1, v1); glVertex3f(x1, y1, z1); // 三角形1
            glNormal3f(nx3, ny3, nz3); glTexCoord2f(u3, v3); glVertex3f(x3, y3, z3);
            glNormal3f(nx2, ny2, nz2); glTexCoord2f(u2, v2); glVertex3f(x2, y2, z2);

            glNormal3f(nx2, ny2, nz2); glTexCoord2f(u2, v2); glVertex3f(x2, y2, z2); // 三角形2
            glNormal3f(nx3, ny3, nz3); glTexCoord2f(u3, v3); glVertex3f(x3, y3, z3);
            glNormal3f(nx4, ny4, nz4); glTexCoord2f(u4, v4); glVertex3f(x4, y4, z4);
        }
    }
    glEnd();

    glPopMatrix();

    glDisable(GL_TEXTURE_2D);
}

//width x, height y,depth z; x ,y,z底部左下角坐标
void drawTriangularPyramid(float x, float y, float z, float width, float height, float depth, float apexX, float apexY, float apexZ, GLint texture) {
    glEnable(GL_TEXTURE_2D);
    glBindTexture(GL_TEXTURE_2D, texture);
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);

    glBegin(GL_TRIANGLES); // 使用三角形来绘制三棱锥

    // 底面（矩形）
    glNormal3f(0.0f, 0.0f, 1.0f); // 底面的法线指向Z轴正方向
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x, y, z);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(x + width, y, z);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + width, y + height, z);

    glTexCoord2f(0.0f, 0.0f); glVertex3f(x, y, z);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + width, y + height, z);
    glTexCoord2f(0.0f, 1.0f); glVertex3f(x, y + height, z);

    // 侧面1（从底面x=0的边到顶点）
    glNormal3f(-1.0f, 0.0f, 0.0f); // 侧面1的法线指向X轴负方向
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x, y, z);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(apexX, apexY, apexZ);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x, y + height, z);

    // 侧面2（从底面x=width的边到顶点）
    glNormal3f(1.0f, 0.0f, 0.0f); // 侧面2的法线指向X轴正方向
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x + width, y, z);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(apexX, apexY, apexZ);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + width, y + height, z);

    // 侧面3（从底面y=depth的边到顶点）
    glNormal3f(0.0f, -1.0f, 0.0f); // 侧面3的法线指向Y轴负方向
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x + width, y + height, z);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(apexX, apexY, apexZ);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x, y + height, z);

    // 侧面4（从底面y=0的边到顶点）
    glNormal3f(0.0f, 1.0f, 0.0f); // 侧面4的法线指向Y轴正方向
    glTexCoord2f(0.0f, 0.0f); glVertex3f(x, y, z);
    glTexCoord2f(1.0f, 0.0f); glVertex3f(apexX, apexY, apexZ);
    glTexCoord2f(1.0f, 1.0f); glVertex3f(x + width, y, z);

    glEnd();
    glDisable(GL_TEXTURE_2D);
}

//############################## 环境 ########################
// 地面
void drawGround(float x, float y, float z, float width, float height, float depth)
{
    static GLuint texture = 0; // 静态变量，只加载一次
    if (texture == 0) {
        texture = loadTexture("./images/OIP.jpg");
        if (!texture) {
            printf("地面纹理加载失败\n");
            return;
        }
    }

    glPushMatrix();
    drawCuboid(x, y, z, width, height, depth, texture);
    glPopMatrix();
}


// ######################    物体    #######################

// 箱子
// x,y,z位置函数，size为正方体箱子大小，直接调整size可实现缩放
void Objects::Box(float x, float y, float z, float size) {
    // 绑定纹理
    static GLuint texture = 0; // 静态变量，只加载一次
    if (texture == 0) {
        texture = loadTexture("./images/box.jpg");
        if (!texture) {
            printf("箱子纹理加载失败\n");
            return;
        }
    }

    glPushMatrix();
    glColor3f(1.0, 1.0, 1.0);
    drawCube(x, y, z, size, texture);
    glPopMatrix();

}

//绘制房子：多个立方体和长方体交叠
void Objects::House1(float x, float y, float z, float size) {
    // 绑定纹理
    static GLuint texture = 0; // 静态变量，只加载一次
    if (texture == 0) {
        texture = loadTexture("./images/house_2.jpg");
        if (!texture) {
            printf("房子纹理加载失败\n");
            return;
        }
    }
    // 绑定纹理
    static GLuint texture2 = 0; // 静态变量，只加载一次
    if (texture2 == 0) {
        texture2 = loadTexture("./images/house_1.jpg");
        if (!texture2) {
            printf("房子纹理加载失败\n");
            return;
        }
    }
    glPushMatrix();
    glColor3f(1.0, 1.0, 1.0);
    drawCube(x, y, z, size, texture);
    drawCuboid(x, y, z + size / 2 + size / 20, size + size / 10, size + size / 10, size / 10, texture2);
    drawCube(x, y, z + size + size / 10, size, texture);
    glPopMatrix();

}

//绘制房子：多个立方体和长方体交叠
void Objects::House2(float x, float y, float z, float size) {
    // 绑定纹理
    static GLuint texture = 0; // 静态变量，只加载一次
    if (texture == 0) {
        texture = loadTexture("./images/house_3.jpg");
        if (!texture) {
            printf("房子纹理加载失败\n");
            return;
        }
    }
    // 绑定纹理
    static GLuint texture2 = 0; // 静态变量，只加载一次
    if (texture2 == 0) {
        texture2 = loadTexture("./images/house_1.jpg");
        if (!texture2) {
            printf("房子纹理加载失败\n");
            return;
        }
    }
    glPushMatrix();
    glColor3f(1.0, 1.0, 1.0);
    drawCube(x, y, z, size, texture);
    drawCuboid(x, y, z + size / 2 + size / 20, size + size / 10, size + size / 10, size / 10, texture2);
    drawCube(x, y, z + size + size / 10, size, texture);
    glPopMatrix();

}

//绘制房子：三棱锥+立方体
void Objects::House3(float x, float y, float z, float width, float height, float depth) {
    // 绑定纹理
    static GLuint texture = 0; // 静态变量，只加载一次
    if (texture == 0) {
        texture = loadTexture("./images/house_5.jpg");
        if (!texture) {
            printf("房子纹理加载失败\n");
            return;
        }
    }
    // 绑定纹理
    static GLuint texture2 = 0; // 静态变量，只加载一次
    if (texture2 == 0) {
        texture2 = loadTexture("./images/house_4.jpg");
        if (!texture2) {
            printf("房子纹理加载失败\n");
            return;
        }
    }
    glPushMatrix();
    glColor3f(1.0, 1.0, 1.0);
    drawCuboid(x, y, z, width, height, depth, texture);
    drawTriangularPyramid(x - width / 2, y - height / 2, z + depth / 2, width, height, depth / 4, x, y, z + depth, texture2);
    glPopMatrix();
}

// 锥形路障
// 位置 (x, y, z) 和缩放比例 scale
void Objects::ConeRoadblock(float x, float y, float z, float scale) {
    static GLuint texture = 0; // 静态变量，只加载一次
    if (texture == 0) {
        texture = loadTexture("./images/cone.png");
        if (!texture) {
            printf("锥形路障纹理加载失败\n");
            return;
        }
    }

    glPushMatrix();
    glColor3f(1.0, 1.0, 1.0);
    glTranslatef(x, y, z);
    glScalef(scale, scale, scale); // 按比例缩放
    glRotated(90.0f, 1.0, 0.0, 0.0);

    drawCone(0, 0, 0, 1.6f, 5.6f, 30, texture); // 顶部圆锥

    glColor3f(0.0, 0.0, 0.0);
    drawCylinder(0, 0, 0, 1.8, 0.2, 30, 0); // 底部圆柱

    glPopMatrix();

}



// 交通灯
// 位置x,y,z , 缩放scale
void Objects::TrafficLight(float x, float y, float z, float scale) {
    glPushMatrix();
    glTranslatef(x, y, z);
    glScalef(scale, scale, scale);
    glRotated(90.0f, 1.0, 0.0, 0.0);

    ////  启用光照
    //glEnable(GL_LIGHTING);
    //glEnable(GL_LIGHT0);
    //glEnable(GL_COLOR_MATERIAL);   // 启用颜色材质
    //glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE); // 设置颜色控制的材质属性

    glColor3f(0.0, 0.0, 0.0);
    drawCylinder(0.0f, 0.0f, 0.0f, 0.5f, 1.0f, 30, 0); // 底座
    drawCuboid(0.0f, 2.0f, 0.0f, 0.3f, 4.0f, 0.3f, 0); // 灯柱
    drawCuboid(0.0f, 5.0f, 0.0f, 1.3f, 2.0f, 0.8f, 0); // 灯箱

    // 绘制三盏灯（红、黄、绿）
     // 红灯
    glColor3f(1.0, 0.0, 0.0);
    drawHemisphere(0.0f, 5.6f, 0.4f, 0.3f, 30, 15, 0.0f);
    // 黄灯
    glColor3f(1.0, 1.0, 0.0);
    drawHemisphere(0.0f, 5.0f, 0.4f, 0.3f, 30, 15, 0.0f);
    // 绿灯
    glColor3f(0.0, 1.0, 0.0);
    drawHemisphere(0.0f, 4.4f, 0.4f, 0.3f, 30, 15, 0.0f);


    glPopMatrix();
}



// 绘制垃圾桶
void Objects::TrashCan(float x, float y, float z, float scale) {
    static GLuint texture = 0; // 静态变量，只加载一次
    if (texture == 0) {
        texture = loadTexture("./images/can.png");
        if (!texture) {
            printf("垃圾桶纹理加载失败\n");
            return;
        }
    }

    glPushMatrix();
    glTranslatef(x, y, z);
    glScalef(scale, scale, scale);
    glRotated(90.0f, 1.0, 0.0, 0.0);

    // 壁厚
    float wallThickness = 0.1f;

    // 前后墙
    glColor3f(0.2f, 0.6f, 0.3f); // 深绿色
    drawCuboid(0.0f, 1.0f, 0.9f, 1.5f, 2.3f, wallThickness, texture);  // 前墙
    drawCuboid(0.0f, 1.0f, -0.7f, 1.5f, 2.3f, wallThickness, 0); // 后墙

    // 左右墙
    drawCuboid(-0.8f, 1.0f, 0.15f, wallThickness, 2.3f, 1.6f, 0); // 左墙
    drawCuboid(0.8f, 1.0f, 0.15f, wallThickness, 2.3f, 1.6f, 0);  // 右墙

    // 突起边缘
    glColor3f(0.1f, 0.4f, 0.2f); // 更深的绿色
    float edgeHeight = 0.15f;     // 每一级突起的高度
    float edgeThickness = 0.1f;  // 每一级突起的厚度

    // 一级突起
    drawCuboid(0.0f, 2.2f, -0.7f, 1.7f, edgeHeight, edgeThickness, 0); // 后突起
    drawCuboid(0.0f, 2.2f, 1.0f, 1.8f, edgeHeight, edgeThickness, 0);  // 前突起
    drawCuboid(-0.9f, 2.2f, 0.1f, edgeThickness, edgeHeight, 1.8f, 0); // 左突起
    drawCuboid(0.9f, 2.2f, 0.1f, edgeThickness, edgeHeight, 1.8f, 0);  // 右突起

    // 二级突起
    drawCuboid(0.0f, 2.3f, -0.6f, 1.7f, edgeHeight, edgeThickness, 0); // 后突起
    drawCuboid(0.0f, 2.3f, 0.9f, 1.7f, edgeHeight, edgeThickness, 0);  // 前突起
    drawCuboid(-0.8f, 2.3f, 0.1f, edgeThickness, edgeHeight, 1.65f, 0); // 左突起
    drawCuboid(0.8f, 2.3f, 0.1f, edgeThickness, edgeHeight, 1.65f, 0);  // 右突起

    // 桶盖
    glColor3f(0.3f, 0.7f, 0.3f); // 浅绿色
    glPushMatrix();
    glTranslatef(0.0f, 1.4f, -1.0f); // 盖子放在后面
    glRotatef(110.0f, 1.0f, 0.0f, 0.0f); // 盖子向后旋转
    drawCuboid(0.0f, 0.0f, 0.0f, 1.7f, 0.05f, 1.7f, 0); // 盖子
    glPopMatrix();

    // 桶底
    glColor3f(0.1f, 0.3f, 0.1f); // 深绿色
    drawCuboid(0.0f, 0.0f, 0.1f, 1.6f, 0.1f, 1.5f, 0);

    glPopMatrix();
}