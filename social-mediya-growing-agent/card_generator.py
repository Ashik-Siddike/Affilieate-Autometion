"""
card_generator.py
=================
Generates premium 1080x1080 visual assets (quote cards, tips, facts)
for visual platforms like Instagram and Pinterest.
Features:
  - Custom radial gradients (Charcoal, Navy, Emerald, Crimson)
  - Glassmorphic card overlay for readability and premium look
  - Automatic text wrapping using Pillow draw.textbbox
  - Custom brand watermarks and category tags (e.g. "✦ PRODUCTIVITY TIP")
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- Design Presets (Radial Gradients) ---
COLOR_PRESETS = {
    "charcoal": {
        "center": (40, 44, 52),
        "edge": (15, 17, 20),
        "highlight": (251, 191, 36)  # Amber
    },
    "navy": {
        "center": (28, 36, 60),
        "edge": (8, 12, 24),
        "highlight": (34, 211, 238)  # Cyan
    },
    "emerald": {
        "center": (20, 50, 38),
        "edge": (6, 18, 12),
        "highlight": (52, 211, 153)  # Emerald green
    },
    "crimson": {
        "center": (60, 24, 32),
        "edge": (20, 8, 12),
        "highlight": (248, 113, 113)  # Coral red
    }
}

def _build_radial_gradient(size: tuple[int, int], preset: dict) -> Image.Image:
    """Creates a smooth radial gradient based on center and edge colors."""
    w, h = size
    cx, cy = w / 2, h / 2
    max_radius = math.hypot(cx, cy)

    img = Image.new("RGB", size)
    pixels = img.load()

    rc, gc, bc = preset["center"]
    re, ge, be = preset["edge"]

    for y in range(h):
        for x in range(w):
            dist = math.hypot(x - cx, y - cy)
            t = min(dist / max_radius, 1.0)
            r = int(rc + (re - rc) * t)
            g = int(gc + (ge - gc) * t)
            b = int(bc + (be - bc) * t)
            pixels[x, y] = (r, g, b)

    return img

def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Tries loading modern fonts from system. Falls back to default font."""
    bold_paths = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    regular_paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    paths = bold_paths if bold else regular_paths
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    """Wraps text into multiple lines fit for max_width."""
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        # Use draw.textbbox to get the width of test_line
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def generate_card(text: str, category_tag: str, brand_name: str, output_path: str) -> str:
    """
    Generates a premium 1080x1080 social media graphic card.
    Args:
        text: The core message/tip/quote to render.
        category_tag: E.g., "PRODUCTIVITY HACK" or "KEYBOARD GUIDE"
        brand_name: E.g., "@whitlogic"
        output_path: Target local file path to save the generated PNG.
    Returns:
        str: Path to the generated image file.
    """
    canvas_size = (1080, 1080)
    
    # Choose a random gradient preset
    preset_name = random.choice(list(COLOR_PRESETS.keys()))
    preset = COLOR_PRESETS[preset_name]
    
    # 1. Base Gradient Canvas
    canvas = _build_radial_gradient(canvas_size, preset)
    
    # Prepare transparent overlay for glassmorphic elements and text
    overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    W, H = canvas_size
    
    # 2. Glassmorphic Card dimensions
    card_margin = 100
    card_left = card_margin
    card_top = 220
    card_right = W - card_margin
    card_bottom = H - 220
    card_width = card_right - card_left
    card_height = card_bottom - card_top
    
    # Draw translucent glass card background
    draw.rounded_rectangle(
        [card_left, card_top, card_right, card_bottom],
        radius=30,
        fill=(255, 255, 255, 12),  # Very transparent white
        outline=(255, 255, 255, 28), # Subtle border
        width=2
    )
    
    # 3. Draw Category Tag Badge inside the card
    tag_font = _load_font(22, bold=True)
    tag_text = f"//  {category_tag.upper()}  //"
    tag_bbox = draw.textbbox((W // 2, card_top + 60), tag_text, font=tag_font, anchor="mm")
    
    # Draw a thin highlights underline for the tag badge
    draw.line(
        [tag_bbox[0], tag_bbox[3] + 8, tag_bbox[2], tag_bbox[3] + 8],
        fill=preset["highlight"] + (220,), # Semi-transparent highlight
        width=3
    )
    draw.text((W // 2, card_top + 60), tag_text, font=tag_font, fill=(255, 255, 255, 220), anchor="mm")
    
    # 4. Draw Core Text (Tip / Quote)
    text_font = _load_font(36, bold=True)
    max_text_width = card_width - 120
    wrapped_lines = wrap_text(draw, text, text_font, max_text_width)
    
    # Calculate line heights and vertical centering
    # Let's sample line height
    sample_bbox = draw.textbbox((0, 0), "Quick Test", font=text_font)
    line_height = (sample_bbox[3] - sample_bbox[1]) + 20
    total_text_height = len(wrapped_lines) * line_height
    
    # Starting Y position to center text block vertically inside the card
    card_center_y = card_top + (card_height / 2)
    # Adjust up by half the text block size, and push down slightly to offset the badge
    start_y = card_center_y - (total_text_height / 2) + 20
    
    for i, line in enumerate(wrapped_lines):
        y_pos = start_y + (i * line_height)
        draw.text((W // 2, y_pos), line, font=text_font, fill=(255, 255, 255, 255), anchor="mm")
        
    # 5. Draw Watermark handle at the bottom
    watermark_font = _load_font(24, bold=True)
    brand_tag = brand_name.lower() if brand_name.startswith("@") else f"@{brand_name.lower()}"
    
    # Draw simple clean watermark text at the bottom center of the canvas
    draw.text((W // 2, H - 120), brand_tag, font=watermark_font, fill=(255, 255, 255, 140), anchor="mm")
    
    # 6. Composite overlay on base gradient
    final_image = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the card
    final_image.convert("RGB").save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    # Test card generation
    test_text = "To minimize neck strain, the top of your dual monitors should be at or slightly below eye level, tilted slightly upward."
    generate_card(test_text, "Home Office Hack", "Whitlogic", "output/test_card.png")
    print("Test card generated successfully at output/test_card.png")
