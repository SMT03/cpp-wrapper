#!/usr/bin/env python3
"""
Simple RTSP Stream Example
A basic example showing how to use the rtsp_module.
"""

import numpy as np
import cv2
import time

# Import the compiled C++ module
try:
    import rtsp_module
    print("✓ RTSP module imported successfully")
except ImportError as e:
    print(f"✗ Failed to import rtsp_module: {e}")
    print("Make sure the C++ module is compiled. Run 'make' to build it.")
    exit(1)


def simple_rtsp_example():
    """Basic example of reading frames from RTSP stream"""
    
    # RTSP stream URL - replace with your camera's URL
    rtsp_url = "rtsp://your-camera-ip:554/stream1"
    
    # Get URL from user
    user_input = input(f"Enter RTSP URL (default: {rtsp_url}): ").strip()
    if user_input:
        rtsp_url = user_input
    
    print(f"Connecting to: {rtsp_url}")
    
    try:
        # Create RTSP reader
        reader = rtsp_module.RTSPReader(rtsp_url)
        print("✓ Connected to RTSP stream")
        
        # Read and display frames
        for i in range(10):  # Capture 10 frames
            print(f"Reading frame {i+1}/10...")
            
            # Read frame from stream
            cv_frame = reader.read()
            
            # Convert to numpy array (automatic via buffer protocol)
            frame = np.array(cv_frame, copy=False)
            
            print(f"  Frame shape: {frame.shape}")
            print(f"  Frame dtype: {frame.dtype}")
            
            # Save frame as image (frame is BGR as returned by the module)
            filename = f"frame_{i+1:03d}.jpg"
            cv2.imwrite(filename, frame)
            print(f"  Saved: {filename}")
            
            # Small delay
            time.sleep(0.5)
        
        # Release resources
        reader.release()
        print("✓ Stream released")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def live_stream_viewer():
    """Live stream viewer with OpenCV window"""
    
    rtsp_url = input("Enter RTSP URL for live viewing: ").strip()
    if not rtsp_url:
        print("No URL provided")
        return
    
    try:
        reader = rtsp_module.RTSPReader(rtsp_url)
        print("✓ Connected. Press 'q' to quit, 's' to save frame")
        
        frame_count = 0
        
        while True:
            # Read frame
            cv_frame = reader.read()
            frame = np.array(cv_frame, copy=False)
            
            frame_count += 1
            
            # Display frame
            cv2.imshow('RTSP Live Stream', frame)
            
            # Handle keypresses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"saved_frame_{frame_count}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved: {filename}")
        
        # Cleanup
        reader.release()
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Simple RTSP Example")
    print("===================")
    
    print("\nChoose an option:")
    print("1. Capture 10 frames and save")
    print("2. Live stream viewer")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        simple_rtsp_example()
    elif choice == "2":
        live_stream_viewer()
    else:
        print("Invalid choice")