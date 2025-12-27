* 环境：直接重新lab1的环境，然后从仓库里面拉取main.cpp,为了防止对环境的破坏，这里就不上传整个项目了，我已经搞坏一个了

* vs2022安装glut：https://blog.csdn.net/ntmbdwp302159902/article/details/139623118?fromshare=blogdetail&sharetype=blogdetail&sharerId=139623118&sharerefer=PC&sharesource=m0_73324094&sharefrom=from_link

  * 这里freeglut的插件有两个版本：不行就换另一个，可能不兼容
  * 最后提交大作业的时候，可能不能用这种方式安装freeglut，可能需要源码，然后打包在项目里面上交，但是先凑活一下，后面再研究

* dxq写的简易版小球走迷宫在example.cpp里面，主体框架参照小球走迷宫，但是代码需要写在main.cpp

* dxy同学：可以参照<code>void drawCube(float x, float y, float z, float size) </code>，定义不同的物体

* dxq同学：主要完成键盘回调函数<code> handleKeys(unsigned char key, int x, int y)</code>和摄像头位置的更新void <code>updateDirection(int moveDirection)</code> 和 小球绘制

*  cak同学：需要完成整体渲染，<code>void display()</code>，在函数中调用不同物体的绘制函数和小球绘制函数，渲染背景和增加光照

* 全局变量设置：有需要添加的全局参数，及时在群里交流，且更新readme.md

  * 在dxq的part而言，全局变量是小球的各项数据，和摄像头的参数变量，则需要用到小球参数和设置摄像头的地方请用全局参数，统一管理。如

    ```c++
    float ballX = 1.0f, ballY = 1.0f, ballZ = 0.0f; // 初始位置
    float AtX = ballX, AtY = ballY-1.5, AtZ = ballZ+1;//摄像机位置
    float targetX = 1, targetY = 10, targetZ = ballZ;//摄像机看向位置，要跟随小球的移动变化
    float ballRadius = 0.3f; // 小球半径
    const float stepSize = 0.2f; // 移动步长
    ```

    