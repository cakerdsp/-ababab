#include "myglwidget.h"



float X = 0;
float Y = 0;
float Z = 0;
int factor = 1;
int a = 0;
int b = 0;
int hhhhh = 0;
int dis = 500;

MyGLWidget::MyGLWidget(QWidget *parent)
	:QOpenGLWidget(parent),
	scene_id(0)
{
}

MyGLWidget::~MyGLWidget()
{

}

void MyGLWidget::initializeGL()
{
	glViewport(0, 0, width(), height());
	glClearColor(1.0f, 1.0f, 1.0f, 1.0f);
	glDisable(GL_DEPTH_TEST);
}

void MyGLWidget::paintGL()
{
	if (scene_id==0) {
		scene_0();
	}
	else if (scene_id == 1){
		scene_1();
	}
	else if (scene_id == 2) {
		scene_2();
	}
	else if (scene_id == 3) {
		scene_3();
	}
	else if (scene_id == 4) {
		scene_4();
	}

}

void MyGLWidget::resizeGL(int width, int height)
{
	glViewport(0, 0, width, height);
	update();
}

void MyGLWidget::keyPressEvent(QKeyEvent *e) {
	//Press 0 or 1 to switch the scene
	if (e->key() == Qt::Key_0) {
		scene_id = 0;
		update();
	}
	else if (e->key() == Qt::Key_1) {
		scene_id = 1;
		update();
	}
	else if (e->key() == Qt::Key_2) {
		scene_id = 2;
		update();
	}
	else if (e->key() == Qt::Key_3) {
		scene_id = 3;
		update();
	}
	else if (e->key() == Qt::Key_4) {
		scene_id = 4;
		update();
	}
	else if (e->key() == Qt::Key_R) {
		factor *= -1;
		update();
	}
	else if (e->key() == Qt::Key_X) {
		X += factor * 15;
		update();
	}
	else if (e->key() == Qt::Key_Y) {
		Y += factor * 15;
		update();
	}
	else if (e->key() == Qt::Key_Z) {
		Z += factor * 15;
		update();
	}
	else if (e->key() == Qt::Key_V) {
		a = (a + 1) % 2;
		update();
	}
	else if (e->key() == Qt::Key_T) {
		b = (b + 1) % 2;
		update();
	}
	else if (e->key() == Qt::Key_D) {
		dis += factor * 50;
		update();
	}

}

void MyGLWidget::scene_0()
{
	glClear(GL_COLOR_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0.0f, 100.0f, 0.0f, 100.0f, -1000.0f, 1000.0f);

	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	glTranslatef(50.0f, 50.0f, 0.0f);
	
	//draw a diagonal "I"
	glPushMatrix();
	glColor3f(0.839f, 0.153f, 0.157f);
	glRotatef(45.0f, 0.0f, 0.0f, 1.0f);
	glTranslatef(-2.5f, -22.5f, 0.0f);
	glBegin(GL_TRIANGLES);
	glVertex2f(0.0f, 0.0f);
	glVertex2f(5.0f, 0.0f);
	glVertex2f(0.0f, 45.0f);

	glVertex2f(5.0f, 0.0f);
	glVertex2f(0.0f, 45.0f);
	glVertex2f(5.0f, 45.0f);

	glEnd();
	glPopMatrix();	
}

