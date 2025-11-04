import fitz  # PyMuPDF
import io
from PIL import Image
from typing import Tuple, Dict, List
import re


class PDFVectorProcessor:
    """
    Processes PDF files by manipulating content streams directly to preserve vector data.
    Applies dark mode color transformations while maintaining text selectability and quality.
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
        """
        Main processing function that converts a PDF to dark mode using vector manipulation.

        Args:
            input_bytes: PDF file as bytes

        Returns:
            Processed PDF as bytes
        """
        # Open the PDF from bytes
        doc = fitz.open(stream=input_bytes, filetype="pdf")

        # Create a new document to redraw into
        new_doc = fitz.open()

        # Process each page
        for page_num in range(len(doc)):
            page = doc[page_num]

            # Create new page with same dimensions
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)

            # Get all page elements and redraw with transformed colors
            self._redraw_page_with_colors(page, new_page, doc)

        # Save to bytes
        output_bytes = new_doc.tobytes(garbage=4, deflate=True)
        doc.close()
        new_doc.close()

        return output_bytes

    def _redraw_page_with_colors(self, source_page: fitz.Page, target_page: fitz.Page, doc: fitz.Document):
        """
        Redraw a page with transformed colors while preserving vector data.
        Uses PyMuPDF's get_drawings() and get_text() to extract and redraw elements.
        """
        # Set background color
        bg_color = (
            self.bg_color["r"] / 255.0,
            self.bg_color["g"] / 255.0,
            self.bg_color["b"] / 255.0
        )
        target_page.draw_rect(target_page.rect, color=None, fill=bg_color)

        # Get all drawings (vector shapes, paths)
        drawings = source_page.get_drawings()

        for drawing in drawings:
            # Transform colors in the drawing
            if 'fill' in drawing and drawing['fill'] is not None:
                fill = drawing['fill']
                # Handle tuple of 3 floats (RGB)
                if isinstance(fill, (tuple, list)) and len(fill) == 3:
                    r, g, b = fill
                    new_r, new_g, new_b = self._transform_rgb(r, g, b)
                    drawing['fill'] = (new_r, new_g, new_b)
                else:
                    drawing['fill'] = None

            if 'color' in drawing and drawing['color'] is not None:
                color = drawing['color']
                # Handle tuple of 3 floats (RGB)
                if isinstance(color, (tuple, list)) and len(color) == 3:
                    r, g, b = color
                    new_r, new_g, new_b = self._transform_rgb(r, g, b)
                    drawing['color'] = (new_r, new_g, new_b)
                else:
                    drawing['color'] = None

            # Redraw the shape on the new page
            self._draw_shape(target_page, drawing)

        # Get and redraw text with transformed colors using rawdict for better positioning
        text_dict = source_page.get_text("rawdict", flags=fitz.TEXTFLAGS_TEXT)

        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        # Get text properties
                        text = span.get("text", "")
                        if not text or not text.strip():
                            continue

                        font = span.get("font", "helv")
                        size = span.get("size", 12)
                        color_int = span.get("color", 0)
                        flags = span.get("flags", 0)

                        # Convert color from integer
                        if isinstance(color_int, int):
                            r = ((color_int >> 16) & 0xFF) / 255.0
                            g = ((color_int >> 8) & 0xFF) / 255.0
                            b = (color_int & 0xFF) / 255.0
                        else:
                            r, g, b = 0, 0, 0

                        # Transform color
                        new_r, new_g, new_b = self._transform_rgb(r, g, b)

                        # Get position - use bbox for more accurate placement
                        origin = span.get("origin", (0, 0))
                        bbox = span.get("bbox", None)

                        # Get font properties for better rendering
                        ascender = span.get("ascender", 0.8)
                        descender = span.get("descender", -0.2)

                        # Insert text with new color and proper positioning
                        try:
                            # Try with original font first
                            tw = target_page.insert_text(
                                origin,
                                text,
                                fontsize=size,
                                fontname=font,
                                color=(new_r, new_g, new_b),
                                render_mode=0  # Fill text
                            )
                        except Exception as e:
                            # Fallback to default font if the original font isn't available
                            try:
                                target_page.insert_text(
                                    origin,
                                    text,
                                    fontsize=size,
                                    fontname="helv",
                                    color=(new_r, new_g, new_b),
                                    render_mode=0
                                )
                            except Exception as e2:
                                # Last resort: try with basic settings
                                print(f"Warning: Could not render text '{text[:20]}...': {e2}")

        # Handle images
        image_list = source_page.get_images(full=True)
        for img_info in image_list:
            xref = img_info[0]
            try:
                # Get image bbox
                img_rects = source_page.get_image_rects(xref)
                if not img_rects:
                    continue

                img_rect = img_rects[0]

                # Extract and transform image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Open with PIL and transform
                img = Image.open(io.BytesIO(image_bytes))
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Transform pixels
                pixels = img.load()
                width, height = img.size

                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        new_r, new_g, new_b = self._transform_rgb(
                            r / 255.0, g / 255.0, b / 255.0
                        )
                        pixels[x, y] = (
                            int(new_r * 255),
                            int(new_g * 255),
                            int(new_b * 255)
                        )

                # Save transformed image
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                # Insert into new page
                target_page.insert_image(img_rect, stream=img_byte_arr.getvalue())

            except Exception as e:
                print(f"Warning: Could not process image: {e}")
                continue

    def _draw_shape(self, page: fitz.Page, drawing: dict):
        """Draw a shape on the page with its properties."""
        try:
            items = drawing.get("items", [])
            fill_color = drawing.get("fill")
            stroke_color = drawing.get("color")
            width = drawing.get("width", 1)

            # Create a Shape object for drawing
            shape = page.new_shape()

            for item in items:
                item_type = item[0]

                if item_type == "l":  # line
                    p1, p2 = item[1], item[2]
                    shape.draw_line(p1, p2)
                elif item_type == "c":  # curve
                    p1, p2, p3, p4 = item[1], item[2], item[3], item[4]
                    shape.draw_bezier(p1, p2, p3, p4)
                elif item_type == "re":  # rectangle
                    rect = item[1]
                    shape.draw_rect(rect)

            # Finish and commit the shape
            shape.finish(
                fill=fill_color,
                color=stroke_color,
                width=width
            )
            shape.commit()

        except Exception as e:
            print(f"Warning: Could not draw shape: {e}")

    def _OLD_transform_content_stream(self, content: str) -> str:
        """
        Parse and transform color operators in PDF content stream.

        Handles operators:
        - rg/RG: RGB color (non-stroking/stroking)
        - g/G: Grayscale (non-stroking/stroking)
        - k/K: CMYK (non-stroking/stroking)
        - sc/SC/scn/SCN: SetColor operators
        """
        # PDF content streams don't always have newlines between operators
        # We need to tokenize the stream properly

        # Split by whitespace but preserve the structure
        tokens = re.split(r'(\s+)', content)
        result = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            # Handle RGB operators (3 numbers followed by rg or RG)
            if token in ('rg', 'RG'):
                # Look back for 3 numbers
                if i >= 6:  # Need at least 3 numbers + 3 spaces
                    try:
                        # Extract the last 3 numeric values before this operator
                        values = []
                        back_idx = i - 1
                        nums_found = 0
                        temp_tokens = []

                        while nums_found < 3 and back_idx >= 0:
                            if tokens[back_idx].strip() and not tokens[back_idx].isspace():
                                try:
                                    val = float(tokens[back_idx])
                                    values.insert(0, val)
                                    temp_tokens.insert(0, back_idx)
                                    nums_found += 1
                                except ValueError:
                                    break
                            back_idx -= 1

                        if nums_found == 3:
                            r, g, b = values
                            new_r, new_g, new_b = self._transform_rgb(r, g, b)

                            # Remove old values from result
                            for _ in range((i - temp_tokens[0])):
                                if result:
                                    result.pop()

                            # Add new values
                            result.append(f"{new_r:.6f} {new_g:.6f} {new_b:.6f} {token}")
                            i += 1
                            continue
                    except:
                        pass

            # Handle Grayscale operators (1 number followed by g or G)
            elif token in ('g', 'G'):
                if i >= 2:
                    try:
                        back_idx = i - 1
                        while back_idx >= 0 and tokens[back_idx].isspace():
                            back_idx -= 1

                        if back_idx >= 0:
                            gray = float(tokens[back_idx])
                            new_gray = self._transform_grayscale(gray)

                            # Remove old value
                            for _ in range(i - back_idx):
                                if result:
                                    result.pop()

                            result.append(f"{new_gray:.6f} {token}")
                            i += 1
                            continue
                    except:
                        pass

            # Handle CMYK operators (4 numbers followed by k or K)
            elif token in ('k', 'K'):
                if i >= 8:
                    try:
                        values = []
                        back_idx = i - 1
                        nums_found = 0
                        temp_tokens = []

                        while nums_found < 4 and back_idx >= 0:
                            if tokens[back_idx].strip() and not tokens[back_idx].isspace():
                                try:
                                    val = float(tokens[back_idx])
                                    values.insert(0, val)
                                    temp_tokens.insert(0, back_idx)
                                    nums_found += 1
                                except ValueError:
                                    break
                            back_idx -= 1

                        if nums_found == 4:
                            c, m, y, k_val = values
                            new_c, new_m, new_y, new_k = self._transform_cmyk(c, m, y, k_val)

                            for _ in range(i - temp_tokens[0]):
                                if result:
                                    result.pop()

                            result.append(f"{new_c:.6f} {new_m:.6f} {new_y:.6f} {new_k:.6f} {token}")
                            i += 1
                            continue
                    except:
                        pass

            # Keep token as-is
            result.append(token)
            i += 1

        return ''.join(result)

    def _OLD_apply_color_overlay(self, page: fitz.Page):
        """
        Apply color transformations using PyMuPDF's redaction/overlay features.
        This approach modifies the page appearance while preserving vector data.
        """
        # Get all text blocks with their colors
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" in block:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Get original color
                        orig_color = span.get("color", 0)

                        # Convert integer color to RGB
                        if isinstance(orig_color, int):
                            r = ((orig_color >> 16) & 0xFF) / 255.0
                            g = ((orig_color >> 8) & 0xFF) / 255.0
                            b = (orig_color & 0xFF) / 255.0
                        else:
                            continue

                        # Transform color
                        new_r, new_g, new_b = self._transform_rgb(r, g, b)

                        # Note: PyMuPDF doesn't allow direct text color modification
                        # We need to use a different strategy

        # Better approach: Redraw the page with inverted colors
        # This requires extracting all elements and redrawing them
        # For now, we'll focus on the image transformation and content stream approach
        pass

    def _transform_rgb(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """
        Transform RGB color values for dark mode with HIGH CONTRAST.

        Args:
            r, g, b: RGB values in range [0, 1]

        Returns:
            Transformed RGB values in range [0, 1]
        """
        # Calculate brightness
        brightness = 0.299 * r + 0.587 * g + 0.114 * b

        # If very light (background), set to theme background
        if brightness > 0.95:
            return (
                self.bg_color["r"] / 255.0,
                self.bg_color["g"] / 255.0,
                self.bg_color["b"] / 255.0
            )

        # For dark colors (text and graphics), apply aggressive brightening
        # Pure black or near-black → bright white for maximum contrast
        if brightness < 0.2:
            # Very dark colors → bright white/light colors
            return (0.95, 0.95, 0.95)

        # Medium-dark colors → brighten significantly while preserving hue
        elif brightness < 0.5:
            h, s, v = self._rgb_to_hsv(r, g, b)

            # Aggressive brightening for better contrast
            # Map 0.2-0.5 brightness to 0.7-0.9 brightness
            v = 0.7 + (v - 0.2) * 0.667  # Linear interpolation

            # Slightly reduce saturation for pastels (easier on eyes)
            s = s * 0.8

            return self._hsv_to_rgb(h, s, v)

        # Medium colors → brighten moderately
        else:
            h, s, v = self._rgb_to_hsv(r, g, b)

            # Moderate brightening
            v = 0.6 + v * 0.4
            s = s * 0.9

            return self._hsv_to_rgb(h, s, v)

    def _transform_grayscale(self, gray: float) -> float:
        """Transform grayscale value for dark mode."""
        # Light colors become dark (background)
        if gray > 0.96:
            # Convert theme bg to grayscale
            bg_gray = (0.299 * self.bg_color["r"] +
                      0.587 * self.bg_color["g"] +
                      0.114 * self.bg_color["b"]) / 255.0
            return bg_gray

        # Dark colors become light
        if gray < 0.5:
            return 0.4 + gray * 0.6

        return gray

    def _transform_cmyk(self, c: float, m: float, y: float, k: float) -> Tuple[float, float, float, float]:
        """Transform CMYK color values for dark mode."""
        # Convert CMYK to RGB
        r = (1 - c) * (1 - k)
        g = (1 - m) * (1 - k)
        b = (1 - y) * (1 - k)

        # Transform RGB
        new_r, new_g, new_b = self._transform_rgb(r, g, b)

        # Convert back to CMYK
        if new_r == 0 and new_g == 0 and new_b == 0:
            return 0, 0, 0, 1

        new_k = 1 - max(new_r, new_g, new_b)
        new_c = (1 - new_r - new_k) / (1 - new_k) if new_k < 1 else 0
        new_m = (1 - new_g - new_k) / (1 - new_k) if new_k < 1 else 0
        new_y = (1 - new_b - new_k) / (1 - new_k) if new_k < 1 else 0

        return new_c, new_m, new_y, new_k

    def _OLD_transform_page_images(self, page: fitz.Page, doc: fitz.Document):
        """
        Extract, transform, and re-embed images in the page.
        """
        # Get all images on the page
        image_list = page.get_images(full=True)

        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]  # Image xref number

            try:
                # Extract image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Open with PIL
                img = Image.open(io.BytesIO(image_bytes))

                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Transform pixels
                pixels = img.load()
                width, height = img.size

                for y in range(height):
                    for x in range(width):
                        r, g, b = pixels[x, y]
                        new_r, new_g, new_b = self._transform_rgb(
                            r / 255.0, g / 255.0, b / 255.0
                        )
                        pixels[x, y] = (
                            int(new_r * 255),
                            int(new_g * 255),
                            int(new_b * 255)
                        )

                # Save transformed image to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='PNG')
                img_byte_arr.seek(0)

                # Replace image in PDF
                # Note: PyMuPDF doesn't support in-place image replacement easily
                # We would need to remove the old image and insert the new one
                # This is complex and may require redrawing the page

                # For now, we'll keep the original image approach
                # A full implementation would require more sophisticated handling

            except Exception as e:
                print(f"Warning: Could not process image {xref}: {e}")
                continue

    def _rgb_to_hsv(self, r: float, g: float, b: float) -> Tuple[float, float, float]:
        """Convert RGB to HSV color space."""
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val

        # Hue calculation
        if diff == 0:
            h = 0
        elif max_val == r:
            h = (60 * ((g - b) / diff) + 360) % 360
        elif max_val == g:
            h = (60 * ((b - r) / diff) + 120) % 360
        else:
            h = (60 * ((r - g) / diff) + 240) % 360

        # Saturation calculation
        s = 0 if max_val == 0 else (diff / max_val)

        # Value
        v = max_val

        return h / 360.0, s, v

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[float, float, float]:
        """Convert HSV to RGB color space."""
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
