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

**Option A: Using ffmpeg-rockchip (Recommended for latest features)**

```bash
# Install ffmpeg-rockchip (community build with latest rkmpp support)
# Build from source for best compatibility
git clone https://github.com/nyanmisaka/ffmpeg-rockchip.git
cd ffmpeg-rockchip
./build.sh

# Or install prebuilt packages if available for your distro
# Check releases: https://github.com/nyanmisaka/ffmpeg-rockchip/releases

# Install MPP (Media Process Platform)
git clone https://github.com/rockchip-linux/mpp.git
cd mpp
cmake -DRKPLATFORM=ON -DHAVE_DRM=ON .
make -j$(nproc)
sudo make install
sudo ldconfig

# Install RGA library
git clone https://github.com/airockchip/librga.git
cd librga
meson setup builddir -Dlibdrm=true -Dlibrga_demo=false
meson compile -C builddir
sudo meson install -C builddir
sudo ldconfig

# Install other dependencies
sudo apt-get install -y build-essential pkg-config libopencv-dev python3-dev python3-pip

# Create virtual environment and install Python packages
python3 -m venv venv
source venv/bin/activate  # or: source venv/bin/activate.fish
pip install -r requirements.txt
```

**Option B: Using jellyfin-ffmpeg (Alternative)**

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

### Complete Hardware Acceleration Stack

#### 1. **FFmpeg with rkmpp Decoder**

The module supports multiple FFmpeg builds with rkmpp:

- **ffmpeg-rockchip** (nyanmisaka) - Latest community build, best performance
- **jellyfin-ffmpeg** - Stable, well-tested
- **Custom FFmpeg builds** with `--enable-rkmpp` flag

**Decoder names:**
- `h264_rkmpp` or `h264_rkmpp_decoder` - H.264/AVC hardware decoding
- `hevc_rkmpp` or `hevc_rkmpp_decoder` - H.265/HEVC hardware decoding

**Verification:**
```bash
# Check available rkmpp decoders
ffmpeg -decoders | grep rkmpp

# Expected output:
# V..... h264_rkmpp           h264 (rkmpp) (codec h264)
# V..... hevc_rkmpp           hevc (rkmpp) (codec hevc)
```

#### 2. **MPP (Media Process Platform)**

MPP is Rockchip's multimedia processing framework that interfaces with VPU hardware.

**Requirements:**
- MPP library installed (`libmpp.so`, `librockchip_mpp.so`)
- Kernel modules loaded: `mpp_service`, `mpp_vdpu2`, `rkvdec`, `rkvenc`
- Device nodes: `/dev/mpp_service`, `/dev/mpp-service`, `/dev/rkvdec`, `/dev/rkvenc`

**Verification:**
```bash
# Check MPP devices
ls -la /dev/mpp* /dev/rkvdec /dev/rkvenc

# Check kernel modules
lsmod | grep -E "mpp|vpu|vdec|venc"

# Check MPP library
ldconfig -p | grep mpp
```

**Build MPP from source (if needed):**
```bash
git clone https://github.com/rockchip-linux/mpp.git
cd mpp
mkdir build && cd build
cmake -DRKPLATFORM=ON -DHAVE_DRM=ON -DCMAKE_BUILD_TYPE=Release ..
make -j$(nproc)
sudo make install
sudo ldconfig

# Verify installation
pkg-config --modversion rockchip_mpp
```

#### 3. **RGA (Raster Graphic Acceleration)**

RGA provides hardware-accelerated 2D operations including color space conversion (NV12→BGR).

**Requirements:**
- librga installed (`librga.so`)
- Kernel module: `rga3_core` (or `rga2` for older SoCs)
- Device node: `/dev/rga`

**Verification:**
```bash
# Check RGA device
ls -la /dev/rga

# Check kernel module
lsmod | grep rga

# Check RGA library
ldconfig -p | grep rga

# Check version
cat /sys/module/rga*/version  # or similar path
```

**Build RGA from source (if needed):**
```bash
# For RK3588, use airockchip fork (latest)
git clone https://github.com/airockchip/librga.git
cd librga
meson setup builddir \
    -Dlibdrm=true \
    -Dlibrga_demo=false \
    -Dbuildtype=release
meson compile -C builddir
sudo meson install -C builddir
sudo ldconfig

# Verify
pkg-config --modversion librga
```

#### 4. **DRM (Direct Rendering Manager)**

DRM provides zero-copy buffer sharing between VPU and RGA.

**Requirements:**
- DRM device: `/dev/dri/card0`, `/dev/dri/renderD128`
- User in `video` and `render` groups

