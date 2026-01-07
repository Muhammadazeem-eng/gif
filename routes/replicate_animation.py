from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
import os
import uuid

from controllers.replicate_animation import generate_animated_sticker

router = APIRouter(

)


@router.get("/generate-replicate-animation")
def generate_replicate_animation(
    concept: str = Query(..., description="Animation concept"),
    frames: int = Query(
        4,
        ge=2,
        le=6,
        description="Number of frames (2–6)"
    ),
):
    """
    Generate animated WhatsApp sticker using:
    GPT-4o-mini → Replicate → rembg → WebP
    """

    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set"
        )

    if not os.environ.get("REPLICATE_API_TOKEN"):
        raise HTTPException(
            status_code=500,
            detail="REPLICATE_API_TOKEN is not set"
        )

    # Unique output filename per request
    output_file = f"replicate_animation_{uuid.uuid4().hex}.webp"

    try:
        # Controller handles everything
        result_path = generate_animated_sticker(
            concept=concept,
            num_frames=frames,
            cleanup=True
        )

        return FileResponse(
            path=result_path,
            media_type="image/webp",
            filename="whatsapp_sticker.webp"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
