"""
image_composer.py  —  Premium Ad-Style Image Generator
=======================================================
Creative Director spec:
  • 800×800 radial-gradient canvas (Charcoal-Navy centre → Pure Black border)
  • Watch PNG drop-shadow / glow for floating 3D depth
  • "WHIT LOGIC" watermark top-left
  • High-contrast typography overlay (White product name + Amber CTA badge)
  • Text contrast-plate & stroke for readability on any screen
  • Aspect-ratio-safe LANCZOS resize — no distortion
  • Cloudinary upload with graceful raw-URL fallback
"""

import io
import math
import os
import requests
import random
import glob

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import cloudinary
import cloudinary.uploader

from config import CLOUDINARY_URL

try:
    from rembg import remove
    from rembg.session_factory import new_session
    
    # Try models in order of quality (isnet-general-use -> u2net -> u2netp)
    REMBG_SESSION = None
    for model_name in ["isnet-general-use", "u2net", "u2netp"]:
        try:
            print(f"[REMBG] Attempting to load background removal model: {model_name}...")
            REMBG_SESSION = new_session(model_name)
            print(f"[REMBG] Successfully loaded model: {model_name}")
            break
        except Exception as e:
            print(f"[REMBG] Failed to load model {model_name}: {e}")
except Exception as exc:
    print(f"[REMBG] Import failed or general initialization error: {exc}")
    remove = None
    REMBG_SESSION = None

# ── Cloudinary bootstrap ────────────────────────────────────────────────────
if CLOUDINARY_URL:
    cloudinary.config(url=CLOUDINARY_URL)

# ── Design tokens ───────────────────────────────────────────────────────────
CANVAS_SIZE        = (800, 800)
GRAD_CENTER_COLOR  = (28, 32, 48)   # Deep Navy / Charcoal
GRAD_EDGE_COLOR    = (6, 6, 10)     # Near-Black
SHADOW_BLUR_RADIUS = 18
SHADOW_OFFSET      = (12, 14)
SHADOW_OPACITY     = 200            # 0-255
WATERMARK_COLOR    = (255, 255, 255, 140)   # Semi-transparent white
TITLE_COLOR        = (255, 255, 255)
CTA_COLOR          = (251, 191, 36)         # Amber / Neon Yellow
PLATE_COLOR        = (0, 0, 0, 175)         # Translucent dark plate
STROKE_COLOR       = (0, 0, 0)


# ── Internal helpers ─────────────────────────────────────────────────────────

def _build_radial_gradient(size: tuple[int, int]) -> Image.Image:
    """
    Generates a radial gradient Image from GRAD_CENTER_COLOR (centre)
    to GRAD_EDGE_COLOR (edges). Pure Pillow, no NumPy required.
    """
    w, h = size
    cx, cy = w / 2, h / 2
    max_radius = math.hypot(cx, cy)

    img = Image.new("RGB", size)
    pixels = img.load()

    rc, gc, bc = GRAD_CENTER_COLOR
    re, ge, be = GRAD_EDGE_COLOR

    for y in range(h):
        for x in range(w):
            dist = math.hypot(x - cx, y - cy)
            t = min(dist / max_radius, 1.0)          # 0 = centre, 1 = edge
            r = int(rc + (re - rc) * t)
            g = int(gc + (ge - gc) * t)
            b = int(bc + (be - bc) * t)
            pixels[x, y] = (r, g, b)

    return img


def _get_random_background(size: tuple[int, int]) -> Image.Image:
    """
    Returns a random premium background image from assets/backgrounds.
    Falls back to radial gradient if none found or error occurs.
    """
    bg_dir = os.path.join(os.path.dirname(__file__), "assets", "backgrounds")
    if os.path.exists(bg_dir):
        bg_files = glob.glob(os.path.join(bg_dir, "*.png")) + glob.glob(os.path.join(bg_dir, "*.jpg"))
        if bg_files:
            try:
                bg_path = random.choice(bg_files)
                bg = Image.open(bg_path).convert("RGB")
                
                # Scale to cover and center crop
                bg_w, bg_h = bg.size
                target_w, target_h = size
                scale = max(target_w / bg_w, target_h / bg_h)
                new_w, new_h = int(bg_w * scale), int(bg_h * scale)
                bg = bg.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                left = (new_w - target_w) / 2
                top = (new_h - target_h) / 2
                right = (new_w + target_w) / 2
                bottom = (new_h + target_h) / 2
                bg = bg.crop((left, top, right, bottom))
                
                return bg
            except Exception as e:
                print(f"[COMPOSE] Error loading premium background: {e}")
                
    return _build_radial_gradient(size)

