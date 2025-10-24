# RTSP Stream Reader - RK3588 Hardware Accelerated

This project provides a Python interface to read RTSP video streams using **Rockchip RK3588 hardware acceleration** with rkmpp (Hardware Video Decoder) and RGA (Raster Graphic Acceleration).

## Key Features

- 🚀 **Hardware H.264/HEVC decoding** via rkmpp (jellyfin-ffmpeg)
- ⚡ **Hardware color conversion** via RGA (NV12→BGR)
- 🎥 **4-camera 2x2 live viewer** with minimal CPU usage (~20-30% for 4x 1080p streams)
- 🔄 **Zero-copy** NumPy array integration
- 📉 **Ultra-low latency** (1-frame buffer)
- 💾 **Low memory footprint**

## Performance

| Configuration | CPU Usage | Notes |
|--------------|-----------|-------|
| 1x 1080p H.264 | ~5-10% | With rkmpp + RGA |
| 4x 1080p H.264 | ~20-30% | Hardware accelerated |
| 4x 1080p (software) | 100%+ | CPU maxed, dropped frames |

## Requirements

### Hardware
- **Rockchip RK3588** SoC (Orange Pi 5, Rock 5B, etc.)
- Network connectivity to RTSP cameras

### Software
- Python 3.x
- jellyfin-ffmpeg (with rkmpp support)
- librga (Rockchip RGA library)
- OpenCV (for Mat/NumPy conversion)
- pybind11

## Quick Start

### 1. Install Dependencies

```bash
# Install jellyfin-ffmpeg with rkmpp support
wget https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v6.0.1-8/jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb
sudo dpkg -i jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb

# Install RGA library
sudo apt-get update
sudo apt-get install librga-dev librga2

# Install build tools and OpenCV
sudo apt-get install -y build-essential pkg-config libopencv-dev python3-dev python3-pip

# Create virtual environment and install Python packages
python3 -m venv venv
source venv/bin/activate  # or: source venv/bin/activate.fish
pip install -r requirements.txt
```

### 2. Build the Module

#### Option 1: Using virtual environment build script (recommended)
```bash
./build_venv.sh
```

#### Option 2: Using CMake
```bash
mkdir build && cd build
cmake ..
make -j$(nproc)
```

#### Option 3: Using Makefile
```bash
make
```

### 3. Run Examples

```bash
# Activate virtual environment
source venv/bin/activate

# Single camera viewer
python3 main.py

# Four-camera 2x2 grid viewer
python3 four_view.py

# Simple 10-frame capture test
python3 simple_example.py
```

## Building

## Usage

```

## Hardware Acceleration Details

### Architecture

```
RTSP Stream → FFmpeg/rkmpp → VPU (Hardware Decode) → DRM Prime → RGA (Color Convert) → BGR Mat → NumPy
```

### What's Hardware Accelerated

1. **Video Decoding (rkmpp)**
   - H.264 streams decoded on Video Processing Unit (VPU)
   - HEVC/H.265 also supported
   - Decoder names: `h264_rkmpp`, `hevc_rkmpp`

2. **Color Conversion (RGA)**
   - NV12 → BGR conversion on dedicated 2D engine
   - Much faster than CPU swscale
   - Zero-copy where possible

### Configuration

The module uses minimal buffering for lowest latency:
- Frame buffer: **1 frame**
- Max delay: **0 microseconds**
- Transport: **TCP** (reliable)
- Reorder queue: **1**

## Four-Camera Viewer

The `four_view.py` script provides a real-time 2x2 grid display:

```bash
python3 four_view.py
```

**Features:**
- Thread-based concurrent stream reading
- Automatic frame resizing to 640x360 per camera
- Combined 1280x720 output window
- Keyboard controls:
  - `q` - Quit
  - `s` - Save snapshot

**Performance:**
- 4x 1080p streams @ ~25-30 FPS
- ~20-30% CPU usage (with rkmpp/RGA)
- ~100-150 MB RAM total

## API Reference

### RTSPReader Class

```python
import rtsp_module

reader = rtsp_module.RTSPReader(url: str)
```

#### Methods

**`read() -> cv::Mat`**
- Reads next frame from RTSP stream
- Returns OpenCV Mat (hardware-decoded, RGA-converted)
- Convertible to NumPy: `np.array(mat, copy=False)`
- Throws exception on error

**`release() -> None`**
- Releases stream and hardware resources
- Automatically called on destruction

### Example Usage

```python
import rtsp_module
import numpy as np
import cv2

# Open stream
reader = rtsp_module.RTSPReader("rtsp://admin:pass@192.168.1.100:554/stream")

