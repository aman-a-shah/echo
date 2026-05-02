import mss
import mss.tools
from PIL import Image, ImageChops, ImageFilter
import io
import math


class ScreenCapturer:
    def __init__(self):
        self.sct = mss.mss()
        self.monitor = self.sct.monitors[1]  # Primary monitor
        self._last_frame: Image.Image | None = None

    def capture_frame(self, max_size=(800, 600)) -> Image.Image:
        """Captures the screen and returns a PIL Image."""
        sct_img = self.sct.grab(self.monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        img.thumbnail(max_size)
        return img

    def capture_frame_bytes(self, max_size=(800, 600)) -> bytes:
        """Captures the screen and returns JPEG bytes."""
        img = self.capture_frame(max_size)
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='JPEG', quality=85)
        return byte_arr.getvalue()

    def diff_score(self, img: Image.Image) -> float:
        """
        Returns a 0.0-1.0 score of how different img is from the last frame.
        0.0 = identical, 1.0 = completely different.

        Uses a small blurred grayscale diff so minor rendering noise and
        cursor flicker don't trigger false positives.
        """
        if self._last_frame is None:
            return 1.0  # First frame — always treat as changed

        size = (160, 120)
        prev = self._last_frame.resize(size).convert("L").filter(ImageFilter.GaussianBlur(2))
        curr = img.resize(size).convert("L").filter(ImageFilter.GaussianBlur(2))

        diff = ImageChops.difference(prev, curr)
        pixels = list(diff.getdata())
        rms = math.sqrt(sum(p * p for p in pixels) / len(pixels))
        return rms / 255.0

    def capture_if_changed(
        self,
        threshold: float = 0.04,
        max_size: tuple = (800, 600),
    ) -> tuple[Image.Image | None, float]:
        """
        Captures a frame and compares it to the last one.

        Returns (img, score) if the scene changed enough to narrate,
        or (None, score) if it's too similar to bother.

        threshold: 0.04 (~4% pixel change) works well for games.
        Catches scene changes, new enemies, dialogue boxes, health drops.
        Ignores cursor blink, minor UI animations, subtle background movement.
        """
        img = self.capture_frame(max_size)
        score = self.diff_score(img)

        if score >= threshold:
            self._last_frame = img
            return img, score
        return None, score


if __name__ == "__main__":
    capturer = ScreenCapturer()
    img = capturer.capture_frame()
    img.save("test_capture.jpg")
    print("Saved test_capture.jpg — check it looks correct!")