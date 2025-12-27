#ifndef MYGLWIDGET_H
#define MYGLWIDGET_H

#ifdef MAC_OS
#include <QtOpenGL/QtOpenGL>
#else
#include <GL/glew.h>
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <string>
#include <fstream>
#include <sstream>
#include <iostream>
#include <string>
#endif
#include <QtGui>
#include <QOpenGLWidget>
#include <QOpenGLFunctions>
#include "utils.h"

#define MAX_Z_BUFFER 99999999.0f
#define MIN_FLOAT 1e-10f

using namespace glm;

class MyGLWidget : public QOpenGLWidget {
    Q_OBJECT

public:
    MyGLWidget(QWidget* parent = nullptr);
    ~MyGLWidget();

protected:
    void initializeGL() override;
    void paintGL() override;
    void resizeGL(int width, int height) override;
    void keyPressEvent(QKeyEvent* e);

private:
    void scene_0();
    void scene_1();
    void drawTriangle(Triangle triangle);
    int edge_walking();
    void bresenham(FragmentAttr& start, FragmentAttr& end, int id);
    void DDA(FragmentAttr& start, FragmentAttr& end, int id);
    void clearBuffer(vec3* now_render_buffer);
    void clearBuffer(int* now_buffer);
    void clearZBuffer(float* now_buffer);
    void resizeBuffer(int newW, int newH);
    vec3 PhongShading(FragmentAttr& nowPixelResult);
    vec3 Blinn_PhongShading(FragmentAttr& nowPixelResult);

    int WindowSizeH = 0;
    int WindowSizeW = 0;
    int scene_id;
    int degree = 0;

    // buffers
    vec3* render_buffer;
    vec3* temp_render_buffer;
    float* temp_z_buffer;
    float* z_buffer;
    vec2 offset;

    std::vector<std::pair<int, std::vector<FragmentAttr>>> edges;

    Model objModel;

    vec3 camPosition;
    vec3 camLookAt;
    vec3 camUp;
    mat4 projMatrix;
    vec3 lightPosition;
    vec3 light_ambient = vec3(1.0f, 1.0f, 1.0f);
    vec3 light_diffuse = vec3(1.0f, 1.0f, 1.0f);
    vec3 light_specular = vec3(1.0f, 1.0f, 1.0f);
    vec3 objectColor = vec3(1.0f, 0.4f, 0.3f);
    vec3 lineColor = vec3(0.0f, 1.0f, 0.0f);

    float ambientfactor = 0.4f;
	float diffusefactor = 0.5f;
    float specularfactor = 3.0f;
    int a = 16;
    std:: string shade = "Blinn_Phong";
    std::string draw_line = "bresenham";
};

#endif // MYGLWIDGET_H
