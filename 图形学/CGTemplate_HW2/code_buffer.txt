#include "myglwidget.h"
#include <GL/glew.h>
#include <algorithm>
#include <iostream>
#include <chrono> 
#include <vector>

MyGLWidget::MyGLWidget(QWidget* parent)
	:QOpenGLWidget(parent)
{
}

MyGLWidget::~MyGLWidget()
{
	delete[] render_buffer;
	delete[] temp_render_buffer;
	delete[] temp_z_buffer;
	delete[] z_buffer;
}

void MyGLWidget::resizeBuffer(int newW, int newH) {
	delete[] render_buffer;
	delete[] temp_render_buffer;
	delete[] temp_z_buffer;
	delete[] z_buffer;
	WindowSizeW = newW;
	WindowSizeH = newH;
	render_buffer = new vec3[WindowSizeH * WindowSizeW];
	temp_render_buffer = new vec3[WindowSizeH * WindowSizeW];
	temp_z_buffer = new float[WindowSizeH * WindowSizeW];
	z_buffer = new float[WindowSizeH * WindowSizeW];
}

void MyGLWidget::initializeGL()
{

	// 获取窗口的大小
	WindowSizeW = width();
	WindowSizeH = height();
	// 设置 OpenGL 渲染的视口大小，从 (0, 0)（左下角）到窗口的宽高。所有的渲染操作都会映射到这个视口中。
	glViewport(0, 0, WindowSizeW, WindowSizeH);
	// 清屏颜色，这里是白色
	glClearColor(1.0f, 1.0f, 1.0f, 1.0f);

	// 禁用深度测试，这样的话，绘制的物体会直接覆盖先前的像素，后绘制的内容会覆盖前面的内容。
	glDisable(GL_DEPTH_TEST);

	// 记录窗口中心位置
	offset = vec2(WindowSizeH / 2, WindowSizeW / 2);
	// 对定义的数组初始化



	// 这里应该是为了实现双缓冲区机制而引入的
	// 存储当前渲染结果的颜色值，每个像素是一个 vec3（表示 RGB 三个颜色分量）。
	render_buffer = new vec3[WindowSizeH * WindowSizeW];

	// 临时渲染缓冲区，可能用于临时保存渲染数据，方便后续处理。
	temp_render_buffer = new vec3[WindowSizeH * WindowSizeW];

	// 存储每个像素的深度值（Z 值），用于深度测试，防止物体被错误覆盖。
	temp_z_buffer = new float[WindowSizeH * WindowSizeW];
	z_buffer = new float[WindowSizeH * WindowSizeW];
	for (int i = 0; i < WindowSizeH * WindowSizeW; i++) {
		// 初始化全部初始化为黑色
		render_buffer[i] = vec3(0, 0, 0);
		temp_render_buffer[i] = vec3(0, 0, 0);

		// 将深度值初始化为最大值 MAX_Z_BUFFER。MAX_Z_BUFFER 表示最远的深度（通常是一个很大的数），表示初始时所有像素点都没有被物体覆盖。
		temp_z_buffer[i] = MAX_Z_BUFFER;
		z_buffer[i] = MAX_Z_BUFFER;
	}
}

void MyGLWidget::keyPressEvent(QKeyEvent* e) {

	// 键盘0和1负责切换画面，键盘9负责旋转
	switch (e->key()) {
	case Qt::Key_W: scene_id = 0; update(); break;
	case Qt::Key_E: scene_id = 1; update(); break;
	case Qt::Key_Q: degree += 15; update(); break;
	}
}

void MyGLWidget::paintGL()
{
	auto start = std::chrono::high_resolution_clock::now();
	switch (scene_id) {
	case 0:scene_0(); break;
	case 1:scene_1(); break;
	}
	auto end = std::chrono::high_resolution_clock::now();
	auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
	std::cout << "Time taken: " << duration.count() << " ms" << std::endl;
}


// 将颜色缓冲区清空，重新设置成黑色
void MyGLWidget::clearBuffer(vec3* now_buffer) {
	for (int i = 0; i < WindowSizeH * WindowSizeW; i++) {
		now_buffer[i] = vec3(0, 0, 0);
	}
}

// 另一种清空方式，全部清零
void MyGLWidget::clearBuffer(int* now_buffer) {
	memset(now_buffer, 0, WindowSizeW * WindowSizeH * sizeof(int));
}


