#!/bin/bash
# Build script for rtsp_module using virtual environment

set -e

# Activate virtual environment
source venv/bin/activate

# Get build flags
PYTHON_INCLUDES=$(python3 -m pybind11 --includes)
PYTHON_EXT=$(python3-config --extension-suffix)
OPENCV_LIBS="-lopencv_core -lopencv_imgproc"
OPENCV_CFLAGS=""
FFMPEG_LIBS=$(pkg-config --libs libavformat libavcodec libavutil libswscale 2>/dev/null || echo "-lavformat -lavcodec -lavutil -lswscale")
FFMPEG_CFLAGS=$(pkg-config --cflags libavformat libavcodec libavutil libswscale 2>/dev/null || echo "")
RGA_LIBS="-lrga"

TARGET="rtsp_module${PYTHON_EXT}"

echo "Building ${TARGET}..."
echo "Python includes: ${PYTHON_INCLUDES}"

# Build
g++ -O3 -Wall -shared -std=c++14 -fPIC \
    ${PYTHON_INCLUDES} \
    ${OPENCV_CFLAGS} \
    ${FFMPEG_CFLAGS} \
    rtsp_module.cpp \
    -o ${TARGET} \
    ${OPENCV_LIBS} \
    ${FFMPEG_LIBS} \
    ${RGA_LIBS}

echo "Build successful! Module: ${TARGET}"
ls -lh ${TARGET}
