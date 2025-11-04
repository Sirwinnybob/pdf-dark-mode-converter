import pikepdf
from pikepdf import Pdf, Name, Array, Operator, Rectangle
import io
import re
from typing import Tuple, List
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


class PDFVectorProcessorPikePDF:
    """
    Vector-based PDF processor using pikepdf for content stream manipulation.
    Preserves all text quality and searchability.
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
        """Process PDF by modifying content streams."""
        # Open PDF
        self.pdf = Pdf.open(io.BytesIO(input_bytes))

        # Process each page (create background per page for correct dimensions)
        for page in self.pdf.pages:
            self._process_page(page)

        # Save to bytes
        output = io.BytesIO()
        self.pdf.save(output)
        output.seek(0)

        result = output.getvalue()
        self.pdf.close()

        return result

    def _create_background_pdf(self, width, height) -> Pdf:
        """Create a single-page PDF with dark background using reportlab."""
        packet = io.BytesIO()
        # Use the exact page dimensions
        can = canvas.Canvas(packet, pagesize=(width, height))

        # Set fill color to theme color
        bg_r = self.bg_color["r"] / 255.0
        bg_g = self.bg_color["g"] / 255.0
        bg_b = self.bg_color["b"] / 255.0

        can.setFillColorRGB(bg_r, bg_g, bg_b)
        can.rect(0, 0, width, height, fill=True, stroke=False)
        can.save()

        packet.seek(0)
        return Pdf.open(packet)

    def _process_page(self, page):
        """Process a single page's content stream."""
        try:
            # Get page dimensions
            mediabox = page.MediaBox
            width = float(mediabox[2] - mediabox[0])
            height = float(mediabox[3] - mediabox[1])

            # Create a background PDF with the exact page dimensions
            bg_pdf = self._create_background_pdf(width, height)
            bg_page = bg_pdf.pages[0]

            # Add dark background as underlay (below all content)
            bg_rect = Rectangle(0, 0, width, height)
            page.add_underlay(bg_page, bg_rect)

            # Close the background PDF
            bg_pdf.close()

            # Now transform the colors in the existing content
            if Name.Contents not in page:
                return

            contents = page.Contents

            # Collect all content and transform it
            all_content = []

            # Handle array of content streams
            if isinstance(contents, pikepdf.Array):
                for i, stream in enumerate(contents):
                    if hasattr(stream, 'read_bytes'):
                        content_data = stream.read_bytes()
                        content_str = content_data.decode('latin-1', errors='ignore')
                        all_content.append(content_str)

            # Handle single content stream
            elif hasattr(contents, 'read_bytes'):
                content_data = contents.read_bytes()
                content_str = content_data.decode('latin-1', errors='ignore')
                all_content.append(content_str)

            # Combine all content
            combined_content = '\n'.join(all_content)

            # Transform the combined content (change text/graphic colors)
            modified_content = self._transform_content_stream(combined_content)

            # Create new stream and replace
            new_stream = pikepdf.Stream(self.pdf, modified_content.encode('latin-1'))
            page.Contents = new_stream

        except Exception as e:
            print(f"Warning: Could not process page: {e}")
            import traceback
            traceback.print_exc()

    def _transform_content_stream(self, content: str) -> str:
        """
        Transform color operators in PDF content stream.
        """
        # Use regex to find and replace color operators

        # RGB non-stroking (rg) - text and fill colors
        # Match numbers like: 0, 0.5, .5, 1.0
        content = re.sub(
            r'(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+rg',
            lambda m: self._replace_rgb(m, 'rg'),
            content
        )

        # RGB stroking (RG) - line colors
        content = re.sub(
            r'(\d*\.?\d+)\s+(\d*\.?\d+)\s+(\d*\.?\d+)\s+RG',
            lambda m: self._replace_rgb(m, 'RG'),
            content
        )

        # Grayscale non-stroking (g) - be more careful with the pattern
        content = re.sub(
            r'(\d+\.?\d*)\s+g\b',
            lambda m: self._replace_gray(m, 'g'),
            content
        )

        # Grayscale stroking (G)
        content = re.sub(
            r'(\d+\.?\d*)\s+G\b',
            lambda m: self._replace_gray(m, 'G'),
            content
        )

        # CMYK non-stroking (k)
        content = re.sub(
            r'(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+k\b',
            lambda m: self._replace_cmyk(m, 'k'),
            content
        )

        # CMYK stroking (K)
        content = re.sub(
            r'(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+(\d+\.?\d*)\s+K\b',
            lambda m: self._replace_cmyk(m, 'K'),
            content
        )

        return content

    def _replace_rgb(self, match, operator):
        """Replace RGB color operator."""
        r = float(match.group(1))
        g = float(match.group(2))
        b = float(match.group(3))

        new_r, new_g, new_b = self._transform_rgb(r, g, b)

        # Debug output
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        if brightness > 0.9:  # Log white colors
            print(f"Transforming white/light RGB: ({r:.2f}, {g:.2f}, {b:.2f}) -> ({new_r:.2f}, {new_g:.2f}, {new_b:.2f})")
        elif brightness < 0.2 and (g > 0.01 or b > 0.01):  # Log dark colored values
            print(f"Transforming dark colored RGB: ({r:.2f}, {g:.2f}, {b:.2f}) -> ({new_r:.2f}, {new_g:.2f}, {new_b:.2f})")

        return f"{new_r:.4f} {new_g:.4f} {new_b:.4f} {operator}"

    def _replace_gray(self, match, operator):
        """Replace grayscale color operator."""
        gray = float(match.group(1))

        new_gray = self._transform_grayscale(gray)

        return f"{new_gray:.4f} {operator} "

    def _replace_cmyk(self, match, operator):
        """Replace CMYK color operator."""
        c = float(match.group(1))
        m = float(match.group(2))
        y = float(match.group(3))
        k = float(match.group(4))

        new_c, new_m, new_y, new_k = self._transform_cmyk(c, m, y, k)

        return f"{new_c:.4f} {new_m:.4f} {new_y:.4f} {new_k:.4f} {operator} "

    def _transform_rgb(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """Transform RGB colors with high contrast."""
        brightness = 0.299 * r + 0.587 * g + 0.114 * b

        # White/light backgrounds → dark theme color
        if brightness > 0.93:
            return (
                self.bg_color["r"] / 255.0,
                self.bg_color["g"] / 255.0,
                self.bg_color["b"] / 255.0
            )

        # Check if it's a colored dark value (has hue/saturation)
        h, s, v = self._rgb_to_hsv(r, g, b)

        # Very dark with low saturation (grayscale/black text) → bright white
        if brightness < 0.15 and s < 0.3:
            return (0.98, 0.98, 0.98)

        # Very dark with saturation (colored like dark blue) → brighten while keeping hue
        if brightness < 0.15:
            # Map dark colored values (0-0.15) to bright colored values (0.65-0.85)
            v = 0.65 + (v / 0.15) * 0.2  # Scale up significantly
            s = min(s * 1.1, 1.0)  # Slightly boost saturation
            new_r, new_g, new_b = self._hsv_to_rgb(h, s, v)
            # Clamp values to 0-1 range
            return (min(max(new_r, 0), 1), min(max(new_g, 0), 1), min(max(new_b, 0), 1))

        # Dark colors (like dark blue) → brighten significantly
        if brightness < 0.4:
            h, s, v = self._rgb_to_hsv(r, g, b)
            v = 0.75 + (v - 0.15) * 0.8
            s = s * 0.85
            return self._hsv_to_rgb(h, s, v)

        # Medium-dark → brighten moderately
        if brightness < 0.6:
            h, s, v = self._rgb_to_hsv(r, g, b)
            v = 0.65 + (v - 0.4) * 1.0
            s = s * 0.9
            return self._hsv_to_rgb(h, s, v)

        # Other colors
        h, s, v = self._rgb_to_hsv(r, g, b)
        v = 0.5 + v * 0.5
        return self._hsv_to_rgb(h, s, v)

    def _transform_grayscale(self, gray: float) -> float:
        """Transform grayscale."""
        if gray > 0.93:
            bg_gray = (0.299 * self.bg_color["r"] +
                      0.587 * self.bg_color["g"] +
                      0.114 * self.bg_color["b"]) / 255.0
            return bg_gray

        if gray < 0.15:
            return 0.98

        if gray < 0.4:
            return 0.75 + (gray - 0.15) * 0.8

        if gray < 0.6:
            return 0.65 + (gray - 0.4) * 1.0

        return 0.5 + gray * 0.5

    def _transform_cmyk(self, c: float, m: float, y: float, k: float) -> Tuple[float, float, float, float]:
        """Transform CMYK to RGB, transform, convert back."""
        # Convert to RGB
        r = (1 - c) * (1 - k)
        g = (1 - m) * (1 - k)
        b = (1 - y) * (1 - k)

        # Transform
        new_r, new_g, new_b = self._transform_rgb(r, g, b)

        # Convert back to CMYK
        if new_r == 0 and new_g == 0 and new_b == 0:
            return 0, 0, 0, 1

        new_k = 1 - max(new_r, new_g, new_b)
        if new_k < 1:
            new_c = (1 - new_r - new_k) / (1 - new_k)
            new_m = (1 - new_g - new_k) / (1 - new_k)
            new_y = (1 - new_b - new_k) / (1 - new_k)
        else:
            new_c = 0
            new_m = 0
            new_y = 0

        return new_c, new_m, new_y, new_k

    def _rgb_to_hsv(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """Convert RGB to HSV."""
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val

        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        s = 0 if max_val == 0 else (diff / max_val)
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