void MyGLWidget::clearZBuffer(float* now_buffer) {
	std::fill(now_buffer, now_buffer + WindowSizeW * WindowSizeH, MAX_Z_BUFFER);
}


// 窗口大小变动后，需要重新生成render_buffer等数组
void MyGLWidget::resizeGL(int w, int h)
{
	// 重新调整窗口大小，找中心点，清空颜色缓冲区
	resizeBuffer(w, h);
	offset = vec2(WindowSizeH / 2, WindowSizeW / 2);
	clearBuffer(render_buffer);
}





// render_buffer 是一个用于存储渲染过程中中间结果的缓冲区
void MyGLWidget::scene_0()
{
	// 选择要加载的model
	objModel.loadModel("./objs/singleTriangle.obj");

	// 自主设置变换矩阵
	// 这个摄像机的设置就是希望实现看向模型中心，通过控制degree来实现控制相机环绕模型的效果
	camPosition = vec3(100 * sin(degree * 3.14 / 180.0) + objModel.centralPoint.y, 100 * cos(degree * 3.14 / 180.0) + objModel.centralPoint.x, 10 + objModel.centralPoint.z);
	camLookAt = objModel.centralPoint;     // 例如，看向物体中心
	camUp = vec3(0, 1, 0);         // 上方向向量，模型是在xz平面上咯

	// 设置投影
	projMatrix = glm::perspective(radians(20.0f), 1.0f, 0.1f, 2000.0f);

	// 单一点光源，可以改为数组实现多光源，在上方100，再往y正方向推100的方向上
	lightPosition = objModel.centralPoint + vec3(0, 100, 100);
	// 清除之前的颜色和深度缓冲区
	clearBuffer(render_buffer);
	clearZBuffer(z_buffer);

	// 绘制模型,绘制到render_buffer中
	for (int i = 0; i < objModel.triangleCount; i++) {
		Triangle nowTriangle = objModel.getTriangleByID(i);
		drawTriangle(nowTriangle);
	}
	// 清除 OpenGL 的颜色缓冲区，准备进行绘制。
	glClear(GL_COLOR_BUFFER_BIT);
	// 使用 render_buffer 中的渲染结果，并将其显示到屏幕窗口上
	renderWithTexture(render_buffer, WindowSizeH, WindowSizeW);
}

// 同上
void MyGLWidget::scene_1()
{
	// 选择要加载的model
	objModel.loadModel("./objs/teapot_600.obj");
	//objModel.loadModel("./objs/teapot_8000.obj");
	//objModel.loadModel("./objs/rock.obj");
	//objModel.loadModel("./objs/cube.obj");
	//objModel.loadModel("./objs/singleTriangle.obj");

	// 自主设置变换矩阵
	camPosition = vec3(100 * sin(degree * 3.14 / 180.0) + objModel.centralPoint.y, 100 * cos(degree * 3.14 / 180.0) + objModel.centralPoint.x, 10 + objModel.centralPoint.z);
	camLookAt = objModel.centralPoint;     // 例如，看向物体中心
	camUp = vec3(0, 1, 0);         // 上方向向量
	projMatrix = glm::perspective(radians(20.0f), 1.0f, 0.1f, 2000.0f);

	// 单一点光源，可以改为数组实现多光源
	lightPosition = objModel.centralPoint + vec3(0, 100, 100);
	clearBuffer(render_buffer);
	clearZBuffer(z_buffer);
	for (int i = 0; i < objModel.triangleCount; i++) {
		Triangle nowTriangle = objModel.getTriangleByID(i);
		drawTriangle(nowTriangle);
	}
	glClear(GL_COLOR_BUFFER_BIT);
	renderWithTexture(render_buffer, WindowSizeH, WindowSizeW);
}

