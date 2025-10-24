CXX = g++
CXXFLAGS = -O3 -Wall -shared -std=c++14 -fPIC
PYTHON_VERSION = python3
PYTHON_INCLUDES = $(shell $(PYTHON_VERSION) -m pybind11 --includes 2>/dev/null || echo "-I/usr/include/python3.13")
OPENCV_LIBS = $(shell pkg-config --libs opencv4 2>/dev/null || pkg-config --libs opencv 2>/dev/null || echo "-lopencv_core -lopencv_imgproc")
OPENCV_CFLAGS = $(shell pkg-config --cflags opencv4 2>/dev/null || pkg-config --cflags opencv 2>/dev/null || echo "")
FFMPEG_LIBS = $(shell pkg-config --libs libavformat libavcodec libavutil libswscale 2>/dev/null || echo "-lavformat -lavcodec -lavutil -lswscale")
FFMPEG_CFLAGS = $(shell pkg-config --cflags libavformat libavcodec libavutil libswscale 2>/dev/null || echo "")
RGA_LIBS = -lrga

TARGET = rtsp_module$(shell $(PYTHON_VERSION)-config --extension-suffix 2>/dev/null || echo ".so")
SOURCE = rtsp_module.cpp

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(PYTHON_INCLUDES) $(OPENCV_CFLAGS) $(FFMPEG_CFLAGS) $(SOURCE) -o $(TARGET) $(OPENCV_LIBS) $(FFMPEG_LIBS) $(RGA_LIBS)

clean:
	rm -f $(TARGET) *.so

.PHONY: all clean