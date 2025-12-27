#pragma once
#ifndef OBJECT_H
#define OBJECT_H

#include <QApplication>
#include <GL/freeglut.h>
//#include <GL/glew.h>
#include<math.h>



// 纹理图片加载函数
GLuint loadTexture(const char* filename);


// 物体类
class Objects {
public:

	void Box(float x, float y, float z, float size); // 箱子,x,y,z位置函数，size为正方体箱子大小，直接调整size可实现缩放

	void ConeRoadblock(float x, float y, float z, float scale); // 圆锥路障，位置 (x, y, z) 和缩放比例 scale

	void TrafficLight(float x, float y, float z, float scale); // 红绿灯，位置 (x, y, z) 和缩放比例 scale

	void TrashCan(float x, float y, float z, float scale); // 垃圾桶，位置 (x, y, z) 和缩放比例 scale

	void House1(float x, float y, float z, float size);//渲染房子，位置(x,y,z)，size指房子底部正方形的大小
	
	void House2(float x, float y, float z, float size);//渲染房子，位置(x,y,z)，size指房子底部正方形的大小
	
	void House3(float x, float y, float z, float width, float height,float depth);//渲染房子，位置(x,y,z)，width指房子底部在x轴的长度，height指房子底部在y轴的长度，depth指在z轴的高度
};
//环境
// 地面
void drawGround(float x, float y, float z, float width = 100.0f, float height = 100.0f, float depth = 0.0f);


// 基本元，用于构建物体，请勿调用
void drawCube(float x, float y, float z, float size, GLint texture); // 正方体
void drawCone(float x, float y, float z, float baseRadius, float height, int slices, GLint texture); // 圆锥
void drawCylinder(float x, float y, float z, float radius, float height, int slices, GLint texture); // 圆柱
void drawCuboid(float x, float y, float z, float width, float height, float depth, GLuint texture); // 立方体
void drawHemisphere(float x, float y, float z, float radius, int slices, int stacks, GLint texture); // 半球
void drawTriangularPyramid(float x, float y, float z, float width, float height, float depth, float apexX, float apexY, float apexZ, GLint texture);//三棱锥，x,y,z是三棱锥底部的左下角坐标，apeX坐标指三棱锥顶部坐标，depth是z轴高度，width是x轴高度，height是y轴高度


#endif
