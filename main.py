#!/usr/bin/env python3

import sys
import cv2
import numpy as np
import time
from typing import Optional

try:
    import rtsp_module
except ImportError:
    print("Error: rtsp_module not found. Make sure the C++ module is compiled.")
    print("Run 'make' to build the module first.")
    sys.exit(1)


class RTSPStreamHandler:
    """
    A Python wrapper around the C++ RTSPReader for easier use.
    """
    
    def __init__(self, rtsp_url: str):
        """
        Initialize the RTSP stream handler.
        
        Args:
            rtsp_url (str): The RTSP stream URL
        """
        self.rtsp_url = rtsp_url
        self.reader: Optional[rtsp_module.RTSPReader] = None
        self.is_connected = False
        
    def connect(self) -> bool:
        """
        Connect to the RTSP stream.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            print(f"Connecting to RTSP stream: {self.rtsp_url}")
            self.reader = rtsp_module.RTSPReader(self.rtsp_url)
            self.is_connected = True
            print("Successfully connected to RTSP stream!")
            return True
        except Exception as e:
            print(f"Failed to connect to RTSP stream: {e}")
            self.is_connected = False
            return False
    
    def read_frame(self) -> Optional[np.ndarray]:
        """
        Read a single frame from the RTSP stream.
        
        Returns:
            np.ndarray: The frame as a NumPy array, or None if failed
        """
        if not self.is_connected or self.reader is None:
            print("Not connected to RTSP stream. Call connect() first.")
            return None
            
        try:
            # Read frame using the C++ module
            cv_mat = self.reader.read()
            
            # Convert cv::Mat to NumPy array
            # The C++ module should handle this conversion automatically
            # through the buffer protocol
            frame = np.array(cv_mat, copy=False)
            
            return frame
        except Exception as e:
            print(f"Failed to read frame: {e}")
            return None
    
    def disconnect(self):
        """
        Disconnect from the RTSP stream and release resources.
        """
        if self.reader is not None:
            try:
                self.reader.release()
                print("RTSP stream disconnected.")
            except Exception as e:
                print(f"Error during disconnect: {e}")
        
        self.reader = None
        self.is_connected = False


def display_stream_info(frame: np.ndarray):
    """
    Display information about the current frame.
    
    Args:
        frame (np.ndarray): The frame to analyze
    """
    if frame is not None:
        height, width = frame.shape[:2]
        channels = frame.shape[2] if len(frame.shape) > 2 else 1
        print(f"Frame info - Width: {width}, Height: {height}, Channels: {channels}, "
              f"Data type: {frame.dtype}, Shape: {frame.shape}")


def save_frame(frame: np.ndarray, filename: str) -> bool:
    """
    Save a frame to disk.
    
    Args:
        frame (np.ndarray): The frame to save
        filename (str): Output filename
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        # Convert BGR to RGB if needed (OpenCV uses BGR by default)
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            success = cv2.imwrite(filename, frame_rgb)
        else:
            success = cv2.imwrite(filename, frame)
        
        if success:
            print(f"Frame saved as: {filename}")
        else:
            print(f"Failed to save frame as: {filename}")
        
        return success
    except Exception as e:
        print(f"Error saving frame: {e}")
        return False


def main():
    """
    Main function demonstrating various uses of the RTSP module.
    """
    # Example RTSP URLs (replace with your actual RTSP stream)
    # Common test RTSP streams:
    rtsp_urls = [
        "rtsp://admin:admin1234@192.168.0.3:554/cam/realmonitor?channel=1&subtype=0",
        "rtsp://admin:admin1234@192.168.0.4:554/cam/realmonitor?channel=1&subtype=0",
        "rtsp://admin:admin1234@192.168.0.5:554/cam/realmonitor?channel=1&subtype=0"
    ]
    
    # Use the first URL for this example
    rtsp_url = rtsp_urls[0]
    
    # Ask user for RTSP URL if using default
    if rtsp_url == "rtsp://your-camera-ip:554/stream1":
        user_url = input("Enter your RTSP stream URL (or press Enter to use test URL): ").strip()
        if user_url:
            rtsp_url = user_url
        else:
            rtsp_url = rtsp_urls[2]  # Use test stream
    
    # Create RTSP handler
    stream_handler = RTSPStreamHandler(rtsp_url)
    
    # Connect to stream
    if not stream_handler.connect():
        return
    
    try:
        print("\nStarting frame capture...")
        print("Press 'q' to quit, 's' to save frame, 'i' for frame info")
        
        frame_count = 0
        start_time = time.time()
        
        while True:
            # Read frame
            frame = stream_handler.read_frame()
            
            if frame is None:
                print("Failed to read frame. Retrying...")
                time.sleep(0.1)
                continue
            
            frame_count += 1
            
            # Calculate FPS every 30 frames
            if frame_count % 30 == 0:
                elapsed = time.time() - start_time
                fps = 30 / elapsed if elapsed > 0 else 0
                print(f"FPS: {fps:.2f}, Frames captured: {frame_count}")
                start_time = time.time()
            
            # Display frame using OpenCV (optional)
            try:
                cv2.imshow('RTSP Stream', frame)
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"frame_{frame_count:06d}_{int(time.time())}.jpg"
                    save_frame(frame, filename)
                elif key == ord('i'):
                    display_stream_info(frame)
                    
            except Exception as e:
                print(f"Display error: {e}")
                print("Continuing without display...")
                
                # Simple keyboard input alternative
                print(f"Frame {frame_count} captured. Press Ctrl+C to stop.")
                time.sleep(0.033)  # ~30 FPS
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    
    except Exception as e:
        print(f"Error during streaming: {e}")
    
    finally:
        # Clean up
        stream_handler.disconnect()
        cv2.destroyAllWindows()
        print("Cleanup completed.")


def test_simple_capture():
    """
    Simple test function to capture a few frames.
    """
    print("=== Simple Capture Test ===")
    
    # Replace with your RTSP URL
    rtsp_url = input("Enter RTSP URL for testing: ").strip()
    if not rtsp_url:
        print("No URL provided. Skipping test.")
        return
    
    try:
        # Direct usage of the C++ module
        reader = rtsp_module.RTSPReader(rtsp_url)
        
        for i in range(5):
            print(f"Capturing frame {i+1}/5...")
            frame_mat = reader.read()
            frame = np.array(frame_mat, copy=False)
            
            print(f"Frame shape: {frame.shape}, dtype: {frame.dtype}")
            
            # Save frame
            filename = f"test_frame_{i+1}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Saved: {filename}")
            
            time.sleep(0.5)
        
        reader.release()
        print("Simple test completed!")
        
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    print("RTSP Stream Reader")
    print("==================")
    
    # Check if module is available
    try:
        # Test module import
        reader_test = rtsp_module.RTSPReader
        print("✓ rtsp_module loaded successfully")
    except Exception as e:
        print(f"✗ Module test failed: {e}")
        sys.exit(1)
    
    # Ask user what to do
    print("\nOptions:")
    print("1. Full stream viewer")
    print("2. Simple capture test")
    print("3. Exit")
    
    choice = input("Choose an option (1-3): ").strip()
    
    if choice == "1":
        main()
    elif choice == "2":
        test_simple_capture()
    else:
        print("Goodbye!")