void MyGLWidget::scene_1()
{
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	if (b == 0)
		glOrtho(0.0f, width(), 0.0f, height(), -1000.0f, 1000.0f);
	else
		gluPerspective(45.0f, width() / height(), 1.0f, 1000.0f);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	if (a == 0)
		gluLookAt(0.0f, 0.0f, dis,
			0.0f, 0.0f, 0.0f,
			0.0f, 1.0f, 0.0f);
	else
		gluLookAt(0.0f, 0.5 * dis, dis,
			0.0f, 0.0f, 0.0f,
			0.0f, 1.0f, 0.0f);
	glTranslatef(0.5 * width(), 0.5 * height(), 0.0f);

    //your implementation here, maybe you should write several glBegin
	glPushMatrix();
	//your implementation
	glColor3f(0.839f, 0.153f, 0.157f);
	glTranslatef(-100.0f, -50.0f, 0.0f);
	glBegin(GL_TRIANGLES);
	// 绘制C
	// 绘制上横线
	glVertex2f(-40.0f, 100.0f);
	glVertex2f(40.0f, 100.0f);
	glVertex2f(40.0f, 85.0f);

	glVertex2f(-40.0f, 85.0f);
	glVertex2f(-40.0f, 100.0f);
	glVertex2f(40.0f, 85.0f);

	// 绘制竖线
	glVertex2f(-40.0f, 85.0f);
	glVertex2f(-25.0f, 85.0f);
	glVertex2f(-40.0f, 15.0f);

	glVertex2f(-40.0f, 15.0f);
	glVertex2f(-25.0f, 85.0f);
	glVertex2f(-25.0f, 15.0f);

	// 绘制下横线
	glVertex2f(-40.0f, 0.0f);
	glVertex2f(40.0f, 15.0f);
	glVertex2f(40.0f, 0.0f);

	glVertex2f(-40.0f, 0.0f);
	glVertex2f(-40.0f, 15.0f);
	glVertex2f(40.0f, 15.0f);

	glEnd();
	glPopMatrix();

	glPushMatrix();
	glColor3f(0.839f, 0.153f, 0.157f);
	glTranslatef(0.0f, -50.0f, 0.0f);
	glBegin(GL_TRIANGLES);

	// 绘制A
	// 绘制左斜线
	// 保持宽度10 ，依照这个比例，斜边应该是27
	// 底部斜边宽度应该是11
	glVertex2f(-40.0f, 0.0f);
	glVertex2f(-29.0f, 0.0f);
	glVertex2f(0.0f, 73.0f);

	glVertex2f(0.0f, 73.0f);  
	glVertex2f(0.0f, 100.0f);
	glVertex2f(-40.0f, 0.0f);
	// 绘制右斜线
	glVertex2f(40.0f, 0.0f);
	glVertex2f(29.0f, 0.0f);
	glVertex2f(0.0f, 73.0f);

	glVertex2f(0.0f, 73.0f);
	glVertex2f(0.0f, 100.0f);
	glVertex2f(40.0f, 0.0f);

	// 绘制中间横线
	glVertex2f(13.0f, 42.0f);
	glVertex2f(-13.0f, 42.0f);
	glVertex2f(17.0f, 32.0f);

	glVertex2f(-17.0f, 32.0f);
	glVertex2f(17.0f, 32.0f);
	glVertex2f(-13.0f, 42.0f);

	glEnd();
	glPopMatrix();

	glPushMatrix();
	glColor3f(0.839f, 0.153f, 0.157f);
	glTranslatef(100.0f, -50.0f, 0.0f);
	glBegin(GL_TRIANGLES);
	// 绘制K
	// 绘制竖线
	glVertex2f(-40.0f, 0.0f);
	glVertex2f(-25.0f, 0.0f);
	glVertex2f(-40.0f, 100.0f);

	glVertex2f(-40.0f, 100.0f);
	glVertex2f(-25.0f, 100.0f);
	glVertex2f(-25.0f, 0.0f);

	// 绘制上斜线
	glVertex2f(40.0f, 100.0f);
	glVertex2f(23.0f, 100.0f);
	glVertex2f(-25.0f, 50.0f);

	glVertex2f(-8.0f, 50.0f);
	glVertex2f(40.0f, 100.0f);
	glVertex2f(-25.0f, 50.0f);

	// 绘制下斜线
	glVertex2f(40.0f, 0.0f);
	glVertex2f(23.0f, 0.0f);
	glVertex2f(-25.0f, 50.0f);

	glVertex2f(-8.0f, 50.0f);
	glVertex2f(40.0f, 0.0f);
	glVertex2f(-25.0f, 50.0f);


	glEnd();
	glPopMatrix();
	glPopMatrix();
}