void MyGLWidget::drawTriangle(Triangle triangle) {
	// 三维顶点映射到二维平面

	// vertices存三个顶点
	vec3* vertices = triangle.triangleVertices;
	// normals存法向量
	vec3* normals = triangle.triangleNormals;

	//是一个长度为 3 的数组，准备用来存储三角形三个顶点变换后的坐标和属性。
	FragmentAttr transformedVertices[3];

	// 清缓冲区
	clearBuffer(this->temp_render_buffer);
	clearZBuffer(this->temp_z_buffer);

	// 设置并获取视图矩阵（从世界坐标系（或对象坐标系）变换到相机坐标系的矩阵）
	mat4 viewMatrix = glm::lookAt(camPosition, camLookAt, camUp);

	for (int i = 0; i < 3; ++i) {
		// 把顶点坐标拼接一个维度变成(x,y,z,1),然后与视图矩阵相乘，得到的ver_mv就是视图矩阵下的坐标
		vec4 ver_mv = viewMatrix * vec4(vertices[i], 1.0f);
		// 存储的是当前顶点的深度值，即从相机到顶点的距离。在渲染过程中，这个值通常用于深度测试，以确定哪些像素/片段在相机前面，哪些在相机后面，从而决定最终显示哪些物体。
		float nowz = glm::length(camPosition - vec3(ver_mv));
		// 从视图坐标系变换到投影坐标系
		vec4 ver_proj = projMatrix * ver_mv;

		// 以屏幕中心点为原点进行位置记录，这一步的作用是将投影后的顶点坐标从裁剪空间转换为屏幕空间坐标
		transformedVertices[i].x = ver_proj.x + offset.x;
		transformedVertices[i].y = ver_proj.y + offset.y;
		transformedVertices[i].z = nowz;

		// pos_mv本来就是记录片元在模型-视图变换坐标系中的坐标
		transformedVertices[i].pos_mv = ver_mv;



		/*
		这段代码的作用是将三角形顶点的法向量（normals[i]）从世界空间转换到视图空间，
		并将转换后的法向量保存到 transformedVertices[i].normal 中。

		从 4x4 的矩阵转换为 3x3 的矩阵，这样可以提取出只影响旋转和缩放的部分，而不包括平移信息。
		对于法向量的转换，我们只需要关心旋转和缩放，因此我们提取出 3x3 的矩阵，忽略了平移部分
		*/
		mat3 normalMatrix = mat3(viewMatrix);
		vec3 normal_mv = normalMatrix * normals[i];
		transformedVertices[i].normal = normal_mv;
		// 在顶点处计算颜色，用于Gouraud着色
		if(shade == "Blinn_Phong") {
			transformedVertices[i].color = Blinn_PhongShading(transformedVertices[i]);
		}
		else {
			transformedVertices[i].color = PhongShading(transformedVertices[i]);
		}
	}



	/* 前面的工作只是将顶点的有关信息存储在了transformedVertices中，没有存入缓冲区，
	   而后面的代码默认了数据已经存储在了缓冲区中，
	   那么中间的代码要做的就是把数据从transformedVertices转移到缓冲区
	   缓冲区是行优先存储的
	*/
	// 将当前三角形渲染在temp_buffer中


// HomeWork: 1、绘制三角形三边
	if (draw_line == "bresenham") {
		bresenham(transformedVertices[0], transformedVertices[1], 1);
		bresenham(transformedVertices[1], transformedVertices[2], 2);
		bresenham(transformedVertices[2], transformedVertices[0], 3);
	}
	else if (draw_line == "DDA") {
		DDA(transformedVertices[0], transformedVertices[1], 1);
		DDA(transformedVertices[1], transformedVertices[2], 2);
		DDA(transformedVertices[2], transformedVertices[0], 3);
	}


	// HomeWork: 2: 用edge-walking填充三角形内部到temp_buffer中
	int firstChangeLine = edge_walking();

	// 合并temp_buffer 到 render_buffer, 深度测试
	// 从firstChangeLine开始遍历，可以稍快
	for (int h = firstChangeLine; h < WindowSizeH; h++) {
		/*
		render_row, temp_render_row, z_buffer_row, 和 temp_z_buffer_row
		分别是指向 render_buffer、temp_render_buffer、z_buffer 和 temp_z_buffer 的当前行数据。
		*/
		auto render_row = &render_buffer[h * WindowSizeW];
		auto temp_render_row = &temp_render_buffer[h * WindowSizeW];
		auto z_buffer_row = &z_buffer[h * WindowSizeW];
		auto temp_z_buffer_row = &temp_z_buffer[h * WindowSizeW];


		for (int i = 0; i < WindowSizeW; i++) {
			/*
			如果 z_buffer_row[i] 小于 temp_z_buffer_row[i]，则表示 render_buffer 中的像素已经比 temp_buffer 中的像素距离相机更近，因此跳过更新。
			*/
			if (z_buffer_row[i] < temp_z_buffer_row[i])
				continue;
			else
			{
				/*
				*否则，更新 z_buffer_row[i] 为 temp_z_buffer_row[i]（新的深度值），并将 render_row[i] 更新为 temp_render_row[i]（新的颜色或像素值）。
				*/
				z_buffer_row[i] = temp_z_buffer_row[i];
				render_row[i] = temp_render_row[i];
			}
		}

	}
}

