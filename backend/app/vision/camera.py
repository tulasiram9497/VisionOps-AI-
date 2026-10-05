from __future__ import annotations

import cv2


class CameraError(RuntimeError):
    """Raised when a local camera or video source cannot be opened."""


class CameraManager:
    """Reusable camera abstraction for webcams and local video files."""

    def __init__(self, source: int | str = 0, width: int = 640, height: int = 480) -> None:
        self.source = source
        self.width = width
        self.height = height
        self.capture: cv2.VideoCapture | None = None

    def open(self) -> cv2.VideoCapture:
        self.capture = cv2.VideoCapture(self.source)
        if not self.capture.isOpened():
            raise CameraError(f"Unable to open camera source: {self.source}")
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return self.capture

    def read_frame(self):
        if self.capture is None or not self.capture.isOpened():
            raise CameraError("Camera has not been opened.")
        success, frame = self.capture.read()
        if not success or frame is None:
            raise CameraError("Failed to read a frame from the camera source.")
        return frame

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
