cmake_minimum_required(VERSION 3.12)
project(rtsp_module)

# Set C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Required packages
find_package(pybind11 REQUIRED)
find_package(OpenCV REQUIRED COMPONENTS core imgproc)
find_package(PkgConfig REQUIRED)

# FFmpeg libraries (required)
pkg_check_modules(AVFORMAT REQUIRED libavformat)
pkg_check_modules(AVCODEC REQUIRED libavcodec)
pkg_check_modules(AVUTIL REQUIRED libavutil)
pkg_check_modules(SWSCALE REQUIRED libswscale)

message(STATUS "FFmpeg libraries found")
add_definitions(-DHAVE_FFMPEG)

# RGA library for RK3588 hardware acceleration
find_library(RGA_LIB rga PATHS /usr/lib /usr/local/lib)
find_path(RGA_INCLUDE_DIR rga/rga.h PATHS /usr/include /usr/local/include)

if(RGA_LIB AND RGA_INCLUDE_DIR)
    message(STATUS "RGA library found: ${RGA_LIB}")
    add_definitions(-DHAVE_RGA)
    include_directories(${RGA_INCLUDE_DIR})
else()
    message(WARNING "RGA library not found. Hardware acceleration will be limited.")
endif()

include_directories(
    ${OpenCV_INCLUDE_DIRS}
    ${AVFORMAT_INCLUDE_DIRS}
    ${AVCODEC_INCLUDE_DIRS}
    ${AVUTIL_INCLUDE_DIRS}
    ${SWSCALE_INCLUDE_DIRS}
)

# Create pybind11 module
pybind11_add_module(rtsp_module rtsp_module.cpp)

# Link libraries
target_link_libraries(rtsp_module PRIVATE 
    ${OpenCV_LIBS}
    ${AVFORMAT_LIBRARIES}
    ${AVCODEC_LIBRARIES}
    ${AVUTIL_LIBRARIES}
    ${SWSCALE_LIBRARIES}
)

# Link RGA if available
if(RGA_LIB)
    target_link_libraries(rtsp_module PRIVATE ${RGA_LIB})
endif()

set_target_properties(rtsp_module PROPERTIES PREFIX "" SUFFIX ".so")