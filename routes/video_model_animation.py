"""
Routes for Video Sticker Generation

API 1: POST /generate-sticker
    - Generate video ONCE
    - Save both files
    - Return original MP4 + task_id

API 2: GET /get-transparent/{task_id}
    - Return transparent WebP
    - Auto-delete both files after
"""

import os
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from controllers.video_model_animation import generate_runware_transparent_sticker

router = APIRouter()

# Store task paths (use Redis/DB in production)
task_storage = {}


class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for video generation")
    duration: int = Field(default=3, ge=1, le=10, description="Video duration in seconds (1-10)")


def cleanup_files(task_id: str):
    """Background task to cleanup files after response is sent."""
    import time
    time.sleep(5)  # Wait 5 seconds to ensure file is sent

    if task_id in task_storage:
        paths = task_storage[task_id]
        for path in paths.values():
            if os.path.exists(path):
                os.remove(path)
        del task_storage[task_id]
        print(f"Cleaned up task: {task_id}")


# ============================================================
# API 1: Generate and return original video + task_id
# ============================================================

@router.post("/generate-video-original-by-video-model")
async def generate_sticker(request: VideoGenerationRequest):
    """
    Generate video, save both files, return original MP4 + task_id.
    Use task_id to get transparent version later.
    """
    try:
        original_video_path, transparent_video_path = await generate_runware_transparent_sticker(
            prompt=request.prompt,
            duration=request.duration
        )

        # Extract task_id from filename
        filename = os.path.basename(original_video_path)
        task_id = filename.replace("_original.mp4", "")

        # Store paths
        task_storage[task_id] = {
            "transparent_path": transparent_video_path,
            "original_path": original_video_path
        }

        response = FileResponse(
            original_video_path,
            media_type="video/mp4",
            filename="sticker_original.mp4"
        )
        response.headers["X-Task-ID"] = task_id

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# API 2: Get transparent video + AUTO CLEANUP
# ============================================================

@router.get("/get-transparent-video-by-video-model/{task_id}")
async def get_transparent(task_id: str, background_tasks: BackgroundTasks):
    """
    Get transparent WebP using task_id.
    Files are automatically deleted after download.
    """
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found. Generate first.")

    transparent_path = task_storage[task_id]["transparent_path"]

    if not os.path.exists(transparent_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Auto cleanup after file is sent
    # background_tasks.add_task(cleanup_files, task_id)

    return FileResponse(
        transparent_path,
        media_type="image/webp",
        filename="sticker_transparent.webp"
    )