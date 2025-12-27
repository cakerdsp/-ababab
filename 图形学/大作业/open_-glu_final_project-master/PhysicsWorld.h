#pragma once

#include "btBulletDynamicsCommon.h"


// Bullet 物理世界相关


extern btDefaultCollisionConfiguration* collisionConfiguration;
extern btCollisionDispatcher* dispatcher;
extern btDbvtBroadphase* overlappingPairCache;
extern btSequentialImpulseConstraintSolver* solver;
extern btDiscreteDynamicsWorld* dynamicsWorld;