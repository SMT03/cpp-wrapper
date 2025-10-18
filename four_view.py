#!/usr/bin/env python3
"""
Four-camera 2x2 viewer

Usage:
  python3 four_view.py

This script attempts to use the compiled `rtsp_module.RTSPReader`. If the
module isn't available it falls back to OpenCV's VideoCapture.

Controls:
  q - quit
  s - save snapshot of the combined view
"""

import threading
import time
from typing import Optional, List

import cv2
import numpy as np

USE_RTSP_MODULE = False
try:
    import rtsp_module
    USE_RTSP_MODULE = True
except Exception:
    USE_RTSP_MODULE = False


class CameraReader(threading.Thread):
    def __init__(self, src: str, idx: int, resize_to=(640, 360)):
        super().__init__(daemon=True)
        self.src = src
        self.idx = idx
        self.resize_to = resize_to
        self.lock = threading.Lock()
        self.frame: Optional[np.ndarray] = None
        self.running = True

        self._use_module = USE_RTSP_MODULE
        self._vc = None
        self._reader = None

    def open(self):
        if self._use_module:
            try:
                self._reader = rtsp_module.RTSPReader(self.src)
            except Exception as e:
                print(f"Camera[{self.idx}] rtsp_module failed to open: {e}")
                self._reader = None
        if not self._use_module or self._reader is None:
            # Fallback to OpenCV VideoCapture
            self._vc = cv2.VideoCapture(self.src)

    def run(self):
        self.open()
        while self.running:
            frame = None
            try:
                if self._reader is not None:
                    mat = self._reader.read()
                    frame = np.array(mat, copy=False)
                elif self._vc is not None:
                    ret, f = self._vc.read()
                    if not ret:
                        frame = None
                    else:
                        frame = f
            except Exception as e:
                print(f"Camera[{self.idx}] read error: {e}")
                frame = None

            if frame is not None:
                # Resize and ensure BGR 3-channel
                try:
                    h, w = frame.shape[:2]
                    if frame.ndim == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    if (w, h) != (self.resize_to[0], self.resize_to[1]):
                        frame = cv2.resize(frame, (self.resize_to[0], self.resize_to[1]))
                except Exception as e:
                    print(f"Camera[{self.idx}] processing error: {e}")
                    frame = None

            with self.lock:
                self.frame = frame

            if frame is None:
                # Wait a bit before retrying on failure
                time.sleep(0.1)

        # cleanup
        if self._reader is not None:
            try:
                self._reader.release()
            except Exception:
                pass
        if self._vc is not None:
            try:
                self._vc.release()
            except Exception:
                pass

    def stop(self):
        self.running = False


def compose_grid(frames: List[Optional[np.ndarray]], per=(640, 360)) -> np.ndarray:
    # frames: list of 4 frames or None
    # per: (width, height) per cell
    w, h = per
    blank = np.zeros((h, w, 3), dtype=np.uint8)
    cells = []
    for f in frames:
        if f is None:
            cells.append(blank.copy())
        else:
            cells.append(f)

    top = np.hstack((cells[0], cells[1]))
    bottom = np.hstack((cells[2], cells[3]))
    grid = np.vstack((top, bottom))
    return grid


def main():
    print("Four-camera viewer")
    print("Enter 4 RTSP URLs (leave blank to use placeholder).")

    defaults = [
        "rtsp://your-camera-ip:554/stream1",
        "rtsp://your-camera-ip:554/stream2",
        "rtsp://your-camera-ip:554/stream3",
        "rtsp://your-camera-ip:554/stream4",
    ]

    urls = []
    for i in range(4):
        u = input(f"URL {i+1} (default: {defaults[i]}): ").strip()
        urls.append(u if u else defaults[i])

    per_cell = (640, 360)
    readers = [CameraReader(urls[i], i, resize_to=per_cell) for i in range(4)]
    for r in readers:
        r.start()

    cv2.namedWindow("4-View", cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow("4-View", per_cell[0] * 2, per_cell[1] * 2)

    try:
        while True:
            frames = []
            for r in readers:
                with r.lock:
                    frames.append(r.frame.copy() if r.frame is not None else None)

            grid = compose_grid(frames, per=per_cell)
            cv2.imshow("4-View", grid)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                ts = int(time.time())
                fn = f"4view_snapshot_{ts}.jpg"
                cv2.imwrite(fn, grid)
                print(f"Saved snapshot: {fn}")
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass
    finally:
        for r in readers:
            r.stop()
        # Give threads a moment to exit
        time.sleep(0.2)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
