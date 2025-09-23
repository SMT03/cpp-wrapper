#!/bin/bash
# Build script for Python 3.12

echo "Building RTSP Module for Python 3.12"
echo "===================================="

# Check if Python 3.12 is available
if ! command -v python3.12 &> /dev/null; then
    echo "Error: Python 3.12 not found"
    echo "Please install Python 3.12 first"
    exit 1
fi

# Install requirements
echo "Installing Python requirements..."
python3.12 -m pip install -r requirements.txt

# Build the module
echo "Building C++ module..."
CXX=g++
CXXFLAGS="-O3 -Wall -shared -std=c++14 -fPIC"
PYTHON_INCLUDES=$(python3.12 -m pybind11 --includes)
OPENCV_LIBS=$(pkg-config --libs opencv4)
OPENCV_CFLAGS=$(pkg-config --cflags opencv4)
TARGET="rtsp_module$(python3.12-config --extension-suffix)"
SOURCE="rtsp_module.cpp"

echo "Compiling with:"
echo "  CXX: $CXX"
echo "  Target: $TARGET"
echo "  Python includes: $PYTHON_INCLUDES"

$CXX $CXXFLAGS $PYTHON_INCLUDES $OPENCV_CFLAGS $SOURCE -o $TARGET $OPENCV_LIBS

if [ $? -eq 0 ]; then
    echo "✓ Build successful!"
    echo "Module created: $TARGET"
    
    # Test the module
    echo "Testing module import..."
    python3.12 -c "import rtsp_module; print('✓ Module import successful')"
    
    if [ $? -eq 0 ]; then
        echo "✓ Module is ready to use!"
        echo ""
        echo "Usage:"
        echo "  python3.12 main.py          # Full-featured example"
        echo "  python3.12 simple_example.py # Simple example"
    else
        echo "✗ Module import failed"
    fi
else
    echo "✗ Build failed!"
    exit 1
fi