#include "Terrain.h"
#include <stdexcept>

Terrain::Terrain(const std::string& heightmap, float x, float y, float z ,float scale,float hscale,float gap) : heightmap(heightmap),x(x),y(y),z(z),hscale(hscale),gap(gap) {
    loadHeightmap();
    generateVertices(scale);
}

Terrain::~Terrain() {
    delete[] vertices;
    if (heightmapData) {
        stbi_image_free(heightmapData);
    }
}



void Terrain::loadHeightmap() {
    heightmapData = stbi_load(heightmap.c_str(), &width, &height, &channels, 1);
    if (!heightmapData) {
        throw std::runtime_error("Failed to load heightmap image");
    }
}

void Terrain::generateVertices(float scale) {
    this->w = width / gap + 1;
    this->h = height / gap + 1;
    vertices = new float[w * h * 3];
    float grey;
    int h_ = 0, w_ = 0, i = 0;
    while(h_ <= height) {
        w_ = 0;
        while(w_<= width) {
            vertices[i++] = (float)(h_/gap) * scale; //x
            vertices[i++] = (float)(w_/gap) * scale; //y
            vertices[i++] = (float(heightmapData[(h_ * width + w_)]) / 255.0f) * hscale; //z
            w_ += gap;
        }
        h_ += gap;
    }
}


void Terrain::draw() {
     glPushMatrix();
     //glLoadIdentity();
     glTranslatef(x, y, z);
     glColor3f(1.0, 0.0, 1.0);
     glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
     for (int i = 0; i < h - 1; ++i) {
         for (int j = 0; j < w - 1; ++j) {
             glBegin(GL_TRIANGLE_STRIP);
             //第一个三角形
             glVertex3f(vertices[(i * w + j) * 3 + 0], vertices[(i * w + j) * 3 + 1], vertices[(i * w + j) * 3 + 2]);//第I 行j 列点                   
             glVertex3f(vertices[((i + 1) * w + j) * 3 + 0], vertices[((i + 1) * w + j) * 3 + 1], vertices[((i + 1) * w + j) * 3 + 2]);//第I＋1行j 列点              
             //glVertex3f(vertices[((i + 1) * w + (j + 1)) * 3 + 0], vertices[((i + 1) * w + (j + 1)) * 3 + 1], vertices[((i + 1) * w + (j + 1)) * 3 + 2]);//第I＋1行j＋1列点


             glVertex3f(vertices[((i) * w + (j + 1)) * 3 + 0], vertices[((i) * w + (j + 1)) * 3 + 1], vertices[((i) * w + (j + 1)) * 3 + 2]);//第I 行j＋1列点
             glVertex3f(vertices[((i + 1) * w + (j + 1)) * 3 + 0], vertices[((i + 1) * w + (j + 1)) * 3 + 1], vertices[((i + 1) * w + (j + 1)) * 3 + 2]);//第I＋1行j＋1列点   
             //glVertex3f(vertices[(i * w + j) * 3 + 0], vertices[(i * w + j) * 3 + 1], vertices[(i * w + j) * 3 + 2]);//第I 行j 列点

             glEnd();

         }
     }
     printf("hhh ");
     glPopMatrix(); 
}


//void Terrain::draw() {
//    glPushMatrix();
//    //glLoadIdentity();
//    glTranslatef(x, y, z);
//    glColor3f(1.0, 0.0, 1.0);
//    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
//    for (int i = 0; i < height - 1; ++i) {
//        for (int j = 0; j < width - 1; ++j) {
//            glBegin(GL_TRIANGLES);
//            //第一个三角形
//            glVertex3f(vertices[(i * width + j) * 3 + 0], vertices[(i * width + j) * 3 + 1], vertices[(i * width + j) * 3 + 2]);//第I 行j 列点                   
//            glVertex3f(vertices[((i + 1) * width + j) * 3 + 0], vertices[((i + 1) * width + j) * 3 + 1], vertices[((i + 1) * width + j) * 3 + 2]);//第I＋1行j 列点              
//            glVertex3f(vertices[((i + 1) * width + (j + 1)) * 3 + 0], vertices[((i + 1) * width + (j + 1)) * 3 + 1], vertices[((i + 1) * width + (j + 1)) * 3 + 2]);//第I＋1行j＋1列点
//
//
//            glVertex3f(vertices[((i + 1) * width + (j + 1)) * 3 + 0], vertices[((i + 1) * width + (j + 1)) * 3 + 1], vertices[((i + 1) * width + (j + 1)) * 3 + 2]);//第I＋1行j＋1列点        
//            glVertex3f(vertices[((i)*width + (j + 1)) * 3 + 0], vertices[((i)*width + (j + 1)) * 3 + 1], vertices[((i)*width + (j + 1)) * 3 + 2]);//第I 行j＋1列点
//
//            glVertex3f(vertices[(i * width + j) * 3 + 0], vertices[(i * width + j) * 3 + 1], vertices[(i * width + j) * 3 + 2]);//第I 行j 列点
//
//            glEnd();
//
//        }
//    }
//    printf("hhh ");
//    glPopMatrix();
//}