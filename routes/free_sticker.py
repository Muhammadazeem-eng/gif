from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
import os
import uuid

from controllers.free_sticker import (
    generate_sticker_free,
    create_animated_webp
)

router = APIRouter()


@router.get("/generate-free-sticker")
def generate_sticker(
    prompt: str = Query(..., description="Prompt for sticker generation"),
    animation: str = Query(
        "float",
        description="Animation type: float, bounce, pulse, wiggle, static"
    ),
):
    """
    Generate a FREE WhatsApp-compatible animated sticker (WebP)
    and return it as a downloadable file.
    """

    try:
        # Unique filename per request
        output_file = f"sticker_{uuid.uuid4().hex}.webp"

        # Generate sticker image
        image = generate_sticker_free(prompt)

        # Create animated WebP
        create_animated_webp(image, animation, output_file)

        return FileResponse(
            path=output_file,
            media_type="image/webp",
            filename="whatsapp_sticker.webp"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Optional cleanup (delete after response is sent)
        if os.path.exists(output_file):
            pass  # keep file if you want caching
