"""
FREE Sticker Generator using Pollinations.ai
No API key required! Unlimited generations!
Uses FLUX model for high-quality sticker generation
"""

import os
import io
import math
import requests
import urllib.parse
from PIL import Image as PILImage

# WhatsApp sticker specs
STICKER_SIZE = 512
MAX_FILE_SIZE = 5000 * 1024  # 500KB for animated


def generate_sticker_free(prompt: str, reference_image_path: str = None) -> PILImage.Image:
    """
    Generate a sticker using Pollinations.ai (FREE, no API key!)

    Note: Pollinations doesn't support reference images directly,
    but you can describe the person/style in the prompt.
    """

    # Build sticker-optimized prompt
    sticker_prompt = f"""kawaii chibi sticker design, cute cartoon style, 
bold clean outlines, simple cel-shading, vibrant colors, 
pure white background, centered composition, 
{prompt}, 
sticker art, no text, high quality"""

    params = {
        "width": 512,  # Square for stickers
        "height": 512,
        "seed": 42,  # Change for different results (or use random.randint(1, 99999))
        "model": "flux",  # Best quality model
        "enhance": "true",
        "nologo": "true",  # No watermark
    }

    encoded_prompt = urllib.parse.quote(sticker_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

    print(f"⏳ Generating sticker (FREE via Pollinations.ai)...")
    print(f"   Prompt: {prompt[:50]}...")

    if reference_image_path:
        print(f"⚠ Note: Pollinations doesn't support reference images.")
        print(f"   Describe the person/style in your prompt instead.")

    try:
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()

        # Convert to PIL Image
        image = PILImage.open(io.BytesIO(response.content))
        print("✓ Sticker generated!")
        return image

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to generate image: {e}")


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
            offset_y = int(math.sin(t * 2 * math.pi) * 15)
            pos = ((STICKER_SIZE - image.width) // 2,
                   (STICKER_SIZE - image.height) // 2 + offset_y)
        elif animation == "bounce":
            offset_y = int(abs(math.sin(t * 2 * math.pi)) * 25)
            pos = ((STICKER_SIZE - image.width) // 2,
                   (STICKER_SIZE - image.height) // 2 - offset_y)
        elif animation == "pulse":
            scale = 0.9 + 0.1 * math.sin(t * 2 * math.pi)
            new_size = int(STICKER_SIZE * scale)
            scaled = image.resize((new_size, new_size), PILImage.LANCZOS)
            pos = ((STICKER_SIZE - new_size) // 2, (STICKER_SIZE - new_size) // 2)
            frame.paste(scaled, pos, scaled)
            frames.append(frame)
            continue
        elif animation == "wiggle":
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
    prompt = "cute kawaii cat with floating hearts, happy expression, big eyes"
    animation_type = "float"  # Options: float, bounce, pulse, wiggle, static
    output_file = "whatsapp_sticker_free.webp"
    # ====================================

    # Generate sticker (FREE!)
    sticker_image = generate_sticker_free(prompt)

    # Save raw PNG
    sticker_image.save("sticker_raw.png")
    print(f"✓ Raw image saved: sticker_raw.png")

    # Create animated WebP
    create_animated_webp(sticker_image, animation_type, output_file)

    print("\n" + "=" * 50)
    print("🆓 Generated with Pollinations.ai (FREE!)")
    print("📱 TO USE IN WHATSAPP:")
    print("1. Install 'Sticker Maker' app from Play Store")
    print("2. Create new pack → Import the .webp file")
    print("3. Add to WhatsApp → Send as sticker!")
    print("=" * 50)


# if __name__ == "__main__":
#     main()