import fitz  # PyMuPDF
import io
from PIL import Image
from typing import Tuple


class PDFSimpleProcessor:
    """
    Simple rasterization-based processor with improved color transformation.
    Focuses on high contrast and better color handling.
    """

    def __init__(self, theme: str = "classic"):
        self.theme = theme
        self.themes = {
            "classic": {"r": 0, "g": 0, "b": 0},
            "claude": {"r": 42, "g": 37, "b": 34},
            "chatgpt": {"r": 52, "g": 53, "b": 65},
            "sepia": {"r": 40, "g": 35, "b": 25},
            "midnight": {"r": 25, "g": 30, "b": 45},
            "forest": {"r": 25, "g": 35, "b": 30}
        }
        self.bg_color = self.themes.get(theme, self.themes["classic"])

    def process_pdf(self, input_bytes: bytes) -> bytes:
        """Process PDF by rendering at high resolution and transforming colors."""
        doc = fitz.open(stream=input_bytes, filetype="pdf")
        new_doc = fitz.open()

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Render at VERY high resolution (5x scale for best quality)
            mat = fitz.Matrix(5, 5)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Transform colors
            img = self._transform_image(img)

            # Convert back to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG', optimize=True)
            img_bytes.seek(0)

            # Create new page and insert image
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(page.rect, stream=img_bytes.getvalue())

        output_bytes = new_doc.tobytes(garbage=4, deflate=True)
        doc.close()
        new_doc.close()

        return output_bytes

    def _transform_image(self, img: Image.Image) -> Image.Image:
        """Transform image colors for dark mode with high contrast."""
        pixels = img.load()
        width, height = img.size

        bg_r = self.bg_color["r"]
        bg_g = self.bg_color["g"]
        bg_b = self.bg_color["b"]

        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]

                # Normalize to 0-1
                r_norm = r / 255.0
                g_norm = g / 255.0
                b_norm = b / 255.0

                # Transform
                new_r, new_g, new_b = self._transform_rgb(r_norm, g_norm, b_norm)

                # Convert back to 0-255
                pixels[x, y] = (
                    int(new_r * 255),
                    int(new_g * 255),
                    int(new_b * 255)
                )

        return img

    def _transform_rgb(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """
        Transform RGB with HIGH CONTRAST for dark mode.
        """
        # Calculate brightness
        brightness = 0.299 * r + 0.587 * g + 0.114 * b

        # Very light colors (backgrounds) → theme background
        if brightness > 0.93:
            return (
                self.bg_color["r"] / 255.0,
                self.bg_color["g"] / 255.0,
                self.bg_color["b"] / 255.0
            )

        # Very dark colors (text) → bright white
        if brightness < 0.15:
            return (0.98, 0.98, 0.98)

        # Dark colors → brighten significantly while preserving hue
        if brightness < 0.4:
            h, s, v = self._rgb_to_hsv(r, g, b)

            # Map 0.15-0.4 brightness to 0.75-0.95 brightness
            v = 0.75 + (v - 0.15) * 0.8

            # Reduce saturation slightly for pastel effect
            s = s * 0.85

            return self._hsv_to_rgb(h, s, v)

        # Medium-dark colors → brighten moderately
        if brightness < 0.6:
            h, s, v = self._rgb_to_hsv(r, g, b)

            # Map 0.4-0.6 to 0.65-0.85
            v = 0.65 + (v - 0.4) * 1.0
            s = s * 0.9

            return self._hsv_to_rgb(h, s, v)

        # Medium-light colors → adjust moderately
        h, s, v = self._rgb_to_hsv(r, g, b)
        v = 0.5 + v * 0.5
        return self._hsv_to_rgb(h, s, v)

    def _rgb_to_hsv(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """Convert RGB to HSV."""
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val

        # Hue
        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        # Saturation
        s = 0 if max_val == 0 else (diff / max_val)

        # Value
        v = max_val

        return h / 360.0, s, v

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """Convert HSV to RGB."""
        h = h * 360.0
        c = v * s
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = v - c

        if 0 <= h < 60:
            r, g, b = c, x, 0
        elif 60 <= h < 120:
            r, g, b = x, c, 0
        elif 120 <= h < 180:
            r, g, b = 0, c, x
        elif 180 <= h < 240:
            r, g, b = 0, x, c
        elif 240 <= h < 300:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x

        return r + m, g + m, b + m