def _add_drop_shadow(watch_img: Image.Image) -> Image.Image:
    """
    Creates a blurred black shadow layer beneath the watch.
    Returns a new RGBA image with shadow composited under the watch.
    """
    # Shadow canvas same size as watch image
    shadow = Image.new("RGBA", watch_img.size, (0, 0, 0, 0))

    # Extract alpha mask from watch (or create a solid mask for non-RGBA)
    if watch_img.mode == "RGBA":
        alpha = watch_img.split()[3]
    else:
        alpha = Image.new("L", watch_img.size, 255)

    # Black fill at the shape of the watch
    shadow_fill = Image.new("RGBA", watch_img.size, (0, 0, 0, SHADOW_OPACITY))
    shadow.paste(shadow_fill, mask=alpha)

    # Blur the shadow
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR_RADIUS))

    # Compose: shadow first, then watch on top (with offset)
    composed_w = watch_img.width  + abs(SHADOW_OFFSET[0])
    composed_h = watch_img.height + abs(SHADOW_OFFSET[1])
    composed = Image.new("RGBA", (composed_w, composed_h), (0, 0, 0, 0))

    sx = max(SHADOW_OFFSET[0], 0)
    sy = max(SHADOW_OFFSET[1], 0)
    wx = max(-SHADOW_OFFSET[0], 0)
    wy = max(-SHADOW_OFFSET[1], 0)

    composed.paste(shadow, (sx, sy), shadow)
    if watch_img.mode == "RGBA":
        composed.paste(watch_img, (wx, wy), watch_img)
    else:
        composed.paste(watch_img, (wx, wy))

    return composed


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """
    Tries to load a clean system font. Falls back to Pillow default if absent.
    Bold/Regular variants attempted in order.
    """
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/calibrib.ttf",
        "C:/Windows/Fonts/trebucbd.ttf",
    ]
    regular_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/trebuc.ttf",
    ]
    paths = bold_paths if bold else regular_paths
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_stroked_text(
    draw: ImageDraw.ImageDraw,
    pos: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple,
    stroke_width: int = 2,
    stroke_fill: tuple = STROKE_COLOR,
    anchor: str = "mm",
) -> None:
    """Draws text with an outer stroke for maximum readability."""
    x, y = pos
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font,
                          fill=stroke_fill, anchor=anchor)
    draw.text(pos, text, font=font, fill=fill, anchor=anchor)


def _draw_watermark(canvas: Image.Image) -> None:
    """Stamps the 'WHIT LOGIC' watermark at the top-left."""
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    font    = _load_font(20, bold=True)

    # Small amber accent dot + brand name
    draw.ellipse([16, 14, 28, 26], fill=(251, 191, 36, 200))
    draw.text((34, 20), "WHIT LOGIC", font=font,
              fill=WATERMARK_COLOR, anchor="lm")

    canvas.paste(Image.alpha_composite(
        canvas.convert("RGBA"), overlay).convert("RGB"))


