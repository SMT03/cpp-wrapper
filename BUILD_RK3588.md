# Building for Rockchip RK3588 with Hardware Acceleration

This guide explains how to build and use the RTSP module with Rockchip rkmpp hardware decoding and RGA hardware color conversion on RK3588.

## Prerequisites

### 1. Install jellyfin-ffmpeg (with rkmpp support)

```bash
# Download jellyfin-ffmpeg for RK3588
# Option A: From jellyfin repository (recommended)
wget https://github.com/jellyfin/jellyfin-ffmpeg/releases/download/v6.0.1-8/jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb
sudo dpkg -i jellyfin-ffmpeg_6.0.1-8-jammy_arm64.deb

# Option B: Build from source
git clone https://github.com/jellyfin/jellyfin-ffmpeg.git
cd jellyfin-ffmpeg
# Follow their build instructions for RK3588
```

### 2. Install RGA library

```bash
# Install librga for hardware color conversion
sudo apt-get update
sudo apt-get install librga-dev librga2

# Or build from source:
git clone https://github.com/rockchip-linux/linux-rga.git
cd linux-rga
meson build
cd build
ninja
sudo ninja install
```

### 3. Install other dependencies

```bash
sudo apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    python3-dev \
    python3-pip

# Python dependencies
pip3 install -r requirements.txt
```

## Building

```bash
# Clean previous builds
rm -rf build
mkdir build
cd build

# Configure with CMake
cmake ..

# Build
make -j$(nproc)

# The output will be rtsp_module.cpython-*.so
```

## Verifying Hardware Acceleration

### Check if rkmpp decoder is available

```bash
/usr/lib/jellyfin-ffmpeg/ffmpeg -decoders | grep rkmpp
```

You should see:
```
 V..... h264_rkmpp           h264 (rkmpp) (codec h264)
 V..... hevc_rkmpp           hevc (rkmpp) (codec hevc)
```

### Check if RGA is available

```bash
ls -l /usr/lib/librga*
ls -l /usr/include/rga/
```

## Running

```bash
# Single camera
python3 main.py

# Four camera view (2x2 grid)
python3 four_view.py
```

## Performance Notes

### With Hardware Acceleration (rkmpp + RGA)
- **H.264 1080p**: ~5-10% CPU usage per stream
- **4x 1080p streams**: ~20-30% CPU usage total
- Decoding offloaded to VPU (Video Processing Unit)
- Color conversion offloaded to RGA (Raster Graphic Acceleration)

### Without Hardware Acceleration (software)
- **H.264 1080p**: ~40-60% CPU usage per stream
- **4x streams**: CPU maxed out, likely dropped frames

## Troubleshooting

### Error: "h264_rkmpp decoder not found"

This means jellyfin-ffmpeg is not properly installed or doesn't have rkmpp support.

**Solution**: Install jellyfin-ffmpeg from the official releases for RK3588.

### Error: "Failed to create DRM device context"

This means the hardware device is not accessible.

**Solutions**:
1. Make sure you're running on actual RK3588 hardware
2. Check DRM permissions: `ls -l /dev/dri/`
3. Add your user to the video/render group:
   ```bash
   sudo usermod -a -G video $USER
   sudo usermod -a -G render $USER
   # Log out and back in
   ```

### Warning: "RGA library not found"

The module will fall back to software swscale for color conversion.

**Solution**: Install librga as shown in prerequisites.

### Error: "Cannot open source file rga/rga.h"

RGA headers are not installed.

**Solution**:
```bash
sudo apt-get install librga-dev
# Or manually copy headers to /usr/include/rga/
```

## Performance Monitoring

Monitor CPU and memory usage:
```bash
# Watch CPU usage
htop

# Monitor hardware video decoder usage
cat /sys/kernel/debug/mpp_service/*/status

# Monitor memory
free -h
```

## Advanced Configuration

### Force software decoding (for testing)

Edit `rtsp_module.cpp` and change the decoder selection logic, or use a different FFmpeg build without rkmpp.

### Adjust RTSP buffer settings

In `rtsp_module.cpp`, the constructor sets:
```cpp
av_dict_set(&opts, "buffer_size", "2048000", 0);
av_dict_set(&opts, "max_delay", "500000", 0);
```

Adjust these values for your network conditions:
- Increase `buffer_size` for higher bandwidth streams
- Decrease `max_delay` for lower latency (may increase dropped frames)

### Multiple Streams

For 4+ concurrent streams, ensure you have sufficient:
- Network bandwidth (1080p ~= 4-8 Mbps per stream)
- Memory (each stream buffer ~10-20 MB)
- VPU sessions (RK3588 supports multiple concurrent decodes)

## Common Issues

### Dropped Frames
- Check network bandwidth
- Increase buffer_size
- Use TCP transport instead of UDP
- Reduce stream resolution at source

### High Latency
- Decrease buffer_size
- Decrease max_delay
- Use UDP transport (less reliable)
- Check network quality

### Memory Leaks
- Ensure `reader.release()` is called
- Use context managers in Python where possible
- Monitor with `top` or `htop`

## System-Specific Notes

### Orange Pi 5 / 5 Plus
- Fully compatible (uses RK3588)
- May need to enable hardware video in device tree

### Radxa Rock 5B
- Fully compatible (uses RK3588)
- Stock image should work out of the box

### Generic RK3588 Boards
- Ensure kernel has MPP drivers enabled
- Check `/dev/mpp_service` exists
- May need custom kernel/device tree

## Additional Resources

- [jellyfin-ffmpeg releases](https://github.com/jellyfin/jellyfin-ffmpeg/releases)
- [linux-rga GitHub](https://github.com/rockchip-linux/linux-rga)
- [Rockchip MPP documentation](https://github.com/rockchip-linux/mpp)
