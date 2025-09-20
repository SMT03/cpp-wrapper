CXX = g++
CXXFLAGS = -O3 -Wall -shared -std=c++14 -fPIC
PYTHON_INCLUDES = $(shell python3 -m pybind11 --includes)
OPENCV_LIBS = $(shell pkg-config --libs opencv4)
OPENCV_CFLAGS = $(shell pkg-config --cflags opencv4)

TARGET = rtsp_module$(shell python3-config --extension-suffix)
SOURCE = rtsp_module.cpp

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) $(PYTHON_INCLUDES) $(OPENCV_CFLAGS) $(SOURCE) -o $(TARGET) $(OPENCV_LIBS)

clean:
	rm -f $(TARGET)

.PHONY: all clean