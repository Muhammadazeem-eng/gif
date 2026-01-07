"""
Gemini Animated Sticker Generator
Uses GPT-4o-mini for frame prompts → Gemini for image generation → rembg for transparency → Animated WebP
"""

import os
import io
import time
from google import genai
from google.genai import types
from PIL import Image as PILImage
from openai import OpenAI
from rembg import remove
from dotenv import load_dotenv

load_dotenv()

# ============== CONFIGURATION ==============
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.0-flash-exp-image-generation"

# WhatsApp sticker specs
STICKER_SIZE = 512
MAX_FILE_SIZE = 500 * 1024  # 500KB

openai_client = OpenAI()


def generate_frame_prompts(concept: str, num_frames: int = 3) -> list:
    """Use GPT-4o-mini to generate detailed sequential frame prompts."""

    print(f"📝 Generating {num_frames} detailed frame prompts...")

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are an expert animation prompt generator for AI image generation. Given a concept, generate highly detailed sequential frame descriptions for a short animation/transformation.

Rules:
- Output ONLY the prompts, one per line, numbered
- Each prompt must be VERY DETAILED (50-100 words) describing:
  * Exact pose and body position
  * Facial expression details
  * Colors and lighting
  * Any effects or particles
  * Stage of transformation/animation
- Keep CONSISTENT elements across all frames: same character design, same art style, same colors
- Style keywords to ALWAYS include at the end: "kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background"
- Show clear progression/transformation between frames
- If it's a character, keep the character design IDENTICAL across frames, only change pose/expression/effects

Example for "cat freezing into ice" (3 frames):
1. Adorable kawaii chibi cat standing upright with arms slightly raised, round body, big sparkling eyes with highlight dots, small pink nose, happy open-mouth smile showing tiny tongue, soft orange fur with cream chest patch, short stubby legs, fluffy tail curled upward, surrounded by tiny blue sparkles starting to appear, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background

2. Same adorable kawaii chibi cat now with surprised expression, eyes wide as saucers with shrunk pupils, small 'o' shaped mouth, fur starting to turn light blue from the paws upward, ice crystals forming on ears and tail tip, frost particles floating around body, small icicles beginning to form under arms, same orange and cream colors on upper body transitioning to icy blue on lower body, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background

3. Same kawaii chibi cat now completely transformed into beautiful ice sculpture, entire body crystalline ice blue with white highlights, frozen in cute pose with paws up, eyes now sparkly ice gems with star reflections, translucent icy texture throughout, snowflakes and ice crystals floating around, small frozen breath puff near mouth, standing on tiny ice puddle, maintaining same cute chibi proportions, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background"""
            },
            {
                "role": "user",
                "content": f"Generate {num_frames} highly detailed frame prompts for: {concept}"
            }
        ],
        temperature=0.7
    )

    lines = response.choices[0].message.content.strip().split('\n')
    prompts = [line.split('. ', 1)[1] if '. ' in line else line for line in lines if line.strip()]

    print(f"✅ Generated {len(prompts)} frame prompts:")
    for i, p in enumerate(prompts):
        print(f"   Frame {i + 1}: {p[:80]}...")

    return prompts


def generate_sticker_frame(prompt: str, frame_index: int, reference_image_path: str = None) -> PILImage.Image:
    """Generate a single sticker frame using Gemini API."""

    client = genai.Client(api_key=GEMINI_API_KEY)

    full_prompt = f"""Create a sticker image with these EXACT requirements:

IMAGE REQUIREMENTS:
- Style: Kawaii chibi cartoon sticker
- Outlines: Bold clean black outlines
- Shading: Simple cel-shading, flat colors
- Background: Plain solid white background
- Composition: Square, subject centered, no cropping
- Quality: High detail, clean edges

SUBJECT TO DRAW:
{prompt}

