"""
AI-Powered Animated Sticker Generator
Uses GPT-4o-mini to generate frame prompts → Replicate for images → Animated WebP
"""

import os
import time
import requests
from PIL import Image
from openai import OpenAI
import replicate
from rembg import remove
from dotenv import load_dotenv

load_dotenv()

openai_client = OpenAI()


def generate_frame_prompts(concept: str, num_frames: int = 5) -> list:
    """Use GPT-4o-mini to generate sequential frame prompts."""

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """You are an animation prompt generator. Given a concept, generate sequential frame descriptions for a short animation/transformation.

            Rules:
            - Output ONLY the prompts, one per line, numbered
            - Each prompt must be a complete image description
            - EVERY prompt MUST end with: "sticker style, die-cut, white outline, transparent background, isolated on transparent background, no background, PNG style"
            - Keep consistent style: kawaii, cute
            - Show clear progression/transformation between frames
            - Keep descriptions concise but detailed enough for image generation

            Example for "cat freezing into ice":
            1. cute kawaii cat waving happily, sticker style, die-cut, white outline, transparent background, isolated on transparent background, no background, PNG style
            2. cute kawaii cat starting to turn blue, frost forming on fur, sticker style, die-cut, white outline, transparent background, isolated on transparent background, no background, PNG style
            3. cute kawaii cat half frozen in ice crystals, blue tint, sticker style, die-cut, white outline, transparent background, isolated on transparent background, no background, PNG style
            4. cute kawaii cat mostly frozen, ice chunks forming, sticker style, die-cut, white outline, transparent background, isolated on transparent background, no background, PNG style
            5. cute kawaii cat completely frozen in ice block, frozen pose, sticker style, die-cut, white outline, transparent background, isolated on transparent background, no background, PNG style"""
            },
            {
                "role": "user",
                "content": f"Generate {num_frames} frame prompts for: {concept}"
            }
        ],
        temperature=0.7
    )

    lines = response.choices[0].message.content.strip().split('\n')
    prompts = [line.split('. ', 1)[1] if '. ' in line else line for line in lines if line.strip()]

    print(f"📝 Generated {len(prompts)} frame prompts")
    for i, p in enumerate(prompts):
        print(f"   {i+1}. {p[:60]}...")

    return prompts


def generate_frame_image(prompt: str, index: int, max_retries: int = 3) -> str:
    """Generate single frame using Replicate with retry logic."""
    from rembg import remove

    print(f"🎨 Generating frame {index + 1}...")

    for attempt in range(max_retries):
        try:
            # Wait to avoid rate limiting
            if index > 0 or attempt > 0:
                wait = 12 if attempt == 0 else 15 * (attempt + 1)
                print(f"   ⏳ Waiting {wait}s to avoid rate limit...")
                time.sleep(wait)

            output = replicate.run(
                "fofr/sticker-maker:4acb778eb059772225ec213948f0660867b2e03f277448f18cf1800b96a65a1a",
                input={
                    "prompt": prompt,
                    "steps": 17,
                    "width": 1024,
                    "height": 1024,
                    "output_format": "png",
                    "number_of_images": 1,
                    "negative_prompt": "ugly, blurry, low quality, text, watermark, different style"
                }
            )

            url = output[0] if isinstance(output, list) else output
            if hasattr(url, 'url'):
                url = url.url

            filepath = f"frame_{index}.png"
            response = requests.get(url)
            with open(filepath, "wb") as f:
                f.write(response.content)

            # Remove background to ensure transparency
            print(f"   🔧 Removing background...")
            img = Image.open(filepath)
            img_no_bg = remove(img)
            img_no_bg.save(filepath)

            print(f"   ✅ Frame {index + 1} saved (transparent)")
            return filepath

        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                print(f"   ⚠️ Rate limited, retrying (attempt {attempt + 2}/{max_retries})...")
                continue
            raise

    raise Exception("Max retries exceeded")


def create_animated_sticker(frame_paths: list, output: str = "animated_sticker_newww_03.webp", fps: int = 3):
    """Combine frames into animated WebP for WhatsApp."""

    print("🎬 Creating animated WebP...")

    frames = []
    for path in frame_paths:
        img = Image.open(path).convert('RGBA')
        img = img.resize((512, 512), Image.Resampling.LANCZOS)
        frames.append(img)

    # Add reverse frames for smooth loop
    frames_loop = frames + frames[-2:0:-1]

    duration = 1000 // fps

    frames_loop[0].save(
        output,
        'WEBP',
        save_all=True,
        append_images=frames_loop[1:],
        duration=duration,
        loop=0,
        quality=85
    )

    size_kb = os.path.getsize(output) / 1024
    print(f"✅ Saved: {output} ({size_kb:.0f}KB)")

    # Compress if too large for WhatsApp (max 500KB)
    if size_kb > 1000:
        print("⚠️ File > 500KB, compressing...")
        frames_loop[0].save(
            output,
            'WEBP',
            save_all=True,
            append_images=frames_loop[1:],
            duration=duration,
            loop=0,
            quality=60
        )
        size_kb = os.path.getsize(output) / 1024
        print(f"✅ Compressed to {size_kb:.0f}KB")

    return output


def cleanup_frames(num_frames: int):
    """Delete temporary frame files."""
    for i in range(num_frames):
        filepath = f"frame_{i}.png"
        if os.path.exists(filepath):
            os.remove(filepath)
    print("🧹 Cleaned up temporary files")


def generate_animated_sticker(concept: str, num_frames: int = 5, cleanup: bool = True):
    """Main function: concept → animated sticker."""

    print(f"\n{'='*50}")
    print(f"🚀 Creating animated sticker: '{concept}'")
    print(f"{'='*50}\n")

    # Step 1: Generate prompts with GPT
    prompts = generate_frame_prompts(concept, num_frames)

    # Step 2: Generate each frame with Replicate
    print(f"\n⏱️ This will take ~{num_frames * 15}s due to rate limits\n")
    frame_paths = []
    for i, prompt in enumerate(prompts):
        path = generate_frame_image(prompt, i)
        frame_paths.append(path)

    # Step 3: Combine into animated WebP
    print()
    output = create_animated_sticker(frame_paths)

    # Step 4: Cleanup temp files
    if cleanup:
        cleanup_frames(num_frames)

    print(f"\n{'='*50}")
    print(f"🎉 Done! Your animated sticker: {output}")
    print(f"{'='*50}")
    print("\n📱 To use on WhatsApp:")
    print("   1. Install 'Sticker Maker' from Play Store/App Store")
    print("   2. Create new pack → Import this .webp file")
    print("   3. Add to WhatsApp → Send as sticker!")

    return output


if __name__ == "__main__":
    # Check API keys
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Set OPENAI_API_KEY first!")
        exit(1)
    if not os.environ.get("REPLICATE_API_TOKEN"):
        print("❌ Set REPLICATE_API_TOKEN first!")
        exit(1)

    # Choose your concept
    concept = "a plane landing at airport"

    # Or try these:
    # concept = "a plane landing at airport"
    # concept = "a flower blooming"
    # concept = "day changing to night"
    # concept = "a caterpillar becoming a butterfly"

    generate_animated_sticker(concept, num_frames=5)