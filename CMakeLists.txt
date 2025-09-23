cmake_minimum_required(VERSION 3.12)
project(rtsp_module)

# Set C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(pybind11 REQUIRED)
find_package(OpenCV REQUIRED)
find_package(PkgConfig REQUIRED)

# Include directories
include_directories(${OpenCV_INCLUDE_DIRS})

# Create pybind11 module
pybind11_add_module(rtsp_module rtsp_module.cpp)

# Link libraries
target_link_libraries(rtsp_module PRIVATE ${OpenCV_LIBS})

# Compiler-specific options for pybind11
target_compile_definitions(rtsp_module PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})
add_library(rtsp_module MODULE rtsp_module.cpp)
target_link_libraries(rtsp_module PRIVATE pybind11::module ${OpenCV_LIBS})
set_target_properties(rtsp_module PROPERTIES PREFIX "" SUFFIX ".so")