def _draw_text_overlay(canvas: Image.Image, title: str) -> None:
    """
    Renders a translucent dark plate at the bottom with:
      • Product name  — Pure White, bold
      • CTA badge     — Amber "BEST BUDGET TACTICAL WATCH"
    """
    if not title:
        return

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    W, H = canvas.size
    plate_h = 150
    plate_top = H - plate_h

    # Draw translucent plate
    draw.rectangle([0, plate_top, W, H], fill=PLATE_COLOR)

    # Thin amber accent line at top of plate
    draw.rectangle([0, plate_top, W, plate_top + 3], fill=(251, 191, 36, 255))

    # ── CTA badge (amber pill) ───────────────────────────────────────────
    badge_text  = "✦  BEST BUDGET TACTICAL WATCH  ✦"
    badge_font  = _load_font(15, bold=True)
    badge_y     = plate_top + 28

    # Pill background
    bbox = draw.textbbox((W // 2, badge_y), badge_text,
                         font=badge_font, anchor="mm")
    pad = 8
    draw.rounded_rectangle(
        [bbox[0] - pad, bbox[1] - 4, bbox[2] + pad, bbox[3] + 4],
        radius=14, fill=(251, 191, 36, 230),
    )
    draw.text((W // 2, badge_y), badge_text, font=badge_font,
              fill=(15, 15, 20), anchor="mm")

    # ── Product title (white, bold, wrapping) ────────────────────────────
    title_font = _load_font(22, bold=True)
    # Truncate long titles gracefully
    max_chars = 52
    display_title = title[:max_chars].rsplit(" ", 1)[0] + "…" \
        if len(title) > max_chars else title
    display_title = display_title.upper()

    title_y = plate_top + 72
    _draw_stroked_text(
        draw, (W // 2, title_y), display_title,
        font=title_font, fill=TITLE_COLOR,
        stroke_width=2, anchor="mm",
    )

    # ── "Review on whitlogic.online" footer micro-text ───────────────────
    micro_font = _load_font(14)
    draw.text(
        (W // 2, H - 20),
        "Full Review → whitlogic.online",
        font=micro_font, fill=(200, 200, 200, 180), anchor="mm",
    )

    # Merge overlay onto canvas
    merged = Image.alpha_composite(canvas.convert("RGBA"), overlay)
    canvas.paste(merged.convert("RGB"))


# ── Public API ───────────────────────────────────────────────────────────────

def compose_image(raw_image_url: str, title: str = "") -> str:
    """
    Downloads a product image, composes a premium 800×800 ad-style graphic,
    uploads to Cloudinary, and returns the CDN URL.

    Falls back gracefully to `raw_image_url` on any error.

    Args:
        raw_image_url : Source product image URL (Amazon / any CDN)
        title         : Product name for the bottom typography overlay

    Returns:
        str: Cloudinary secure URL, or raw_image_url on failure.
    """
    if not CLOUDINARY_URL:
        print("[COMPOSE] Cloudinary not configured. Using raw URL.")
        return raw_image_url

    try:
        print(f"[COMPOSE] Starting premium composition → {raw_image_url[:60]}…")

        # ── 1. Download source image ─────────────────────────────────────
        resp = requests.get(raw_image_url, timeout=15)
        resp.raise_for_status()
        source_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")

        # ── Background Removal (rembg) ───────────────────────────────────
        if remove and REMBG_SESSION:
            print("[COMPOSE] Applying AI background removal...")
            source_img = remove(source_img, session=REMBG_SESSION)

        # ── 2. Aspect-ratio-safe resize (LANCZOS, no distortion) ─────────
        source_img.thumbnail(
            (580, 580),                     # max product area within 800×800
            Image.Resampling.LANCZOS,
        )

        # ── 3. Drop-shadow / glow ────────────────────────────────────────
        shadowed = _add_drop_shadow(source_img)

        # ── 4. Premium Lifestyle Canvas ──────────────────────────────────
        canvas = _get_random_background(CANVAS_SIZE)

        # ── 5. Centre-paste the shadowed watch ───────────────────────────
        # Convert canvas to RGBA for compositing
        canvas_rgba = canvas.convert("RGBA")
        sx = (CANVAS_SIZE[0] - shadowed.width)  // 2
        sy = (CANVAS_SIZE[1] - shadowed.height) // 2 - 20  # slight upward shift
        canvas_rgba.paste(shadowed, (sx, sy), shadowed)
        canvas = canvas_rgba.convert("RGB")

        # ── 6. Watermark ─────────────────────────────────────────────────
        _draw_watermark(canvas)

        # ── 7. Text overlay ──────────────────────────────────────────────
        _draw_text_overlay(canvas, title)

        # ── 8. Encode to JPEG bytes ──────────────────────────────────────
        buf = io.BytesIO()
        canvas.save(buf, format="JPEG", quality=92, optimize=True)
        buf.seek(0)

        # ── 9. Upload to Cloudinary ──────────────────────────────────────
        result = cloudinary.uploader.upload(
            buf,
            folder="whitlogic/composed",
            public_id=f"ad_{abs(hash(raw_image_url))}",
            overwrite=True,
            resource_type="image",
        )
        cdn_url = result.get("secure_url")
        if not cdn_url:
            raise ValueError("Cloudinary returned no secure_url.")

        print(f"[COMPOSE] ✅ Premium image ready → {cdn_url}")
        return cdn_url

    except cloudinary.exceptions.Error as ce:
        print(f"[COMPOSE] Cloudinary API error (fallback): {ce}")
        return raw_image_url
    except Exception as exc:
        print(f"[COMPOSE] Composition failed ({exc}). Falling back to raw URL.")
        return raw_image_url

def compose_pinterest_image(raw_image_url: str, title: str = "") -> str:
    """
    Downloads a product image, composes a 1000x1500 Pinterest-optimized graphic,
    uploads to Cloudinary, and returns the CDN URL.
    """
    if not CLOUDINARY_URL:
        return raw_image_url

    try:
        resp = requests.get(raw_image_url, timeout=15)
        resp.raise_for_status()
        source_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")

        # ── Background Removal (rembg) ───────────────────────────────────
        if remove and REMBG_SESSION:
            print("[COMPOSE] Applying AI background removal...")
            source_img = remove(source_img, session=REMBG_SESSION)

        # Resize to fit within 800x800 for the center of Pinterest image
        source_img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        shadowed = _add_drop_shadow(source_img)

        # 1000x1500 canvas
        canvas = _get_random_background((1000, 1500))
        
        canvas_rgba = canvas.convert("RGBA")
        
        # Center the shadowed watch
        sx = (1000 - shadowed.width) // 2
        sy = (1500 - shadowed.height) // 2
        canvas_rgba.paste(shadowed, (sx, sy), shadowed)
        
        canvas = canvas_rgba.convert("RGB")
        draw = ImageDraw.Draw(canvas)

        # Top text
        top_font = _load_font(48, bold=True)
        _draw_stroked_text(draw, (500, 150), "EXPERT REVIEW", font=top_font, fill=(251, 191, 36), stroke_width=3, anchor="mm")

        # Bottom Plate
        plate_h = 300
        plate_top = 1500 - plate_h
        
        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rectangle([0, plate_top, 1000, 1500], fill=PLATE_COLOR)
        overlay_draw.rectangle([0, plate_top, 1000, plate_top + 4], fill=(251, 191, 36, 255))
        
        # Button/CTA
        btn_font = _load_font(24, bold=True)
        overlay_draw.rounded_rectangle([350, plate_top + 180, 650, plate_top + 240], radius=30, fill=(251, 191, 36))
        overlay_draw.text((500, plate_top + 210), "Read Full Review", font=btn_font, fill=(0,0,0), anchor="mm")
        
        canvas.paste(Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB"))
        draw = ImageDraw.Draw(canvas)
        
        # Title in the bottom plate
        title_font = _load_font(36, bold=True)
        max_chars = 60
        display_title = title[:max_chars].rsplit(" ", 1)[0] + "…" if len(title) > max_chars else title
        display_title = display_title.upper()
        
        _draw_stroked_text(draw, (500, plate_top + 100), display_title, font=title_font, fill=(255,255,255), stroke_width=2, anchor="mm")

        # Encode & Upload
        buf = io.BytesIO()
        canvas.save(buf, format="JPEG", quality=90, optimize=True)
        buf.seek(0)

        result = cloudinary.uploader.upload(
            buf,
            folder="whitlogic/pinterest",
            public_id=f"pin_{abs(hash(raw_image_url))}",
            overwrite=True,
            resource_type="image",
        )
        print(f"[COMPOSE] ✅ Pinterest image ready → {result.get('secure_url')}")
        return result.get("secure_url", raw_image_url)

    except Exception as exc:
        print(f"[COMPOSE] Pinterest composition failed ({exc}).")
        return raw_image_url

