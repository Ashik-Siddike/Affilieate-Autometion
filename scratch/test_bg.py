from PIL import Image, ImageDraw
import requests
import io
import math

def remove_white_bg(img: Image.Image, tolerance: int = 240) -> Image.Image:
    """Removes the white background using a simple flood-fill approach from the edges."""
    img = img.convert("RGBA")
    
    # Create a mask for the floodfill
    # To use PIL's ImageDraw.floodfill, we need a standard image, let's use an RGB copy
    rgb_img = img.convert("RGB")
    
    # We will floodfill with a magic color (e.g. magenta) from the corners
    magic_color = (255, 0, 255)
    
    # Threshold for what is considered "white background"
    # Actually, PIL's floodfill has a 'value' and 'thresh' parameter in newer versions, but we can do a simple manual BFS if needed.
    
    width, height = img.size
    pixels = img.load()
    
    # Simple BFS to find contiguous near-white pixels from the borders
    visited = set()
    queue = []
    
    # Add borders to queue
    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))
        
    def is_white(c):
        return c[0] >= tolerance and c[1] >= tolerance and c[2] >= tolerance

    # Filter initial queue to only start from white pixels
    valid_queue = []
    for (x, y) in queue:
        if (x, y) not in visited and is_white(pixels[x, y]):
            valid_queue.append((x, y))
            visited.add((x, y))
            pixels[x, y] = (pixels[x,y][0], pixels[x,y][1], pixels[x,y][2], 0)
            
    # BFS
    while valid_queue:
        cx, cy = valid_queue.pop(0)
        
        for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
            if 0 <= nx < width and 0 <= ny < height:
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    if is_white(pixels[nx, ny]):
                        pixels[nx, ny] = (pixels[nx,ny][0], pixels[nx,ny][1], pixels[nx,ny][2], 0)
                        valid_queue.append((nx, ny))
                        
    return img

def test():
    print("Downloading test image...")
    # Example Amazon image URL
    url = "https://m.media-amazon.com/images/I/61b1m2619FL._AC_SL1500_.jpg"
    resp = requests.get(url)
    img = Image.open(io.BytesIO(resp.content))
    
    print("Processing...")
    bg_removed = remove_white_bg(img)
    bg_removed.save("test_out.png")
    print("Done. Saved as test_out.png")

if __name__ == "__main__":
    test()
