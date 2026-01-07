from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
import os
import uuid

from controllers.free_animation import generate_animated_sticker

router = APIRouter()

# Fixed WhatsApp-safe FPS
FPS = 4


@router.get("/generate-free-animation")
def generate_free_animation(
    concept: str = Query(..., description="Animation concept"),
    frames: int = Query(
        4,                 # default
        ge=2,              # minimum
        le=6,              # maximum
        description="Number of frames (2–6)"
    ),
):
    """
    Generate a FREE animated WhatsApp sticker.
    """

    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set"
        )

    output_file = f"free_animation_{uuid.uuid4().hex}.webp"

    try:
        generate_animated_sticker(
            concept=concept,
            num_frames=frames,
            fps=FPS,
            output_file=output_file,
            save_raw_frames=False
        )

        return FileResponse(
            path=output_file,
            media_type="image/webp",
            filename="whatsapp_sticker.webp"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))