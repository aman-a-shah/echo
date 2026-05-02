import mss
import mss.tools
from PIL import Image
import io


class ScreenCapturer:
    def __init__(self):
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]  # Primary monitor

    def capture_frame(self, max_size=(800, 600)):
        """Captures the screen and returns a PIL Image."""
        sct_img = self.sct.grab(self.monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.thumbnail(max_size)
        return img

    def capture_frame_bytes(self, max_size=(800, 600)):
        """Captures the screen and returns JPEG bytes."""
        img = self.capture_frame(max_size)
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='JPEG', quality=85)
        return byte_arr.getvalue()


if __name__ == "__main__":
    capturer = ScreenCapturer()
    img = capturer.capture_frame()
    img.save("test_capture.jpg")
    print("Saved test_capture.jpg — check it looks correct!")