**Verification:**
```bash
# Check DRM devices
ls -la /dev/dri/

# Check permissions
groups $USER | grep -E "video|render"

# Add to groups if missing
sudo usermod -a -G video $USER
sudo usermod -a -G render $USER
# Log out and back in for changes to take effect
```

### Hardware Acceleration Flow

1. **RTSP Stream Reception**
   - TCP transport for reliability
   - Minimal buffering (1 frame)

2. **Hardware Decoding (VPU via MPP)**
   - Compressed H.264/H.265 → DRM PRIME buffers
   - NV12 pixel format in GPU memory
   - Zero-copy via DRM buffer sharing

3. **Hardware Color Conversion (RGA)**
   - NV12 → BGR24 conversion
   - Performed on 2D acceleration engine
   - Direct output to CPU-accessible memory

4. **NumPy Integration**
   - BGR Mat → Python buffer protocol
   - Zero-copy view into cv::Mat data
   - Suitable for OpenCV operations

### Performance Optimization

**For complete hardware acceleration, ensure:**

1. **FFmpeg rkmpp decoder is used:**
   ```bash
   # Module will print on startup:
   # "RTSPReader initialized with rkmpp hardware decoding"
   
   # If you see "software decoding", check:
   ffmpeg -decoders | grep rkmpp
   ldconfig -p | grep mpp
   ```

2. **RGA is functioning:**
   ```bash
   # Check RGA device access
   ls -l /dev/rga
   # Should show: crw-rw---- 1 root video ...
   
   # Test RGA with demo (if available)
   rgaImDemo  # or similar test program
   ```

3. **DRM permissions are correct:**
   ```bash
   # Check renderD128 permissions
   ls -l /dev/dri/renderD128
   # Should be accessible by video/render group
   ```

4. **No software fallbacks triggered:**
   - Monitor terminal output for warnings
   - "Failed to create DRM device context" → Check DRM permissions
   - "RGA conversion failed" → Check RGA device/module
   - "Warning: ... using software decoder" → Check rkmpp availability

### Testing Hardware Acceleration

```bash
# Test hardware decode with ffmpeg directly
ffmpeg -rtsp_transport tcp \
    -hwaccel drm \
    -hwaccel_device /dev/dri/renderD128 \
    -c:v h264_rkmpp \
    -i "rtsp://your-camera-url" \
    -f null -

# Monitor VPU usage
watch -n 1 'cat /sys/kernel/debug/mpp_service/*/status'

# Check if RGA is being used
sudo dmesg | grep -i rga | tail -20

# Run the module and check output
source venv/bin/activate
python3 -c "
import rtsp_module
reader = rtsp_module.RTSPReader('rtsp://test-url')
# Should print: 'RTSPReader initialized with rkmpp hardware decoding'
"
```

## Complete Hardware Acceleration Checklist

Follow these steps to ensure full hardware acceleration is enabled:

### ✅ Pre-requisites

1. **Verify you're on RK3588 hardware:**
   ```bash
   cat /proc/cpuinfo | grep "Rockchip"
   uname -m  # Should show aarch64
   ```

2. **Check kernel modules are loaded:**
   ```bash
   # All should return results:
   lsmod | grep mpp_service
   lsmod | grep rkvdec
   lsmod | grep rga
   
   # If missing, try loading manually:
   sudo modprobe mpp_service
   sudo modprobe rkvdec
   sudo modprobe rga3_core  # or rga for older kernels
   ```

3. **Verify device nodes exist:**
   ```bash
   ls -l /dev/mpp* /dev/rkvdec /dev/rkvenc /dev/rga /dev/dri/*
   
   # Expected output should include:
   # /dev/mpp_service or /dev/mpp-service
   # /dev/rkvdec
   # /dev/rga
   # /dev/dri/card0
   # /dev/dri/renderD128
   ```

4. **Set correct permissions:**
   ```bash
   # Add user to required groups
   sudo usermod -a -G video $USER
   sudo usermod -a -G render $USER
   
   # Apply group changes (or log out and back in)
   newgrp video
   newgrp render
   
   # Verify
   groups | grep -E "video|render"
   ```

### 📦 Installation Steps

1. **Install MPP:**
   ```bash
   # Option A: From package (if available)
   sudo apt-get install rockchip-mpp-dev librockchip-mpp1
   
   # Option B: Build from source
   git clone https://github.com/rockchip-linux/mpp.git
   cd mpp && mkdir build && cd build
   cmake -DRKPLATFORM=ON -DHAVE_DRM=ON -DCMAKE_BUILD_TYPE=Release ..
   make -j$(nproc) && sudo make install && sudo ldconfig
   
   # Verify
   pkg-config --modversion rockchip_mpp
   ldconfig -p | grep mpp
   ```