//由于画布的原因，需要计算
int MyGLWidget::edge_walking() {
	// 遍历edge_recorder在不同高度的起点、终点，用shading model计算内部每个像素的颜色
	int firstChangeLine = 0;
	// 对从DDA或者bresenham获取到的边表进行排序
	std::sort(edges.begin(), edges.end(), [](std::pair<int, std::vector<FragmentAttr>> a, std::pair<int, std::vector<FragmentAttr>> b) {
		return a.first > b.first;
		});

	if (!edges.empty()) {
		firstChangeLine = edges.back().first;  // 记录第一条非空行的行号
	}
	for (int i = 0; i < edges.size(); ++i) {
		std::sort(edges[i].second.begin(), edges[i].second.end(), [](FragmentAttr a, FragmentAttr b) {
			return a.x < b.x;
			});
		int y = edges[i].first;
		if (edges[i].second.size() > 1) {
			int k = 0;
			while (k + 1 < edges[i].second.size()) {
				int start_x = edges[i].second[k].x;
				int end_x = edges[i].second[k + 1].x;
				float start_z = edges[i].second[k].z;
				float end_z = edges[i].second[k + 1].z;
				float dz = (end_z - start_z) / float(end_x - start_x);
				for (int x = max(0, start_x + 1); x <= min(WindowSizeW, end_x - 1); ++x) {
					FragmentAttr tmp = getLinearInterpolation(edges[i].second[k], edges[i].second[k + 1], x, y);
					if (shade == "Phong") {
						temp_render_buffer[y * WindowSizeW + x] = PhongShading(tmp);
					}
					else if (shade == "Gouraud") {
						temp_render_buffer[y * WindowSizeW + x] = tmp.color;
					}
					else if (shade == "Blinn_Phong") {
						temp_render_buffer[y * WindowSizeW + x] = Blinn_PhongShading(tmp);
					}
					//temp_render_buffer[y * WindowSizeW + x] = vec3(1.0f, 1.0f, 1.0f);
					// 深度
					temp_z_buffer[y * WindowSizeW + x] = tmp.z;
				}
				++k;
			}
		}
	}

	edges.clear();
	return firstChangeLine;
}




vec3 MyGLWidget::PhongShading(FragmentAttr& nowPixelResult) {
	// 计算最终颜色
	vec3 norm = glm::normalize(nowPixelResult.normal);
	vec3 lightDir = glm::normalize(lightPosition - nowPixelResult.pos_mv);
	vec3 viewDir = glm::normalize(camPosition - nowPixelResult.pos_mv);
	vec3 reflectDir = glm::reflect(-lightDir, norm);

	vec3 ambient = ambientfactor* light_ambient;

	float diff = glm::max(glm::dot(norm, lightDir), 0.0f);
	vec3 diffuse = diffusefactor * diff * light_diffuse;

	float spec = glm::pow(glm::max(glm::dot(viewDir, reflectDir), 0.0f), a);
	vec3 specular = specularfactor * spec * light_specular;

	vec3 color = (ambient + diffuse + specular) * objectColor;
	return color;
}
vec3 MyGLWidget::Blinn_PhongShading(FragmentAttr& nowPixelResult) {
	// 计算最终颜色
	vec3 norm = glm::normalize(nowPixelResult.normal);
	vec3 lightDir = glm::normalize(lightPosition - nowPixelResult.pos_mv);
	vec3 viewDir = glm::normalize(camPosition - nowPixelResult.pos_mv);
	vec3 H = glm::normalize(lightDir + viewDir);

	vec3 ambient = ambientfactor * light_ambient;

	float diff = glm::max(glm::dot(norm, lightDir), 0.0f);
	vec3 diffuse = diffusefactor * diff * light_diffuse;

	float spec = glm::pow(glm::max(glm::dot(norm, H), 0.0f), a);
	vec3 specular = specularfactor * spec * light_specular;

	vec3 color = (ambient + diffuse + specular) * objectColor;
	return color;

}

