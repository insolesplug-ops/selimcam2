"""
Generate VISIBLE placeholder assets for testing.
Run this ONCE before first launch.
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_placeholder(path, width, height, text, bg_color, text_color):
    """Create placeholder image with text."""
    img = Image.new('RGBA', (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    try:
        # Try to load a font
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48)
        except:
            font = ImageFont.load_default()
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill=text_color, font=font)
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    print(f"Created: {path}")

# Create directories
os.makedirs("assets/ui", exist_ok=True)
os.makedirs("assets/fonts", exist_ok=True)

print("="*60)
print(" GENERATING VISIBLE PLACEHOLDER ASSETS")
print("="*60)

# SEMI-TRANSPARENT UI overlays (NOT fully transparent!)
# Flash OFF - Dark semi-transparent overlay
create_placeholder("assets/ui/flash off.png", 480, 800, "", 
                  (0, 0, 0, 50), (255, 255, 255))  # 50 alpha = barely visible

# Flash ON - Yellow tint
create_placeholder("assets/ui/flash on.png", 480, 800, "", 
                  (255, 255, 0, 80), (255, 255, 0))  # Yellow overlay

# Flash AUTO - Blue tint
create_placeholder("assets/ui/flash automatically.png", 480, 800, "", 
                  (100, 150, 255, 80), (100, 200, 255))  # Blue overlay

# Bottom bar icons - COMPLETELY TRANSPARENT (icons will be drawn as text)
create_placeholder("assets/ui/gallery.png", 480, 800, "", 
                  (0, 0, 0, 0), (200, 200, 200))

create_placeholder("assets/ui/settings.png", 480, 800, "", 
                  (0, 0, 0, 0), (200, 200, 200))

# Boot logo - SOLID
create_placeholder("assets/ui/boot_logo.png", 200, 200, "CAM", 
                  (30, 30, 30, 255), (255, 255, 255))  # SOLID background

print("\n" + "="*60)
print(" VISIBLE ASSETS GENERATED")
print("="*60)