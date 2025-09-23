# RTSP Stream Reader - C++ Python Extension

This project provides a Python interface to read RTSP video streams using OpenCV's C++ backend for high performance.

## Features

- Fast RTSP stream reading using OpenCV C++
- Automatic conversion between OpenCV Mat and NumPy arrays
- Zero-copy data transfer via buffer protocol
- Python 3.12 compatible

## Requirements

- Python 3.12
- OpenCV 4.x (with development headers)
- pybind11
- pkg-config

### Ubuntu/Debian Installation
```bash
# Install system dependencies
sudo apt update
sudo apt install python3.12 python3.12-dev python3.12-pip
sudo apt install libopencv-dev pkg-config

# Install Python packages
python3.12 -m pip install -r requirements.txt
```

## Building

### Option 1: Using the build script (recommended)
```bash
./build.sh
```

### Option 2: Using Make
```bash
make
```

### Option 3: Manual compilation
```bash
g++ -O3 -Wall -shared -std=c++14 -fPIC \
    $(python3.12 -m pybind11 --includes) \
    $(pkg-config --cflags opencv4) \
    rtsp_module.cpp \
    -o rtsp_module$(python3.12-config --extension-suffix) \
    $(pkg-config --libs opencv4)
```

## Usage

### Simple Example
```python
import rtsp_module
import numpy as np
import cv2

# Connect to RTSP stream
reader = rtsp_module.RTSPReader("rtsp://your-camera-ip:554/stream1")

# Read a frame
cv_frame = reader.read()
frame = np.array(cv_frame, copy=False)  # Convert to NumPy array

# Use the frame
print(f"Frame shape: {frame.shape}")
cv2.imwrite("frame.jpg", frame)

# Clean up
reader.release()
```

### Running the Examples

1. **Full-featured example:**
   ```bash
   python3.12 main.py
   ```
   Features:
   - Live stream viewer
   - Frame saving
   - FPS calculation
   - Keyboard controls

2. **Simple example:**
   ```bash
   python3.12 simple_example.py
   ```
   Features:
   - Basic frame capture
   - Live viewer option

### RTSP URL Examples

```python
# Basic RTSP URL
"rtsp://192.168.1.100:554/stream1"

# With authentication
"rtsp://username:password@192.168.1.100:554/stream1"

# Different stream paths
"rtsp://camera-ip:554/h264"
"rtsp://camera-ip:554/live/main"
```

## API Reference

### RTSPReader Class

#### Constructor
```python
reader = rtsp_module.RTSPReader(url: str)
```
- `url`: RTSP stream URL
- Throws exception if connection fails

#### Methods

**read() -> cv::Mat**
- Reads a single frame from the stream
- Returns OpenCV Mat object (convertible to NumPy array)
- Throws exception if read fails

**release() -> None**
- Releases the video capture resources
- Should be called when done

### NumPy Integration

The cv::Mat objects returned by `read()` are automatically convertible to NumPy arrays:

```python
cv_frame = reader.read()
numpy_frame = np.array(cv_frame, copy=False)  # Zero-copy conversion
```

## Troubleshooting

### Build Issues

1. **pybind11 not found:**
   ```bash
   python3.12 -m pip install pybind11
   ```

2. **OpenCV not found:**
   ```bash
   sudo apt install libopencv-dev
   ```

3. **Python 3.12 not found:**
   ```bash
   sudo apt install python3.12-dev
   ```

### Runtime Issues

1. **Module import fails:**
   - Ensure the .so file is in the same directory
   - Check Python version compatibility

2. **RTSP connection fails:**
   - Verify the RTSP URL is correct
   - Check network connectivity
   - Ensure camera supports RTSP

3. **Frame reading fails:**
   - Check if stream is still active
   - Verify codec compatibility

## Performance Notes

- The C++ backend provides significantly better performance than pure Python OpenCV
- Zero-copy NumPy conversion minimizes memory overhead
- Suitable for real-time applications

## License

[Add your license information here]