2. **Install RGA:**
   ```bash
   # For RK3588 (use airockchip version)
   git clone https://github.com/airockchip/librga.git
   cd librga
   meson setup builddir -Dlibdrm=true -Dlibrga_demo=false -Dbuildtype=release
   meson compile -C builddir
   sudo meson install -C builddir
   sudo ldconfig
   
   # Verify
   pkg-config --modversion librga
   ldconfig -p | grep librga
   ls -l /usr/local/lib/librga.so*
   ```

3. **Install FFmpeg with rkmpp:**
   ```bash
   # Option A: ffmpeg-rockchip (Recommended)
   git clone https://github.com/nyanmisaka/ffmpeg-rockchip.git
   cd ffmpeg-rockchip
   # Follow build instructions in repository
   ./build.sh
   sudo cp ffmpeg /usr/local/bin/
   
   # Option B: jellyfin-ffmpeg (Pre-built)
   wget https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v6.0.1-8/jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb
   sudo dpkg -i jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb
   
   # Verify rkmpp decoders
   ffmpeg -decoders | grep rkmpp
   # Should show: h264_rkmpp and hevc_rkmpp
   ```

4. **Set up build environment:**
   ```bash
   # Install build tools
   sudo apt-get install -y build-essential cmake pkg-config
   sudo apt-get install -y libopencv-dev python3-dev python3-pip
   
   # Create Python venv
   cd /path/to/cpp-wrapper
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Build the module:**
   ```bash
   # Using the venv build script
   ./build_venv.sh
   
   # Or using CMake
   mkdir build && cd build
   cmake ..
   make -j$(nproc)
   
   # The .so module should be created
   ls -lh rtsp_module*.so
   ```

### 🧪 Verification Steps

1. **Test FFmpeg rkmpp decode:**
   ```bash
   # Replace with your RTSP URL
   ffmpeg -rtsp_transport tcp \
       -c:v h264_rkmpp \
       -i "rtsp://admin:pass@192.168.1.100:554/stream" \
       -frames:v 10 \
       -f null -
   
   # Should NOT show errors about missing decoder
   # Check for hardware activity:
   cat /sys/kernel/debug/mpp_service/mpp_srv/status
   ```

2. **Test the Python module:**
   ```bash
   source venv/bin/activate
   python3 << 'EOF'
   import rtsp_module
   import numpy as np
   
   # Replace with your RTSP URL
   url = "rtsp://admin:pass@192.168.1.100:554/stream"
   
   print("Creating RTSPReader...")
   reader = rtsp_module.RTSPReader(url)
   # Should print: "RTSPReader initialized with rkmpp hardware decoding"
   
   print("Reading frame...")
   mat = reader.read()
   frame = np.array(mat, copy=False)
   print(f"✓ Frame captured: {frame.shape}, dtype: {frame.dtype}")
   
   reader.release()
   print("✓ Hardware acceleration working!")
   EOF
   ```

3. **Monitor hardware usage:**
   ```bash
   # Open multiple terminals:
   
   # Terminal 1: Monitor VPU
   watch -n 1 'cat /sys/kernel/debug/mpp_service/*/status 2>/dev/null || echo "MPP not available"'
   
   # Terminal 2: Monitor CPU
   htop
   
   # Terminal 3: Run your application
   source venv/bin/activate
   python3 four_view.py
   
   # Expected: CPU usage 20-30% for 4 cameras, VPU should show active sessions
   ```

### 🚨 Common Issues & Fixes

**"h264_rkmpp decoder not found"**
```bash
# Check FFmpeg has rkmpp compiled in:
ffmpeg -decoders | grep rkmpp
ffmpeg -version | grep rkmpp

# If missing, rebuild FFmpeg with rkmpp or use pre-built version
```

**"Failed to create DRM device context"**
```bash
# Check DRM devices and permissions:
ls -l /dev/dri/
id | grep -E "video|render"

# If not in groups:
sudo usermod -a -G video,render $USER
# Log out and back in
```

**"RGA conversion failed"**
```bash
# Check RGA device:
ls -l /dev/rga

# Check RGA kernel module:
lsmod | grep rga
dmesg | grep -i rga | tail -20

# If missing, load module:
sudo modprobe rga3_core
```

**Module shows "software decoding"**
```bash
# Verify FFmpeg in PATH has rkmpp:
which ffmpeg
ffmpeg -decoders | grep rkmpp

# Check MPP library is found:
ldconfig -p | grep mpp

# Rebuild module with correct FFmpeg:
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH
./build_venv.sh
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