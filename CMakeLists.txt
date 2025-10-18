cmake_minimum_required(VERSION 3.12)
project(rtsp_module)

target_link_libraries(rtsp_module PRIVATE ${OpenCV_LIBS})
target_compile_definitions(rtsp_module PRIVATE VERSION_INFO=${EXAMPLE_VERSION_INFO})
# Set C++ standard
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(USE_FFMPEG "Build with FFmpeg-based RTSP reader" ON)
option(USE_RKMPP "Enable Rockchip rkmpp/hwaccel hooks (requires user-provided headers/libs)" OFF)

find_package(pybind11 REQUIRED)
find_package(OpenCV REQUIRED)

find_package(PkgConfig REQUIRED)
if(USE_FFMPEG)
	pkg_check_modules(AVFORMAT libavformat QUIET)
	pkg_check_modules(AVCODEC libavcodec QUIET)
	pkg_check_modules(AVUTIL libavutil QUIET)
	pkg_check_modules(SWSCALE libswscale QUIET)
	if(AVFORMAT_FOUND AND AVCODEC_FOUND AND AVUTIL_FOUND AND SWSCALE_FOUND)
		message(STATUS "FFmpeg found via pkg-config")
		add_definitions(-DHAVE_FFMPEG)
		include_directories(${AVFORMAT_INCLUDE_DIRS} ${AVCODEC_INCLUDE_DIRS} ${AVUTIL_INCLUDE_DIRS} ${SWSCALE_INCLUDE_DIRS})
		link_libraries(${AVFORMAT_LIBRARIES} ${AVCODEC_LIBRARIES} ${AVUTIL_LIBRARIES} ${SWSCALE_LIBRARIES})
	else()
		message(WARNING "FFmpeg not found via pkg-config. Building without FFmpeg support.")
	endif()
endif()

if(USE_RKMPP)
	add_definitions(-DHAVE_RKMPP)
	# User should provide include/link paths for rkmpp and RGA if needed.
endif()

include_directories(${OpenCV_INCLUDE_DIRS})

# Create pybind11 module
pybind11_add_module(rtsp_module rtsp_module.cpp)

# Link OpenCV and (optionally) FFmpeg libs
target_link_libraries(rtsp_module PRIVATE ${OpenCV_LIBS})

# If pkg-config located FFmpeg libs, link them explicitly
if(AVFORMAT_FOUND)
	target_link_libraries(rtsp_module PRIVATE ${AVFORMAT_LIBRARIES} ${AVCODEC_LIBRARIES} ${AVUTIL_LIBRARIES} ${SWSCALE_LIBRARIES})
endif()

set_target_properties(rtsp_module PROPERTIES PREFIX "" SUFFIX ".so")