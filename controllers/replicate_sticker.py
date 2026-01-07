"""
WhatsApp Animated Sticker Generator
====================================
Generates proper animated WebP stickers for WhatsApp.

Usage:
    set REPLICATE_API_TOKEN=your_token
    python whatsapp_sticker.py
"""

import os
import math
import requests
from PIL import Image
from dotenv import load_dotenv
import replicate

load_dotenv()


def generate_sticker(prompt: str) -> str:
    """Generate static sticker image from prompt."""
    print(f"🎨 Generating: {prompt}")

    output = replicate.run(
        "fofr/sticker-maker:4acb778eb059772225ec213948f0660867b2e03f277448f18cf1800b96a65a1a",
        input={
            "prompt": f"{prompt}, kawaii style, cute, sticker, die-cut",
            "steps": 17,
            "width": 1152,
            "height": 1152,
            "output_format": "png",
            "number_of_images": 1,
            "negative_prompt": "ugly, blurry, low quality, text, watermark"
        }
    )

    # Download image
    url = output[0] if isinstance(output, list) else output
    if hasattr(url, 'url'):
        url = url.url

    response = requests.get(url)
    with open("temp_sticker.png", "wb") as f:
        f.write(response.content)

    print("✅ Sticker generated")
    return "temp_sticker.png"


def create_animated_webp(image_path: str, output_path: str = "sticker.webp",
                         animation: str = "bounce", frames: int = 20, fps: int = 15):
    """
    Create animated WebP for WhatsApp.

    WhatsApp requirements:
    - 512x512 pixels
    - Animated WebP format
    - Max 500KB
    - Transparent background
    """
    print(f"🎬 Creating {animation} animation...")

    img = Image.open(image_path).convert('RGBA')
    img = img.resize((512, 512), Image.Resampling.LANCZOS)

    animated_frames = []
    duration = 1000 // fps  # ms per frame

    for i in range(frames):
        progress = i / frames
        angle = progress * 2 * math.pi

        if animation == "bounce":
            # Bounce up and down
            offset = int(25 * abs(math.sin(angle)))
            frame = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
            small = img.resize((480, 480), Image.Resampling.LANCZOS)
            frame.paste(small, (16, 32 - offset), small)

        elif animation == "shake":
            # Shake left-right
            offset = int(15 * math.sin(angle * 2))
            frame = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
            small = img.resize((480, 480), Image.Resampling.LANCZOS)
            frame.paste(small, (16 + offset, 16), small)

        elif animation == "pulse":
            # Grow and shrink
            scale = 0.85 + 0.15 * abs(math.sin(angle))
            new_size = int(512 * scale)
            scaled = img.resize((new_size, new_size), Image.Resampling.LANCZOS)
            frame = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
            offset = (512 - new_size) // 2
            frame.paste(scaled, (offset, offset), scaled)

        elif animation == "wiggle":
            # Rotate back and forth
            rotation = 8 * math.sin(angle * 2)
            rotated = img.rotate(rotation, resample=Image.Resampling.BICUBIC, expand=False)
            frame = rotated.resize((512, 512), Image.Resampling.LANCZOS)

        else:
            frame = img.copy()

        animated_frames.append(frame)

    # Save as animated WebP
    animated_frames[0].save(
        output_path,
        'WEBP',
        save_all=True,
        append_images=animated_frames[1:],
        duration=duration,
        loop=0,
        quality=90,
        method=6
    )

    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Animated sticker saved: {output_path} ({size_kb:.0f}KB)")

    if size_kb > 1500:
        print("⚠️ File > 500KB, compressing...")
        compress_webp(output_path, animated_frames, duration)

    return output_path


def compress_webp(path: str, frames: list, duration: int):
    """Compress if file too large."""
    # Reduce quality
    frames[0].save(
        path, 'WEBP',
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        quality=70,
        method=6
    )
    size_kb = os.path.getsize(path) / 1024
    print(f"✅ Compressed to {size_kb:.0f}KB")


def main():
    print("\n🐱 WhatsApp Animated Sticker Generator\n")

    # Check API token
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("❌ Set REPLICATE_API_TOKEN first!")
        print("   Windows: set REPLICATE_API_TOKEN=r8_xxx")
        return

    # Generate sticker
    prompt = "a baby is flying in the air"
    image_path = generate_sticker(prompt)

    # Create animated WebP
    output = create_animated_webp(
        image_path,
        output_path="whatsapp_sticker.webp",
        animation="bounce",  # bounce, shake, pulse, wiggle
        frames=20,
        fps=15
    )



    print(f"\n🎉 Done! Send '{output}' to WhatsApp via Sticker Maker app")
    print("\n📱 To use on WhatsApp:")
    print("   1. Install 'Sticker Maker' from Play Store")
    print("   2. Create new pack → Import this .webp file")
    print("   3. Add to WhatsApp → Send as sticker!")

