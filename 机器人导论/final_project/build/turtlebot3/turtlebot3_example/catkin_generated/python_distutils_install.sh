#!/bin/sh

if [ -n "$DESTDIR" ] ; then
    case $DESTDIR in
        /*) # ok
            ;;
        *)
            /bin/echo "DESTDIR argument must be absolute... "
            /bin/echo "otherwise python's distutils will bork things."
            exit 1
    esac
fi

echo_and_run() { echo "+ $@" ; "$@" ; }

echo_and_run cd "/home/cake/机器人导论/final_project/src/turtlebot3/turtlebot3_example"

# ensure that Python install destination exists
echo_and_run mkdir -p "$DESTDIR/home/cake/机器人导论/final_project/install/lib/python3/dist-packages"

# Note that PYTHONPATH is pulled from the environment to support installing
# into one location when some dependencies were installed in another
# location, #123.
echo_and_run /usr/bin/env \
    PYTHONPATH="/home/cake/机器人导论/final_project/install/lib/python3/dist-packages:/home/cake/机器人导论/final_project/build/lib/python3/dist-packages:$PYTHONPATH" \
    CATKIN_BINARY_DIR="/home/cake/机器人导论/final_project/build" \
    "/usr/bin/python3" \
    "/home/cake/机器人导论/final_project/src/turtlebot3/turtlebot3_example/setup.py" \
     \
    build --build-base "/home/cake/机器人导论/final_project/build/turtlebot3/turtlebot3_example" \
    install \
    --root="${DESTDIR-/}" \
    --install-layout=deb --prefix="/home/cake/机器人导论/final_project/install" --install-scripts="/home/cake/机器人导论/final_project/install/bin"
