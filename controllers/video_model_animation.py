# """
# Controller for Runware Video Generation
# Returns both original MP4 and transparent WebP
# """
#
# import os
# import uuid
# import asyncio
# import requests
# from typing import Optional, Tuple
#
# from runware import Runware, IVideoInference
# from moviepy import VideoFileClip
# from PIL import Image
# from rembg import remove
# from dotenv import load_dotenv
#
# load_dotenv()
#
#
# async def generate_runware_transparent_sticker(
#         prompt: str,
#         duration: int = 3,
#         fps: int = 10,
# ) -> Tuple[str, str]:
#     """
#     Generate video and return both versions.
#
#     Returns:
#         Tuple[str, str]: (original_video_path, transparent_webp_path)
#     """
#
#     # Create output directory
#     output_dir = os.path.join(os.getcwd(), "outputs")
#     os.makedirs(output_dir, exist_ok=True)
#
#     temp_id = uuid.uuid4().hex
#     original_video_path = os.path.join(output_dir, f"{temp_id}_original.mp4")
#     transparent_webp_path = os.path.join(output_dir, f"{temp_id}_transparent.webp")
#
#     runware = Runware(
#         api_key=os.environ.get("RUNWARE_API_KEY"),
#         timeout=600
#     )
#     await runware.connect()
#
#     try:
#         # 1️⃣ Generate video (async mode)
#         task_uuid = str(uuid.uuid4())
#
#         request = IVideoInference(
#             taskUUID=task_uuid,
#             positivePrompt=prompt,
#             model="bytedance:2@2",
#             duration=duration,
#             width=640,
#             height=640,
#             fps=24,
#             deliveryMethod="async",
#         )
#
#         response = await runware.videoInference(requestVideo=request)
#         print(f"Task submitted: {response.taskUUID}")
#
#         # 2️⃣ Poll for results
#         video_url = None
#         max_attempts = 120
#
#         for attempt in range(max_attempts):
#             print(f"Polling for result... (attempt {attempt + 1}/{max_attempts})")
#
#             videos = await runware.getResponse(
#                 taskUUID=response.taskUUID,
#                 numberResults=1
#             )
#
#             if videos and len(videos) > 0:
#                 video = videos[0]
#                 if hasattr(video, 'status'):
#                     if video.status == "success":
#                         video_url = video.videoURL
#                         print(f"Video ready: {video_url}")
#                         break
#                     elif video.status == "error":
#                         raise Exception(f"Video generation failed: {video}")
#                     else:
#                         print(f"Status: {video.status}")
#                 elif hasattr(video, 'videoURL'):
#                     video_url = video.videoURL
#                     print(f"Video ready: {video_url}")
#                     break
#
#             await asyncio.sleep(5)
#
#         if not video_url:
#             raise Exception("Timeout waiting for video generation")
#
#         # 3️⃣ Download original video
#         print("Downloading video...")
#         dl_response = requests.get(video_url, timeout=600)
#         dl_response.raise_for_status()
#
#         with open(original_video_path, "wb") as f:
#             f.write(dl_response.content)
#
#         # 4️⃣ Extract frames
#         print("Extracting frames...")
#         clip = VideoFileClip(original_video_path)
#         frame_images = []
#
#         for frame in clip.iter_frames(fps=fps):
#             img = Image.fromarray(frame)
#             frame_images.append(img)
#
#         clip.close()
#         print(f"Extracted {len(frame_images)} frames")
#
#         # 5️⃣ Remove backgrounds
#         print("Removing backgrounds...")
#         transparent_frames = []
#         for i, img in enumerate(frame_images):
#             rgba = remove(img).convert("RGBA")
#             transparent_frames.append(rgba)
#             if (i + 1) % 5 == 0:
#                 print(f"Processed {i + 1}/{len(frame_images)} frames")
#
#         # 6️⃣ Create animated WebP
#         MAX_FILE_SIZE = 500 * 1024  # 500KB
#
#         # 6️⃣ Create animated WebP
#         print("Creating animated WebP...")
#         transparent_frames[0].save(
#             transparent_webp_path,
#             save_all=True,
#             append_images=transparent_frames[1:],
#             duration=int(1000 / fps),
#             loop=0,
#             format="WEBP",
#             quality=85
#         )
#
#         # Check file size & compress if needed
#         if os.path.getsize(transparent_webp_path) > MAX_FILE_SIZE:
#             print("⚠️ Compressing to meet WhatsApp size limit...")
#             transparent_frames[0].save(
#                 transparent_webp_path,
#                 save_all=True,
#                 append_images=transparent_frames[1:],
#                 duration=int(1000 / fps),
#                 loop=0,
#                 format="WEBP",
#                 quality=60
#             )
#
#         print(f"✅ Original: {original_video_path}")
#         print(f"✅ Transparent: {transparent_webp_path}")
#
#         return original_video_path, transparent_webp_path
#
#     finally:
#         await runware.disconnect()
#
#
# if __name__ == "__main__":
#     # ========== CUSTOMIZE HERE ==========
#     prompt = "A cat standing still suddenly becomes frozen, covered in ice, frost spreading over their body"
#     duration = 5  # Video duration in seconds (change this!)
#     fps = 10      # Frames per second for WebP
#     # ====================================
#
#     original, transparent = asyncio.run(
#         generate_runware_transparent_sticker(
#             prompt=prompt,
#             duration=duration,
#             fps=fps
#         )
#     )
#     print(f"Original: {original}")
#     print(f"Transparent: {transparent}")




