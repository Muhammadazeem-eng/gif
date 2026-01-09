"""
FREE Animated Sticker Generator
Uses GPT-4o-mini for frame prompts → Pollinations.ai (FREE) for images → rembg for transparency → Animated WebP
"""

import os
import io
import time
import random
import requests
import urllib.parse
from PIL import Image as PILImage
from openai import OpenAI
from rembg import remove
from dotenv import load_dotenv

load_dotenv()

# WhatsApp sticker specs
STICKER_SIZE = 512
MAX_FILE_SIZE = 500 * 1024  # 500KB

openai_client = OpenAI()


def generate_frame_prompts(concept: str, num_frames: int = 5) -> list:
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
- Style keywords to ALWAYS include at the end: "kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background, no text"
- Show clear progression/transformation between frames
- If it's a character, keep the character design IDENTICAL across frames, only change pose/expression/effects

Example for "cat freezing into ice" (5 frames):
1. Adorable kawaii chibi cat standing upright with arms slightly raised, round body, big sparkling eyes with highlight dots, small pink nose, happy open-mouth smile showing tiny tongue, soft orange fur with cream chest patch, short stubby legs, fluffy tail curled upward, normal happy pose, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background, no text

2. Same adorable kawaii chibi cat with slightly worried expression, eyes a bit wider, tiny blue sparkles starting to appear around paws, fur color unchanged, same orange and cream colors, hint of frost forming at feet, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background, no text

3. Same kawaii chibi cat now with surprised expression, eyes wide as saucers with shrunk pupils, small 'o' shaped mouth, fur starting to turn light blue from the paws upward, ice crystals forming on ears and tail tip, frost particles floating around body, small icicles beginning to form under arms, same orange and cream colors on upper body transitioning to icy blue on lower body, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background, no text

4. Same kawaii chibi cat mostly frozen, body 70% crystalline ice blue, only face and chest still showing orange fur, frozen pose with paws up, large ice crystals on ears and tail, snowflakes swirling around, icicles hanging from arms, expression frozen in cute surprise, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background, no text

5. Same kawaii chibi cat now completely transformed into beautiful ice sculpture, entire body crystalline ice blue with white highlights, frozen in cute pose with paws up, eyes now sparkly ice gems with star reflections, translucent icy texture throughout, snowflakes and ice crystals floating around, small frozen breath puff near mouth, standing on tiny ice puddle, maintaining same cute chibi proportions, kawaii chibi style, cute cartoon sticker, bold black outlines, cel-shaded, vibrant colors, simple clean design, centered composition, solid white background, no text"""
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
        print(f"   Frame {i + 1}: {p[:70]}...")

    return prompts


def generate_frame_pollinations(prompt: str, frame_index: int, seed: int = None) -> PILImage.Image:
    """Generate a single frame using Pollinations.ai (FREE!)."""

    if seed is None:
        seed = random.randint(1, 99999)

    # Enhanced prompt for better sticker quality
    full_prompt = f"""{prompt}, 
high quality illustration, clean artwork, professional sticker design, 
centered subject, full body visible, no cropping"""

    params = {
        "width": 512,
        "height": 512,
        "seed": seed,
        "model": "flux",
        "enhance": "true",
        "nologo": "true",
    }

    encoded_prompt = urllib.parse.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"

    print(f"   🎨 Generating frame {frame_index + 1} (seed: {seed})...")

    try:
        response = requests.get(url, params=params, timeout=120)
        response.raise_for_status()
        image = PILImage.open(io.BytesIO(response.content))
        print(f"   ✅ Frame {frame_index + 1} generated!")
        return image

    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to generate frame {frame_index + 1}: {e}")


def create_animated_webp(frames: list, output_path: str = "sticker.webp", fps: int = 4) -> str:
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

    # Create smooth loop: 1→2→3→4→5→4→3→2→1
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
    num_frames: int,
    fps: int = 4,
    output_file: str = "animated_sticker.webp",
    save_raw_frames: bool = False,
    base_seed: int = None
) -> str:
    """
    User-controlled animated sticker generation.

    Flow:
    concept → GPT generates N prompts → Pollinations generates N images
    → background removed → combined into animated WebP
    """

    # 🔒 Safety clamp (allow up to 15 frames)
    num_frames = max(2, min(num_frames, 6))

    print(f"\n{'='*60}")
    print(f"🆓 FREE Animated Sticker Generator")
    print(f"{'='*60}")
    print(f"🎨 Concept: {concept}")
    print(f"🧩 Frames: {num_frames}")
    print(f"🎞 FPS: {fps}")
    print(f"{'='*60}\n")

    # Base seed for style consistency
    if base_seed is None:
        base_seed = random.randint(1, 99999)
    print(f"🎲 Base seed: {base_seed}\n")

    # 1️⃣ Generate frame prompts
    prompts = generate_frame_prompts(concept, num_frames)

    if len(prompts) != num_frames:
        raise Exception(
            f"Expected {num_frames} prompts, got {len(prompts)}"
        )

    # 2️⃣ Generate frames (NO delay)
    frames = []
    for i, prompt in enumerate(prompts):
        frame_seed = base_seed + i
        frame = generate_frame_pollinations(
            prompt=prompt,
            frame_index=i,
            seed=frame_seed
        )
        frames.append(frame)

        if save_raw_frames:
            frame.save(f"frame_{i + 1}_raw.png")

    # 3️⃣ Create animated WebP
    output = create_animated_webp(
        frames=frames,
        output_path=output_file,
        fps=fps
    )

    print(f"\n{'='*60}")
    print(f"🎉 Sticker created: {output}")
    print(f"{'='*60}")

    return output