try:
    while True:
        # Read frame (hardware decoded)
        mat = reader.read()
        frame = np.array(mat, copy=False)  # Zero-copy
        
        # Display
        cv2.imshow('Camera', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    reader.release()
    cv2.destroyAllWindows()
```

## RTSP URL Format

```
rtsp://[username:password@]host[:port]/path
```

**Examples:**
```python
# No auth
"rtsp://192.168.1.100:554/stream1"

# With credentials
"rtsp://admin:password123@192.168.1.100:554/h264"

# Common camera paths
"rtsp://camera-ip:554/cam/realmonitor?channel=1&subtype=0"  # Dahua
"rtsp://camera-ip:554/Streaming/Channels/101"               # Hikvision
"rtsp://camera-ip:554/live/main"                            # Generic
```

## Troubleshooting

### "h264_rkmpp decoder not found"

**Cause:** jellyfin-ffmpeg not installed or lacks rkmpp support.

**Solution:**
```bash
# Install jellyfin-ffmpeg for RK3588
wget https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v6.0.1-8/jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb
sudo dpkg -i jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb

# Verify
/usr/lib/jellyfin-ffmpeg/ffmpeg -decoders | grep rkmpp
```

### "Failed to create DRM device context"

**Cause:** Hardware device not accessible or not on RK3588.

**Solution:**
```bash
# Check DRM devices
ls -l /dev/dri/

# Add user to video group
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER
# Log out and back in
```

### "RGA library not found"

**Cause:** librga not installed.

**Solution:**
```bash
sudo apt-get install librga-dev librga2

# Or build from source
git clone https://github.com/rockchip-linux/linux-rga.git
cd linux-rga && meson build && cd build
ninja && sudo ninja install
```

### Build fails with missing headers

**Solution:**
```bash
# Install all build dependencies
sudo apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    libavformat-dev \
    libavcodec-dev \
    libavutil-dev \
    libswscale-dev \
    librga-dev \
    python3-dev

# Recreate venv
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Stream connection fails

**Common issues:**
1. **Wrong URL/credentials** - Verify with VLC or ffplay first
2. **Network firewall** - Check camera is reachable: `ping camera-ip`
3. **RTSP port blocked** - Default is 554, some use 8554
4. **Stream not available** - Camera may have max client limit

**Debug:**
```bash
# Test with ffplay (from jellyfin-ffmpeg)
/usr/lib/jellyfin-ffmpeg/ffplay "rtsp://your-camera-url"

# Test with ffmpeg
/usr/lib/jellyfin-ffmpeg/ffmpeg -rtsp_transport tcp -i "rtsp://your-url" -frames:v 1 test.jpg
```

### High CPU usage

**If CPU is still high (>40%) with rkmpp:**

1. **Verify hardware decoding:**
   ```python
   # Check module output on start
   # Should print: "RTSPReader initialized with rkmpp hardware decoding"
   ```

2. **Check VPU usage:**
   ```bash
   cat /sys/kernel/debug/mpp_service/*/status
   ```

3. **Monitor system:**
   ```bash
   htop  # CPU usage per core
   iotop  # Check if disk I/O is issue
   ```

## Advanced Topics

### Custom Build Flags

Edit `CMakeLists.txt` or `Makefile` to:
- Change optimization level (`-O3` → `-O2` or `-Ofast`)
- Enable debug symbols: add `-g`
- Profile: add `-pg`

### Multiple RK3588 Boards

This works on any RK3588-based SBC:
- Orange Pi 5 / 5 Plus
- Radxa Rock 5B / 5A
- Firefly ROC-RK3588S-PC
- Banana Pi BPI-W3
- Generic RK3588 boards

**Requirements:**
- Kernel with MPP drivers enabled
- `/dev/mpp_service` device present
- DRM/KMS enabled in device tree

## Performance Monitoring

```bash
# Real-time CPU usage
htop

# VPU hardware decoder status
watch -n 1 'cat /sys/kernel/debug/mpp_service/*/status'

# Memory usage
free -h && vmstat 1

# Network bandwidth
iftop -i eth0
```

## Credits & References

- [jellyfin-ffmpeg](https://github.com/jellyfin/jellyfin-ffmpeg) - FFmpeg with rkmpp patches
- [linux-rga](https://github.com/rockchip-linux/linux-rga) - Rockchip RGA library
- [Rockchip MPP](https://github.com/rockchip-linux/mpp) - Media Process Platform
- [pybind11](https://github.com/pybind/pybind11) - Python/C++ bindings

## License

[Add your license here]

## Support

For detailed RK3588-specific instructions, see [BUILD_RK3588.md](BUILD_RK3588.md)

**Common issues:**
- Hardware acceleration not working → Check DRM permissions
- Build errors → Verify all dependencies installed
- Connection failures → Test RTSP URL with ffplay first


[Add your license information here]