void MyGLWidget::bresenham(FragmentAttr& start, FragmentAttr& end, int id) {
	//// 根据起点、终点，计算当前边在画布上的像素
	////（可以只考虑都在画布中。加分思考：在画布外怎么处理）
	//// 在PPT给出的算法伪代码的基础上考虑各个方向，各种情况后进行修改写成的。
	////printf("hhh ");
	int delta_x = end.x - start.x, delta_y = end.y - start.y;
	int dx = abs(delta_x);
	int dy = abs(delta_y);
	int dmin = min(dx, dy);
	int dmax = max(dx, dy);
	int signx = delta_x > 0 ? 1 : -1;
	int signy = delta_y > 0 ? 1 : -1;
	int p = 2 * dmin - dmax;
	int x = start.x;
	int y = start.y;
	int a = 2 * dmin;
	int b = 2 * dmin - 2 * dmax;
	// 思路很简单，dmax所在的维度在循环中总是会加1（或减1），这意味着dmax就是执行循环的次数，我现在只需要考虑z轴在dmax循环次数下如何从start.z到end.z即可
	/*float z = start.z;
	float dz = (end.z - start.z) / float(dmax);*/
	vec3 color = start.color;
	do {
		// 只需要填充x坐标就行
		FragmentAttr tmp = getLinearInterpolation(start, end, x, y);
		// 维护表，考虑了画布外的情况
		if (y < WindowSizeH && y >= 0) {
			auto it = std::find_if(edges.begin(), edges.end(), [&](std::pair<int, std::vector<FragmentAttr>> value) {
				return value.first == y; });
			if (it != edges.end()) {
				(*it).second.push_back(tmp);
			}
			else {
				edges.push_back({ y,{tmp} });
			}
		}


		if (x < WindowSizeW && x >= 0 && y < WindowSizeH && y >= 0) {
			if (shade == "Phong") {
				temp_render_buffer[y * WindowSizeW + x] = PhongShading(tmp);
			}
			else  if (shade == "Blinn_Phong") {
				temp_render_buffer[y * WindowSizeW + x] = Blinn_PhongShading(tmp);
			}
			else if (shade == "Gouraud") {
				temp_render_buffer[y * WindowSizeW + x] = tmp.color;
			}
			temp_z_buffer[y * WindowSizeW + x] = tmp.z;
		}
		// 更新
		if (p <= 0) {
			dmax == dx ? x += signx : y += signy;
			p += a;
		}
		else {
			x += signx;
			y += signy;
			p += b;
		}
		//z += dz;
	} while (x != end.x || y != end.y);

}


void MyGLWidget::DDA(FragmentAttr& start, FragmentAttr& end, int id) {
	//printf("hhh");
	float delta_x = end.x - start.x;
	float delta_y = end.y - start.y;
	int step = max(abs(delta_x), abs(delta_y));
	float dx = delta_x / step;
	float dy = delta_y / step;
	float x = start.x;
	float y = start.y;
	float z = start.z;
	float dz = (end.z - start.z) / step;
	vec3 color = start.color;
	// 缓冲区是行优先存储的
	for (int i = 0; i <= step; ++i) {
		int x_ = round(x);
		int y_ = round(y);
		// 维护表，考虑了画布外的情况
		FragmentAttr tmp = getLinearInterpolation(start, end, x_, y_);
		if (y_ < WindowSizeH && y_ >= 0) {
			auto it = std::find_if(edges.begin(), edges.end(), [&](std::pair<int, std::vector<FragmentAttr>> value) {
				return value.first == y_; });
			// 只需要填充x坐标就行
			if (it != edges.end()) {
				(*it).second.push_back(tmp);
			}
			else {
				edges.push_back({ y_,{tmp} });
			}
		}
		if (x_ < WindowSizeW && x_ >= 0 && y_ < WindowSizeH && y_ >= 0) {
			if (shade == "Phong") {
				temp_render_buffer[y_ * WindowSizeW + x_] = PhongShading(tmp);
			}
			else  if (shade == "Blinn_Phong") {
				temp_render_buffer[y_ * WindowSizeW + x_] = Blinn_PhongShading(tmp);
			}
			else if (shade == "Gouraud") {
				temp_render_buffer[y_ * WindowSizeW + x_] = tmp.color;
			}
			temp_z_buffer[y_ * WindowSizeW + x_] = tmp.z;
		}
		x += dx;
		y += dy;
		z += dz;
	}
}



