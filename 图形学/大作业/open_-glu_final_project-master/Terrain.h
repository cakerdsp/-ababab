#pragma once
#include <GL/glew.h>
#include <string>
#include "stb_image.h"

class Terrain {
public:
    explicit Terrain(const std::string& heightmap, float x = 1.0f, float y = 1.0f, float z = 1.0f, float scale = 10.0f,float hscale = 100,float gap = 10);
    ~Terrain();
    void draw();

private:
    void generateVertices(float scale);
    void loadHeightmap();

    float x;
    float y;
    float z;
    int width, height, channels;
    float* vertices = nullptr;
    int h ;
    int w ;
    int gap ;
    int hscale;
    std::string heightmap;
    unsigned char* heightmapData = nullptr;
};