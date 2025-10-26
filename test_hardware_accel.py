#!/usr/bin/env python3
"""
Hardware Acceleration Test Script for RK3588
Tests FFmpeg rkmpp decoder, RGA color conversion, and overall performance
"""

import subprocess
import sys
import os
import time
import re
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def run_command(cmd, check=True, capture_output=True):
    """Run a shell command and return result"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture_output,
            text=True,
            timeout=10
        )
        if check and result.returncode != 0:
            return None, result.stderr
        return result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return None, "Command timed out"
    except Exception as e:
        return None, str(e)

def test_kernel_modules():
    """Test if required kernel modules are loaded"""
    print_header("Kernel Modules Test")
    
    modules = {
        'mpp_service': 'MPP Service',
        'rkvdec': 'Rockchip Video Decoder',
        'rkvenc': 'Rockchip Video Encoder',
        'rga3_core': 'RGA 3.0 Core',
        'rockchipdrm': 'Rockchip DRM'
    }
    
    all_passed = True
    for module, description in modules.items():
        output, _ = run_command(f"lsmod | grep -i {module}")
        if output:
            print_success(f"{description} ({module}) is loaded")
        else:
            print_error(f"{description} ({module}) is NOT loaded")
            all_passed = False
    
    return all_passed

def test_device_nodes():
    """Test if required device nodes exist"""
    print_header("Device Nodes Test")
    
    devices = {
        '/dev/mpp_service': 'MPP Service',
        '/dev/rga': 'RGA Device',
        '/dev/dri/card0': 'DRM Card 0',
        '/dev/dri/renderD128': 'DRM Render Node'
    }
    
    all_passed = True
    for device, description in devices.items():
        if os.path.exists(device):
            # Check if readable
            if os.access(device, os.R_OK):
                print_success(f"{description} ({device}) exists and is readable")
            else:
                print_warning(f"{description} ({device}) exists but NOT readable (check permissions)")
                all_passed = False
        else:
            print_error(f"{description} ({device}) does NOT exist")
            all_passed = False
    
    return all_passed

def test_user_permissions():
    """Test if user has required permissions"""
    print_header("User Permissions Test")
    
    import grp
    
    required_groups = ['video', 'render']
    user_groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]
    
    all_passed = True
    for group in required_groups:
        if group in user_groups:
            print_success(f"User is in '{group}' group")
        else:
            print_error(f"User is NOT in '{group}' group")
            print_info(f"  Add with: sudo usermod -aG {group} $USER")
            all_passed = False
    
    return all_passed

def test_ffmpeg_installation():
    """Test if FFmpeg is installed with rkmpp support"""
    print_header("FFmpeg Installation Test")
    
    # Check if ffmpeg exists
    output, _ = run_command("which ffmpeg")
    if not output:
        print_error("FFmpeg is NOT installed")
        return False
    
    ffmpeg_path = output.strip()
    print_success(f"FFmpeg found at: {ffmpeg_path}")
    
    # Check FFmpeg version
    output, _ = run_command("ffmpeg -version | head -n1")
    if output:
        print_info(f"Version: {output.strip()}")
    
    # Check for rkmpp decoders
    output, _ = run_command("ffmpeg -hide_banner -decoders 2>/dev/null | grep -i rkmpp")
    if output:
        print_success("rkmpp decoders found:")
        for line in output.strip().split('\n'):
            print(f"  {line.strip()}")
        return True
    else:
        print_error("rkmpp decoders NOT found")
        print_info("  FFmpeg may not be compiled with rkmpp support")
        return False

def test_rga_library():
    """Test if RGA library is installed"""
    print_header("RGA Library Test")
    
    # Check for librga.so
    output, _ = run_command("ldconfig -p | grep librga")
    if output:
        print_success("librga found:")
        for line in output.strip().split('\n'):
            print(f"  {line.strip()}")
        return True
    else:
        print_error("librga NOT found")
        print_info("  Install from: https://github.com/airockchip/librga")
        return False

def test_hardware_decode(test_url=None):
    """Test hardware H.264 decoding with FFmpeg"""
    print_header("Hardware Decode Test")
    
    if not test_url:
        print_warning("No test URL provided, skipping decode test")
        print_info("  Run with: python test_hardware_accel.py rtsp://your.camera.ip:554/stream")
        return None
    
    print_info(f"Testing hardware decode with: {test_url}")
    print_info("Attempting to decode 100 frames...")
    
    cmd = (
        f"ffmpeg -hide_banner -rtsp_transport tcp "
        f"-hwaccel drm -hwaccel_device /dev/dri/renderD128 "
        f"-c:v h264_rkmpp -i '{test_url}' "
        f"-vframes 100 -f null - 2>&1"
    )
    
    start_time = time.time()
    output, _ = run_command(cmd, check=False)
    elapsed_time = time.time() - start_time
    
    if output:
        # Parse for frame rate and errors
        if "error" in output.lower() or "failed" in output.lower():
            print_error("Hardware decode encountered errors:")
            for line in output.split('\n'):
                if 'error' in line.lower() or 'failed' in line.lower():
                    print(f"  {line.strip()}")
            return False
        
        # Extract FPS from output
        fps_match = re.search(r'(\d+\.?\d*)\s*fps', output)
        if fps_match:
            fps = float(fps_match.group(1))
            print_success(f"Hardware decode successful!")
            print_info(f"  Decoded 100 frames in {elapsed_time:.2f}s")
            print_info(f"  Average FPS: {fps:.2f}")
            
            if fps > 25:
                print_success(f"  Performance: Excellent (>{25} FPS)")
            else:
                print_warning(f"  Performance: May need optimization (<{25} FPS)")
            
            return True
        else:
            print_success("Hardware decode completed (FPS not detected)")
            return True
    
    print_error("Hardware decode failed")
    return False

def test_python_module():
    """Test if the Python rtsp_module can be imported"""
    print_header("Python Module Test")
    
    try:
        import rtsp_module
        print_success("rtsp_module imported successfully")
        
        # Check if RTSPReader class exists
        if hasattr(rtsp_module, 'RTSPReader'):
            print_success("RTSPReader class found")
            print_info(f"  Module location: {rtsp_module.__file__}")
            return True
        else:
            print_error("RTSPReader class NOT found in module")
            return False
            
    except ImportError as e:
        print_error(f"Failed to import rtsp_module: {e}")
        print_info("  Build the module with: ./build_venv.sh or make")
        return False

def test_python_module_with_url(test_url=None):
    """Test Python module with actual RTSP stream"""
    print_header("Python Module Stream Test")
    
    if not test_url:
        print_warning("No test URL provided, skipping stream test")
        return None
    
    try:
        import rtsp_module
        import numpy as np
        
        print_info(f"Testing with: {test_url}")
        print_info("Attempting to read 30 frames...")
        
        reader = rtsp_module.RTSPReader(test_url)
        
        frames_read = 0
        start_time = time.time()
        
        for i in range(30):
            frame = reader.read()
            if frame is not None and isinstance(frame, np.ndarray):
                frames_read += 1
            else:
                break
        
        elapsed_time = time.time() - start_time
        
        if frames_read > 0:
            fps = frames_read / elapsed_time
            print_success(f"Read {frames_read} frames successfully!")
            print_info(f"  Time: {elapsed_time:.2f}s")
            print_info(f"  Average FPS: {fps:.2f}")
            print_info(f"  Frame shape: {frame.shape}")
            print_info(f"  Frame dtype: {frame.dtype}")
            return True
        else:
            print_error("Failed to read frames from stream")
            return False
            
    except Exception as e:
        print_error(f"Python module test failed: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print_header("Test Summary")
    
    total_tests = len(results)
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    print(f"Total Tests: {total_tests}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    if skipped > 0:
        print_warning(f"Skipped: {skipped}")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✓ PASS" if result is True else ("✗ FAIL" if result is False else "⊘ SKIP")
        color = Colors.GREEN if result is True else (Colors.RED if result is False else Colors.YELLOW)
        print(f"  {color}{status}{Colors.END} - {test_name}")
    
    print()
    if failed == 0 and passed > 0:
        print_success("All tests passed! Hardware acceleration is ready.")
        return True
    elif failed > 0:
        print_error("Some tests failed. Please fix the issues above.")
        return False
    else:
        print_warning("No tests completed. Provide RTSP URL for full testing.")
        return None

def main():
    """Main test function"""
    print_header("RK3588 Hardware Acceleration Test Suite")
    
    # Get test URL from command line
    test_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not test_url:
        print_warning("No RTSP URL provided")
        print_info("Usage: python test_hardware_accel.py rtsp://camera.ip:554/stream")
        print_info("Running system tests only...\n")
    
    # Run all tests
    results = {}
    
    results['Kernel Modules'] = test_kernel_modules()
    results['Device Nodes'] = test_device_nodes()
    results['User Permissions'] = test_user_permissions()
    results['FFmpeg Installation'] = test_ffmpeg_installation()
    results['RGA Library'] = test_rga_library()
    results['Hardware Decode'] = test_hardware_decode(test_url)
    results['Python Module'] = test_python_module()
    results['Python Module Stream'] = test_python_module_with_url(test_url)
    
    # Print summary
    success = print_summary(results)
    
    # Exit with appropriate code
    if success is True:
        sys.exit(0)
    elif success is False:
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == '__main__':
    main()
