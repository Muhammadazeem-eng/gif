"""
Controller for Runware Video Generation
Returns both original MP4 and transparent WebP
"""

import os
import uuid
import asyncio
import requests
from typing import Optional, Tuple

from runware import Runware, IVideoInference
from moviepy import VideoFileClip
from PIL import Image
from rembg import remove
from dotenv import load_dotenv

load_dotenv()


async def generate_runware_transparent_sticker(
        prompt: str,
        duration: int = 3,
        fps: int = 10,
) -> Tuple[str, str]:
    """
    Generate video and return both versions.

    Returns:
        Tuple[str, str]: (original_video_path, transparent_webp_path)
    """

    # Create output directory
    output_dir = os.path.join(os.getcwd(), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    temp_id = uuid.uuid4().hex
    original_video_path = os.path.join(output_dir, f"{temp_id}_original.mp4")
    transparent_webp_path = os.path.join(output_dir, f"{temp_id}_transparent.webp")

    runware = Runware(
        api_key=os.environ.get("RUNWARE_API_KEY"),
        timeout=600
    )
    await runware.connect()

    try:
        # 1️⃣ Generate video (async mode)
        task_uuid = str(uuid.uuid4())

        request = IVideoInference(
            taskUUID=task_uuid,
            positivePrompt=prompt,
            model="bytedance:2@2",
            duration=duration,
            width=640,
            height=640,
            fps=24,
            deliveryMethod="async",
        )

        response = await runware.videoInference(requestVideo=request)
        print(f"Task submitted: {response.taskUUID}")

        # 2️⃣ Poll for results
        video_url = None
        max_attempts = 120

        for attempt in range(max_attempts):
            print(f"Polling for result... (attempt {attempt + 1}/{max_attempts})")

            videos = await runware.getResponse(
                taskUUID=response.taskUUID,
                numberResults=1
            )

            if videos and len(videos) > 0:
                video = videos[0]
                if hasattr(video, 'status'):
                    if video.status == "success":
                        video_url = video.videoURL
                        print(f"Video ready: {video_url}")
                        break
                    elif video.status == "error":
                        raise Exception(f"Video generation failed: {video}")
                    else:
                        print(f"Status: {video.status}")
                elif hasattr(video, 'videoURL'):
                    video_url = video.videoURL
                    print(f"Video ready: {video_url}")
                    break

            await asyncio.sleep(5)

        if not video_url:
            raise Exception("Timeout waiting for video generation")

        # 3️⃣ Download original video
        print("Downloading video...")
        dl_response = requests.get(video_url, timeout=600)
        dl_response.raise_for_status()

        with open(original_video_path, "wb") as f:
            f.write(dl_response.content)

        # 4️⃣ Extract frames
        print("Extracting frames...")
        clip = VideoFileClip(original_video_path)
        frame_images = []

        for frame in clip.iter_frames(fps=fps):
            img = Image.fromarray(frame)
            frame_images.append(img)

        clip.close()
        print(f"Extracted {len(frame_images)} frames")

        # 5️⃣ Remove backgrounds
        print("Removing backgrounds...")
        transparent_frames = []
        for i, img in enumerate(frame_images):
            rgba = remove(img).convert("RGBA")
            transparent_frames.append(rgba)
            if (i + 1) % 5 == 0:
                print(f"Processed {i + 1}/{len(frame_images)} frames")

        # 6️⃣ Create animated WebP
        MAX_FILE_SIZE = 500 * 1024  # 500KB

        # 6️⃣ Create animated WebP
        print("Creating animated WebP...")
        transparent_frames[0].save(
            transparent_webp_path,
            save_all=True,
            append_images=transparent_frames[1:],
            duration=int(1000 / fps),
            loop=0,
            format="WEBP",
            quality=85
        )

        # Check file size & compress if needed
        if os.path.getsize(transparent_webp_path) > MAX_FILE_SIZE:
            print("⚠️ Compressing to meet WhatsApp size limit...")
            transparent_frames[0].save(
                transparent_webp_path,
                save_all=True,
                append_images=transparent_frames[1:],
                duration=int(1000 / fps),
                loop=0,
                format="WEBP",
                quality=60
            )

        print(f"✅ Original: {original_video_path}")
        print(f"✅ Transparent: {transparent_webp_path}")

        return original_video_path, transparent_webp_path

    finally:
        await runware.disconnect()


if __name__ == "__main__":
    # ========== CUSTOMIZE HERE ==========
    prompt = "A cat standing still suddenly becomes frozen, covered in ice, frost spreading over their body"
    duration = 5  # Video duration in seconds (change this!)
    fps = 10      # Frames per second for WebP
    # ====================================

    original, transparent = asyncio.run(
        generate_runware_transparent_sticker(
            prompt=prompt,
            duration=duration,
            fps=fps
        )
    )
    print(f"Original: {original}")
    print(f"Transparent: {transparent}")