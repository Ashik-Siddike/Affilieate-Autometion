"""
card_generator.py
=================
Generates premium 1080x1080 visual assets (quote cards, tips, facts)
for visual platforms like Instagram and Pinterest.
Features:
  - Custom radial gradients (Charcoal, Navy, Emerald, Crimson)
  - Glassmorphic card overlay for readability and premium look
  - Neo-Brutalist offset layout with neon highlight shadows
  - Automatic text wrapping using Pillow draw.textbbox
  - Custom brand watermarks and category tags
"""

import os
import math
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# --- Design Presets (Radial Gradients & Highlights) ---
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

def generate_card(text: str, category_tag: str, brand_name: str, output_path: str, style: str = None) -> str:
    """
    Generates a premium 1080x1080 social media graphic card.
    Args:
        text: The core message/tip/quote to render.
        category_tag: E.g., "PRODUCTIVITY HACK" or "KEYBOARD GUIDE"
        brand_name: E.g., "@whitlogic"
        output_path: Target local file path to save the generated PNG.
        style: Layout style ("glassmorphic", "neo_brutalist" or None for random).
    Returns:
        str: Path to the generated image file.
    """
    canvas_size = (1080, 1080)
    W, H = canvas_size
    
    # Choose random preset color highlight
    preset_name = random.choice(list(COLOR_PRESETS.keys()))
    preset = COLOR_PRESETS[preset_name]
    
    # Select style randomly if not specified
    if style is None:
        style = random.choice(["glassmorphic", "neo_brutalist"])
        
    print(f"[GROWING-AGENT] Card Style: {style} (Color Preset: {preset_name})")
    
    # Define Layout Dimensions
    card_margin = 100
    card_left = card_margin
    card_top = 220
    card_right = W - card_margin
    card_bottom = H - 220
    card_width = card_right - card_left
    card_height = card_bottom - card_top

    if style == "neo_brutalist":
        # 1. Base Canvas - flat obsidian background
        canvas = Image.new("RGB", canvas_size, (16, 16, 18))
        overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 2. Asymmetric Shadow Block (Brutalist style)
        shadow_offset = 15
        draw.rectangle(
            [card_left + shadow_offset, card_top + shadow_offset, card_right + shadow_offset, card_bottom + shadow_offset],
            fill=preset["highlight"] + (180,) # Highlight with transparency
        )
        
        # 3. Main Outer Card
        draw.rectangle(
            [card_left, card_top, card_right, card_bottom],
            fill=(26, 26, 30, 255),
            outline=(255, 255, 255, 255),
            width=4
        )
        
        # 4. Asymmetric Tag pill
        tag_font = _load_font(20, bold=True)
        tag_text = category_tag.upper()
        # Measure text to draw a capsule pill background
        tag_bbox = draw.textbbox((card_left + 45, card_top + 40), tag_text, font=tag_font, anchor="la")
        pad_x, pad_y = 12, 6
        draw.rectangle(
            [tag_bbox[0] - pad_x, tag_bbox[1] - pad_y, tag_bbox[2] + pad_x, tag_bbox[3] + pad_y],
            fill=preset["highlight"] + (255,),
            outline=(0, 0, 0),
            width=2
        )
        draw.text((card_left + 45, card_top + 40), tag_text, font=tag_font, fill=(0, 0, 0), anchor="la")
        
        # 5. Core wrapped text
        text_font = _load_font(36, bold=True)
        max_text_width = card_width - 120
        wrapped_lines = wrap_text(draw, text, text_font, max_text_width)
        
        sample_bbox = draw.textbbox((0, 0), "Test", font=text_font)
        line_height = (sample_bbox[3] - sample_bbox[1]) + 20
        total_text_height = len(wrapped_lines) * line_height
        
        # Shift down to account for top tag pill
        card_center_y = card_top + (card_height / 2)
        start_y = card_center_y - (total_text_height / 2) + 30
        
        for i, line in enumerate(wrapped_lines):
            y_pos = start_y + (i * line_height)
            draw.text((W // 2, y_pos), line, font=text_font, fill=(255, 255, 255, 255), anchor="mm")
            
        # 6. Watermark at bottom
        watermark_font = _load_font(24, bold=True)
        brand_tag = brand_name.lower() if brand_name.startswith("@") else f"@{brand_name.lower()}"
        draw.text((W // 2, H - 120), brand_tag, font=watermark_font, fill=(255, 255, 255, 140), anchor="mm")

    else:
        # Glassmorphic Style (Default)
        # 1. Base Gradient Canvas
        canvas = _build_radial_gradient(canvas_size, preset)
        overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # 2. Glass Card Background
        draw.rounded_rectangle(
            [card_left, card_top, card_right, card_bottom],
            radius=30,
            fill=(255, 255, 255, 12),
            outline=(255, 255, 255, 28),
            width=2
        )
        
        # 3. Category Tag
        tag_font = _load_font(22, bold=True)
        tag_text = f"//  {category_tag.upper()}  //"
        tag_bbox = draw.textbbox((W // 2, card_top + 60), tag_text, font=tag_font, anchor="mm")
        
        draw.line(
            [tag_bbox[0], tag_bbox[3] + 8, tag_bbox[2], tag_bbox[3] + 8],
            fill=preset["highlight"] + (220,),
            width=3
        )
        draw.text((W // 2, card_top + 60), tag_text, font=tag_font, fill=(255, 255, 255, 220), anchor="mm")
        
        # 4. Core Text
        text_font = _load_font(36, bold=True)
        max_text_width = card_width - 120
        wrapped_lines = wrap_text(draw, text, text_font, max_text_width)
        
        sample_bbox = draw.textbbox((0, 0), "Test", font=text_font)
        line_height = (sample_bbox[3] - sample_bbox[1]) + 20
        total_text_height = len(wrapped_lines) * line_height
        
        card_center_y = card_top + (card_height / 2)
        start_y = card_center_y - (total_text_height / 2) + 20
        
        for i, line in enumerate(wrapped_lines):
            y_pos = start_y + (i * line_height)
            draw.text((W // 2, y_pos), line, font=text_font, fill=(255, 255, 255, 255), anchor="mm")
            
        # 5. Watermark
        watermark_font = _load_font(24, bold=True)
        brand_tag = brand_name.lower() if brand_name.startswith("@") else f"@{brand_name.lower()}"
        draw.text((W // 2, H - 120), brand_tag, font=watermark_font, fill=(255, 255, 255, 140), anchor="mm")
        
    # Composite overlay on base canvas
    final_image = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save the card
    final_image.convert("RGB").save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    # Test card generation with both styles
    test_text = "To minimize neck strain, the top of your dual monitors should be at or slightly below eye level."
    generate_card(test_text, "Workspace Setup", "Whitlogic", "output/test_glass.png", style="glassmorphic")
    generate_card(test_text, "Workspace Setup", "Whitlogic", "output/test_brutalist.png", style="neo_brutalist")
    print("Test cards generated successfully in output/")