IMPORTANT: Use a plain solid white background. Do not use checkered or patterned backgrounds."""

    contents = [full_prompt]

    if reference_image_path and os.path.exists(reference_image_path):
        ref_image = PILImage.open(reference_image_path)
        img_buffer = io.BytesIO()
        ref_image.save(img_buffer, format='JPEG')
        img_bytes = img_buffer.getvalue()
        contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
        if frame_index == 0:
            print(f"   📷 Using reference image: {reference_image_path}")

    print(f"   🎨 Generating frame {frame_index + 1}...")

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=['Text', 'Image']
        )
    )

    for part in response.candidates[0].content.parts:
        if hasattr(part, 'inline_data') and part.inline_data is not None:
            image_data = part.inline_data.data
            pil_image = PILImage.open(io.BytesIO(image_data))
            print(f"   ✅ Frame {frame_index + 1} generated!")
            return pil_image

    raise Exception(f"No image generated for frame {frame_index + 1}")


def create_animated_webp(frames: list, output_path: str = "sticker.webp", fps: int = 3) -> str:
    """Create animated WebP sticker from multiple frames with background removal."""

    print("🎬 Creating animated WebP...")

    processed_frames = []
    for i, frame in enumerate(frames):
        # Remove background using rembg
        print(f"   🔧 Removing background from frame {i + 1}...")
        frame = remove(frame)

        # Convert and resize
        frame = frame.convert("RGBA")
        frame = frame.resize((STICKER_SIZE, STICKER_SIZE), PILImage.LANCZOS)
        processed_frames.append(frame)

    # Create smooth loop: 1→2→3→2→1
    frames_loop = processed_frames + processed_frames[-2:0:-1]

    duration = 1000 // fps

    frames_loop[0].save(
        output_path,
        save_all=True,
        append_images=frames_loop[1:],
        duration=duration,
        loop=0,
        format="WEBP",
        quality=85,
        method=6
    )

    if os.path.getsize(output_path) > MAX_FILE_SIZE:
        print("⚠️ Compressing to meet WhatsApp size limit...")
        frames_loop[0].save(
            output_path,
            save_all=True,
            append_images=frames_loop[1:],
            duration=duration,
            loop=0,
            format="WEBP",
            quality=60,
            method=6
        )

    size_kb = os.path.getsize(output_path) / 1024
    print(f"✅ Saved: {output_path} ({size_kb:.1f} KB)")
    return output_path


def generate_animated_sticker(
        concept: str,
        reference_image: str = None,
        num_frames: int = 3,
        fps: int = 3,
        output_file: str = "animated_sticker.webp",
        save_raw_frames: bool = False
):
    """Main function: concept → animated sticker."""

    print(f"\n{'=' * 50}")
    print(f"🚀 Creating animated sticker: '{concept}'")
    if reference_image:
        print(f"📷 Reference image: {reference_image}")
    print(f"{'=' * 50}\n")

    # Step 1: Generate detailed prompts with GPT
    prompts = generate_frame_prompts(concept, num_frames)

    # Step 2: Generate each frame with Gemini
    print(f"\n🎨 Generating {len(prompts)} frames with Gemini...\n")
    frames = []
    for i, prompt in enumerate(prompts):
        if i > 0:
            print("   ⏳ Waiting 5s...")
            time.sleep(5)

        frame = generate_sticker_frame(prompt, i, reference_image)
        frames.append(frame)

        if save_raw_frames:
            frame.save(f"frame_{i + 1}_raw.png")
            print(f"   💾 Saved: frame_{i + 1}_raw.png")

    # Step 3: Create animated WebP with background removal
    print()
    output = create_animated_webp(frames, output_file, fps)

    print(f"\n{'=' * 50}")
    print(f"🎉 Done! Your animated sticker: {output}")
    print(f"{'=' * 50}")
    print("\n📱 TO USE IN WHATSAPP:")
    print("   1. Install 'Sticker Maker' app from Play Store")
    print("   2. Create new pack → Import the .webp file")
    print("   3. Add to WhatsApp → Send as sticker!")

    return output


if __name__ == "__main__":
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY first!")
        exit(1)
    if not GEMINI_API_KEY:
        print("❌ Set GEMINI_API_KEY first!")
        exit(1)

    # ========== CUSTOMIZE HERE ==========
    concept = "a cute boy transforming into frozen ice"
    reference_image = r"C:\Users\muham\Downloads\Generated Image October 23, 2025 - 2_51PM.jpeg"  # or r"C:\path\to\image.jpg"
    num_frames = 3
    fps = 3
    output_file = "04_whatsapp_sticker.webp"
    save_raw_frames = True
    # ====================================

    generate_animated_sticker(
        concept=concept,
        reference_image=reference_image,
        num_frames=num_frames,
        fps=fps,
        output_file=output_file,
        save_raw_frames=save_raw_frames
    )