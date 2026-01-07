from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
import uuid
import os

from controllers.replicate_sticker import (
    generate_sticker,
    create_animated_webp
)

router = APIRouter()



# Fixed animation settings
FRAMES = 20
FPS = 15


@router.get("/generate-replicate-sticker")
def generate_replicate_sticker(
    prompt: str = Query(..., description="Sticker prompt"),
    animation: str = Query(
        "bounce",
        description="bounce | shake | pulse | wiggle | static"
    ),
):
    """
    Generate WhatsApp-compatible animated WebP sticker using Replicate.
    Frames and FPS are fixed for WhatsApp compatibility.
    """

    if not os.environ.get("REPLICATE_API_TOKEN"):
        raise HTTPException(
            status_code=500,
            detail="REPLICATE_API_TOKEN is not set"
        )

    output_file = f"replicate_sticker_{uuid.uuid4().hex}.webp"

    try:
        # Generate base image
        image_path = generate_sticker(prompt)

        # Create animated WebP (fixed frames & fps)
        create_animated_webp(
            image_path=image_path,
            output_path=output_file,
            animation=animation,
            frames=FRAMES,
            fps=FPS
        )

        return FileResponse(
            path=output_file,
            media_type="image/webp",
            filename="whatsapp_sticker.webp"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temp image
        if os.path.exists("temp_sticker.png"):
            os.remove("temp_sticker.png")