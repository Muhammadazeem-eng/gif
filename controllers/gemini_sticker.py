"""
Gemini Sticker Generator - Creates animated WhatsApp stickers
Uses Nano Banana (gemini-2.5-flash-image) for cost efficiency (~$0.039/image)
"""

import os
import io
import math
import base64
from google import genai
from google.genai import types
from PIL import Image as PILImage
from dotenv import load_dotenv

load_dotenv()

# ============== CONFIGURATION ==============
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
# MODEL = "gemini-2.5-flash-image"  # Cheap: ~$0.039/image (vs Pro: ~$0.134+)
MODEL="gemini-3-pro-image-preview"
# WhatsApp sticker specs
STICKER_SIZE = 512
MAX_FILE_SIZE = 500 * 1024  # 500KB for animated


def generate_sticker(prompt: str, reference_image_path: str = None) -> PILImage.Image:
    """Generate a sticker image using Gemini API."""

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build sticker-optimized prompt
    sticker_prompt = f"""Create a kawaii-style sticker with these requirements:
- Style: Cute, chibi, cartoon sticker design
- Features: Bold clean outlines, simple cel-shading, vibrant colors
- Background: Pure white (for transparency removal)
- Size: Square composition, centered subject
- Subject: {prompt}"""

    # Build content (text + optional reference image)
    contents = [sticker_prompt]

    if reference_image_path and os.path.exists(reference_image_path):
        ref_image = PILImage.open(reference_image_path)
        # Convert to bytes for Gemini
        img_buffer = io.BytesIO()
        ref_image.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()

        # Add as inline data
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        print(f"✓ Using reference image: {reference_image_path}")

    print(f"⏳ Generating sticker...")

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
    )

    # Extract image from response
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'inline_data') and part.inline_data is not None:
            # Get raw bytes from inline_data
            image_data = part.inline_data.data

            # Convert bytes to PIL Image
            pil_image = PILImage.open(io.BytesIO(image_data))
            print("✓ Sticker generated!")
            return pil_image
        elif hasattr(part, 'text') and part.text:
            print(f"Model response: {part.text}")

    raise Exception("No image generated")


def remove_white_background(image: PILImage.Image, threshold: int = 240) -> PILImage.Image:
    """Remove white background and make it transparent."""
    image = image.convert("RGBA")
    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (255, 255, 255, 0)  # Transparent

    return image


def create_animated_webp(image: PILImage.Image, animation: str = "float",
                         output_path: str = "sticker.webp") -> str:
    """Create animated WebP sticker for WhatsApp."""

    # Resize to 512x512
    image = image.resize((STICKER_SIZE, STICKER_SIZE), PILImage.LANCZOS)

    # Remove white background
    image = remove_white_background(image)

    # Animation settings
    frames = []
    num_frames = 20
    duration = 67  # ~15fps

    for i in range(num_frames):
        t = i / num_frames
        frame = PILImage.new("RGBA", (STICKER_SIZE, STICKER_SIZE), (0, 0, 0, 0))

        if animation == "float":
            # Gentle floating motion
            offset_y = int(math.sin(t * 2 * math.pi) * 15)
            pos = ((STICKER_SIZE - image.width) // 2,
                   (STICKER_SIZE - image.height) // 2 + offset_y)
        elif animation == "bounce":
            # Bouncing motion
            offset_y = int(abs(math.sin(t * 2 * math.pi)) * 25)
            pos = ((STICKER_SIZE - image.width) // 2,
                   (STICKER_SIZE - image.height) // 2 - offset_y)
        elif animation == "pulse":
            # Pulsing/breathing effect
            scale = 0.9 + 0.1 * math.sin(t * 2 * math.pi)
            new_size = int(STICKER_SIZE * scale)
            scaled = image.resize((new_size, new_size), PILImage.LANCZOS)
            pos = ((STICKER_SIZE - new_size) // 2, (STICKER_SIZE - new_size) // 2)
            frame.paste(scaled, pos, scaled)
            frames.append(frame)
            continue
        elif animation == "wiggle":
            # Rotation wiggle
            angle = math.sin(t * 2 * math.pi) * 8
            rotated = image.rotate(angle, resample=PILImage.BICUBIC, expand=False)
            pos = ((STICKER_SIZE - rotated.width) // 2,
                   (STICKER_SIZE - rotated.height) // 2)
            frame.paste(rotated, pos, rotated)
            frames.append(frame)
            continue
        else:  # static
            pos = ((STICKER_SIZE - image.width) // 2,
                   (STICKER_SIZE - image.height) // 2)

        frame.paste(image, pos, image)
        frames.append(frame)

    # Save as animated WebP
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        format="WEBP",
        quality=85,
        method=6
    )

    # Check file size & compress if needed
    if os.path.getsize(output_path) > MAX_FILE_SIZE:
        print("⚠ Compressing to meet WhatsApp size limit...")
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,
            format="WEBP",
            quality=60,
            method=6
        )

    size_kb = os.path.getsize(output_path) / 1024
    print(f"✓ Saved: {output_path} ({size_kb:.1f} KB)")
    return output_path


def main():
    """Main function - customize your sticker here."""

    # ========== CUSTOMIZE HERE ==========
    prompt = "cute kawaii dancing boy as shown in the reference image the face should be same as in image, happy expression, chibi style"
    reference_image = r"C:\Users\muham\Downloads\WhatsApp Image 2025-10-20 at 4.26.17 PM.jpeg"
    animation_type = "float"  # Options: float, bounce, pulse, wiggle, static
    output_file = "whatsapp_sticker_gem.webp"
    # ====================================

    # Generate sticker
    sticker_image = generate_sticker(prompt, reference_image)

    # Save raw PNG (optional)
    sticker_image.save("sticker_raiiw.png")
    print(f"✓ Raw image saved: sticker_raw2.png")

    # Create animated WebP
    create_animated_webp(sticker_image, animation_type, output_file)

    print("\n" + "=" * 50)
    print("📱 TO USE IN WHATSAPP:")
    print("1. Install 'Sticker Maker' app from Play Store")
    print("2. Create new pack → Import the .webp file")
    print("3. Add to WhatsApp → Send as sticker!")
    print("=" * 50)