void MyGLWidget::scene_2()
{
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0.0f, width(), 0.0f, height(), -1000.0f, 1000.0f);

	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	glTranslatef(0.5 * width(), 0.5 * height(), 0.0f);

	//your implementation here, maybe you should write several glBegin
	glPushMatrix();
	//your implementation
	glColor3f(0.039f, 0.153f, 0.157f);
	glTranslatef(-100.0f, -50.0f, 0.0f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C
	// 绘制上横线
	glVertex2f(40.0f, 100.0f);
	glVertex2f(40.0f, 85.0f);
	glVertex2f(-40.0f, 100.0f);
	glVertex2f(-25.0f, 85.0f);
	glVertex2f(-40.0f, 0.0f);
	glVertex2f(-25.0f, 15.0f);
	glVertex2f(40.0f, 0.0f);
	glVertex2f(40.0f, 15.0f);

	glEnd();
	glPopMatrix();



	glPushMatrix();
	glColor3f(0.039f, 0.153f, 0.157f);
	glTranslatef(0.0f, -50.0f, 0.0f);
	// 绘制A
	// 绘制左斜线
	// 保持宽度10 ，依照这个比例，斜边应该是27
	// 底部斜边宽度应该是11
	glBegin(GL_TRIANGLE_STRIP);

	glVertex2f(-40.0f, 0.0f);
	glVertex2f(-29.0f, 0.0f);
	glVertex2f(0.0f, 100.0f);
	glVertex2f(0.0f, 73.0f);
	glVertex2f(40.0f, 0.0f);
	glVertex2f(29.0f, 0.0f);

	glEnd();

	glBegin(GL_TRIANGLE_STRIP);
	glVertex2f(13.0f, 42.0f);
	glVertex2f(17.0f, 32.0f);
	glVertex2f(-13.0f, 42.0f);
	glVertex2f(-17.0f, 32.0f);
	glEnd();

	glPopMatrix();



	glPushMatrix();
	glColor3f(0.039f, 0.153f, 0.157f);
	glTranslatef(100.0f, -50.0f, 0.0f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制K
	// 绘制竖线
	glVertex2f(-25.0f, 100.0f);
	glVertex2f(-40.0f, 100.0f);
	glVertex2f(-25.0f, 0.0f);
	glVertex2f(-40.0f, 0.0f);
	glEnd();

	glBegin(GL_TRIANGLE_STRIP);
	glVertex2f(23.0f, 100.0f);
	glVertex2f(40.0f, 100.0f);
	glVertex2f(-25.0f, 50.0f);
	glVertex2f(-8.0f, 50.0f);
	glVertex2f(23.0f, 0.0f);
	glVertex2f(40.0f, 0.0f);
	glEnd();


	glPopMatrix();
	glPopMatrix();
}


void MyGLWidget::scene_3()
{
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	glOrtho(0.0f, width(), 0.0f, height(), -1000.0f, 1000.0f);

	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	glTranslatef(0.5 * width(), 0.5 * height(), 0.0f);

	//your implementation here, maybe you should write several glBegin
	glPushMatrix();
	//your implementation
	glColor3f(0.139f, 0.153f, 0.657f);
	glTranslatef(-100.0f, -50.0f, 0.0f);
	glBegin(GL_QUAD_STRIP);
	// 绘制C
	// 绘制上横线
	glVertex2f(40.0f, 100.0f);
	glVertex2f(40.0f, 85.0f);
	glVertex2f(-40.0f, 100.0f);
	glVertex2f(-25.0f, 85.0f);
	glVertex2f(-40.0f, 0.0f);
	glVertex2f(-25.0f, 15.0f);
	glVertex2f(40.0f, 0.0f);
	glVertex2f(40.0f, 15.0f);

	glEnd();
	glPopMatrix();



	glPushMatrix();
	glColor3f(0.139f, 0.153f, 0.657f);
	glTranslatef(0.0f, -50.0f, 0.0f);
	// 绘制A
	// 绘制左斜线
	// 保持宽度10 ，依照这个比例，斜边应该是27
	// 底部斜边宽度应该是11
	glBegin(GL_QUAD_STRIP);

	glVertex2f(-40.0f, 0.0f);
	glVertex2f(-29.0f, 0.0f);
	glVertex2f(0.0f, 100.0f);
	glVertex2f(0.0f, 73.0f);
	glVertex2f(40.0f, 0.0f);
	glVertex2f(29.0f, 0.0f);

	glEnd();

	glBegin(GL_QUAD_STRIP);
	glVertex2f(13.0f, 42.0f);
	glVertex2f(17.0f, 32.0f);
	glVertex2f(-13.0f, 42.0f);
	glVertex2f(-17.0f, 32.0f);
	glEnd();

	glPopMatrix();



	glPushMatrix();
	glColor3f(0.139f, 0.153f, 0.657f);
	glTranslatef(100.0f, -50.0f, 0.0f);
	glBegin(GL_QUAD_STRIP);
	// 绘制K
	// 绘制竖线
	glVertex2f(-25.0f, 100.0f);
	glVertex2f(-40.0f, 100.0f);
	glVertex2f(-25.0f, 0.0f);
	glVertex2f(-40.0f, 0.0f);
	glEnd();

	glBegin(GL_QUAD_STRIP);
	glVertex2f(23.0f, 100.0f);
	glVertex2f(40.0f, 100.0f);
	glVertex2f(-25.0f, 50.0f);
	glVertex2f(-8.0f, 50.0f);
	glVertex2f(23.0f, 0.0f);
	glVertex2f(40.0f, 0.0f);
	glEnd();


	glPopMatrix();
	glPopMatrix();
}

void MyGLWidget::scene_4()
{
	float d = 10.0f;
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluPerspective(45.0f, width() / height(), 1.0f, 1000.0f);

	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	gluLookAt(0.0f, 0.0f, 500.0f,
		0.0f, 0.0f, 0.0f,
		0.0f, 1.0f, 0.0f);

	glRotatef(Y, 0, 1, 0);
	glRotatef(X, 1, 0, 0);
	glRotatef(Z, 0, 0, 1);

	glEnable(GL_DEPTH_TEST);
	//your implementation here, maybe you should write several glBegin
	glPushMatrix();
	//your implementation
	glColor3f(0.839f, 0.153f, 0.157f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C前面
	glVertex3f(40.0f, 100.0f, d);
	glVertex3f(40.0f, 85.0f, d);
	glVertex3f(-40.0f, 100.0f, d);
	glVertex3f(-25.0f, 85.0f, d);
	glVertex3f(-40.0f, 0.0f, d);
	glVertex3f(-25.0f, 15.0f, d);
	glVertex3f(40.0f, 0.0f, d);
	glVertex3f(40.0f, 15.0f, d);

	glEnd();
	glPopMatrix();


	glPushMatrix();
	//your implementation
	glColor3f(0.839f, 0.839f, 0.157f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面
	glVertex3f(40.0f, 100.0f, -d);
	glVertex3f(40.0f, 85.0f, -d);
	glVertex3f(-40.0f, 100.0f, -d);
	glVertex3f(-25.0f, 85.0f, -d);
	glVertex3f(-40.0f, 0.0f, -d);
	glVertex3f(-25.0f, 15.0f, -d);
	glVertex3f(40.0f, 0.0f, -d);
	glVertex3f(40.0f, 15.0f, -d);

	glEnd();
	glPopMatrix();


	glPushMatrix();
	//your implementation
	glColor3f(0.839f, 0.439f, 0.157f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面
	glVertex3f(40.0f, 100.0f, -d);
	glVertex3f(40.0f, 85.0f, -d);
	glVertex3f(40.0f, 100.0f, d);
	glVertex3f(40.0f, 85.0f, d);
	glEnd();
	glPopMatrix();

	glPushMatrix();
	//your implementation
	glColor3f(0.439f, 0.439f, 0.157f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面
	glVertex3f(40.0f, 100.0f, -d);
	glVertex3f(-40.0f, 100.0f, -d);
	glVertex3f(40.0f, 100.0f, d);
	glVertex3f(-40.0f, 100.0f, d);
	glEnd();
	glPopMatrix();

	glPushMatrix();
	//your implementation
	glColor3f(0.439f, 0.439f, 0.457f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面
	glVertex3f(40.0f, 85.0f, d);
	glVertex3f(-25.0f, 85.0f, d);
	glVertex3f(40.0f, 85.0f, -d);
	glVertex3f(-25.0f, 85.0f, -d);
	glEnd();
	glPopMatrix();

	glPushMatrix();
	//your implementation
	glColor3f(0.439f, 0.339f, 0.457f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面

	glVertex3f(-25.0f, 85.0f, d);
	glVertex3f(-25.0f, 15.0f, d);
	glVertex3f(-25.0f, 85.0f, -d);
	glVertex3f(-25.0f, 15.0f, -d);
	glEnd();
	glPopMatrix();

	glPushMatrix();
	//your implementation
	glColor3f(0.439f, 0.339f, 0.457f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面

	glVertex3f(-25.0f, 15.0f, d);
	glVertex3f(-25.0f, 15.0f, -d);

	glVertex3f(40.0f, 15.0f, d);
	glVertex3f(40.0f, 15.0f, -d);
	glEnd();
	glPopMatrix();


	glPushMatrix();
	//your implementation
	glColor3f(0.039f, 0.339f, 0.57f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面


	glVertex3f(40.0f, 15.0f, d);
	glVertex3f(40.0f, 15.0f, -d);
	glVertex3f(40.0f, 0.0f, d);
	glVertex3f(40.0f, 0.0f, -d);
	glEnd();
	glPopMatrix();


	glPushMatrix();
	//your implementation
	glColor3f(0.039f, 0.039f, 0.57f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面

	glVertex3f(40.0f, 0.0f, d);
	glVertex3f(40.0f, 0.0f, -d);

	glVertex3f(-40.0f, 0.0f, d);
	glVertex3f(-40.0f, 0.0f, -d);
	glEnd();
	glPopMatrix();


	glPushMatrix();
	//your implementation
	glColor3f(0.039f, 0.39f, 0.057f);
	glBegin(GL_TRIANGLE_STRIP);
	// 绘制C后面

	glVertex3f(-40.0f, 0.0f, d);
	glVertex3f(-40.0f, 0.0f, -d);

	glVertex3f(-40.0f, 100.0f, d);
	glVertex3f(-40.0f, 100.0f, -d);

	glEnd();
	glPopMatrix();

	glPopMatrix();
}