########################################################################################

"""
Controller for Runware Video Generation
Returns both original MP4 and transparent WebP (under 500KB for WhatsApp)
FAST version - no trial/error compression loops
"""

import os
import uuid
import asyncio
import requests
from typing import Tuple

from runware import Runware, IVideoInference
from moviepy import VideoFileClip
from PIL import Image
from rembg import remove
from dotenv import load_dotenv

load_dotenv()



VIDEO_ASPECT_RATIOS = {
    # ---------- 480p-ish ----------
    "16:9_480p": (864, 480),
    "4:3_480p": (736, 544),
    "1:1_480p": (640, 640),
    "3:4_480p": (544, 736),
    "9:16_480p": (480, 864),
    "21:9_480p": (960, 416),

    # ---------- 720p-ish ----------
    "16:9_720p": (1248, 704),
    "4:3_720p": (1120, 832),
    "1:1_720p": (960, 960),
    "3:4_720p": (832, 1120),
    "9:16_720p": (704, 1248),
    "21:9_720p": (1504, 640),

}



MAX_FILE_SIZE = 500 * 1024  # 500KB


def prepare_frames_for_whatsapp(
        frames: list,
        fps: int,
        target_size: int = MAX_FILE_SIZE
) -> Tuple[list, int]:
    """
    Prepare frames to fit WhatsApp limits.
    Calculates optimal settings upfront - NO trial/error loops.

    Returns: (processed_frames, adjusted_fps)
    """
    num_frames = len(frames)
    frame_w, frame_h = frames[0].size

    # Estimate: ~3-5KB per 512x512 frame at quality 50
    # More frames or bigger size = need more aggressive settings
    estimated_size = num_frames * (frame_w / 512) * (frame_h / 512) * 4000

    print(f"  Input: {num_frames} frames @ {frame_w}x{frame_h}")
    print(f"  Estimated raw size: ~{estimated_size / 1024:.0f}KB")

    # Determine compression level needed
    ratio = estimated_size / target_size

    if ratio <= 1:
        # Already good
        print(f"  → No compression needed")
        return frames, fps

    elif ratio <= 2:
        # Light compression - just resize to 384x384
        new_size = (384, 384)
        print(f"  → Light compression: resize to {new_size}")
        return [f.resize(new_size, Image.LANCZOS) for f in frames], fps

    elif ratio <= 4:
        # Medium - resize to 320x320
        new_size = (320, 320)
        print(f"  → Medium compression: resize to {new_size}")
        return [f.resize(new_size, Image.LANCZOS) for f in frames], fps

    elif ratio <= 8:
        # Heavy - resize + skip frames
        new_size = (256, 256)
        skip = 2
        reduced = frames[::skip]
        new_fps = max(fps // skip, 5)
        print(f"  → Heavy compression: {new_size}, skip every {skip}nd frame ({len(reduced)} frames)")
        return [f.resize(new_size, Image.LANCZOS) for f in reduced], new_fps

    else:
        # Extreme - small size + aggressive frame skip
        new_size = (256, 256)
        skip = max(3, int(ratio / 4))
        reduced = frames[::skip]
        new_fps = max(fps // skip, 4)
        print(f"  → Extreme compression: {new_size}, keep every {skip}th frame ({len(reduced)} frames)")
        return [f.resize(new_size, Image.LANCZOS) for f in reduced], new_fps


async def generate_runware_transparent_sticker(
        prompt: str,
        duration: int = 3,
        fps: int = 10,
) -> Tuple[str, str]:
    """
    Generate video and return both versions.
    """

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
        # 1️⃣ Generate video
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
            print(f"Polling... ({attempt + 1}/{max_attempts})")

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
                        raise Exception(f"Generation failed: {video}")
                elif hasattr(video, 'videoURL'):
                    video_url = video.videoURL
                    break

            await asyncio.sleep(5)

        if not video_url:
            raise Exception("Timeout waiting for video")

        # 3️⃣ Download
        print("Downloading...")
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
        print(f"Got {len(frame_images)} frames")

        # 5️⃣ Remove backgrounds (this is the slow part - can't speed up much)
        print("Removing backgrounds...")
        transparent_frames = []
        for i, img in enumerate(frame_images):
            rgba = remove(img).convert("RGBA")
            transparent_frames.append(rgba)
            if (i + 1) % 10 == 0:
                print(f"  {i + 1}/{len(frame_images)}")

        # 6️⃣ Prepare for WhatsApp (fast - just calculates once)
        print("Preparing for WhatsApp...")
        final_frames, final_fps = prepare_frames_for_whatsapp(
            transparent_frames, fps, MAX_FILE_SIZE
        )

        # 7️⃣ Save WebP (single save, no loops)
        print("Saving WebP...")
        final_frames[0].save(
            transparent_webp_path,
            save_all=True,
            append_images=final_frames[1:],
            duration=int(1000 / final_fps),
            loop=0,
            format="WEBP",
            quality=50,
            method=4  # Balanced speed/compression
        )

        final_size = os.path.getsize(transparent_webp_path)
        print(f"✅ Original: {original_video_path}")
        print(f"✅ Sticker: {transparent_webp_path} ({final_size / 1024:.1f}KB)")

        if final_size > MAX_FILE_SIZE:
            print(f"⚠️ Still {final_size / 1024:.1f}KB - may need manual adjustment")

        return original_video_path, transparent_webp_path

    finally:
        await runware.disconnect()

async def generate_runware_video_only(
    prompt: str,
    duration: int,
    aspect_ratio: str,
    fps: int = 24,
) -> str:
    print("▶️ generate_runware_video_only() started")

    if aspect_ratio not in VIDEO_ASPECT_RATIOS:
        raise ValueError(f"Invalid aspect_ratio: {aspect_ratio}")

    width, height = VIDEO_ASPECT_RATIOS[aspect_ratio]

    output_dir = os.path.join(os.getcwd(), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    temp_id = uuid.uuid4().hex
    output_path = os.path.join(output_dir, f"{temp_id}_video.mp4")
    print(f"📁 Output path: {output_path}")

    runware = Runware(
        api_key=os.environ.get("RUNWARE_API_KEY"),
        timeout=600
    )
    await runware.connect()

    try:
        task_uuid = str(uuid.uuid4())

        request = IVideoInference(
            taskUUID=task_uuid,
            positivePrompt=prompt,
            model="bytedance:1@1",
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            outputFormat="mp4",
            outputQuality=85,
            deliveryMethod="async",
        )
        print(f"🚀 Submitting video inference task: {task_uuid}")

        response = await runware.videoInference(requestVideo=request)

        video_url = None
        for _ in range(120):
            print("⏳ Checking task status...")

            results = await runware.getResponse(
                taskUUID=response.taskUUID,
                numberResults=1
            )

            if results and results[0].status == "success":
                video_url = results[0].videoURL
                break

            await asyncio.sleep(5)

        if not video_url:
            raise Exception("Video generation timeout")

        dl = requests.get(video_url, timeout=600)
        dl.raise_for_status()

        with open(output_path, "wb") as f:
            f.write(dl.content)

        return output_path

    finally:
        await runware.disconnect()

# if __name__ == "__main__":
#     prompt = "A cat standing still suddenly becomes frozen, covered in ice, frost spreading over their body"
#     duration = 5
#     fps = 10
#
#     original, transparent = asyncio.run(
#         generate_runware_transparent_sticker(
#             prompt=prompt,
#             duration=duration,
#             fps=fps
#         )
#     )