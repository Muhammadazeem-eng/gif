from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import uuid
import os
import shutil

from controllers.gemini_sticker import (
    generate_sticker,
    create_animated_webp
)

router = APIRouter()

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/generate")
def generate_gemini_sticker(
    prompt: str = Form(..., description="Sticker prompt"),
    animation: str = Form(
        "float",
        description="float | bounce | pulse | wiggle | static"
    ),
    reference_image: UploadFile | None = File(
        None,
        description="Optional reference image"
    ),
):
    """
    Generate WhatsApp-compatible animated WebP sticker using Gemini.
    Reference image is optional.
    """

    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set"
        )

    output_file = f"gemini_sticker_{uuid.uuid4().hex}.webp"
    reference_path = None

    try:
        # Save reference image if provided
        if reference_image:
            reference_path = os.path.join(
                TEMP_DIR,
                f"{uuid.uuid4().hex}_{reference_image.filename}"
            )
            with open(reference_path, "wb") as buffer:
                shutil.copyfileobj(reference_image.file, buffer)

        # Generate sticker image (PIL Image)
        sticker_image = generate_sticker(
            prompt=prompt,
            reference_image_path=reference_path
        )

        # Create animated WebP
        create_animated_webp(
            image=sticker_image,
            animation=animation,
            output_path=output_file
        )

        return FileResponse(
            path=output_file,
            media_type="image/webp",
            filename="whatsapp_sticker.webp"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup temp reference image
        if reference_path and os.path.exists(reference_path):
            os.remove(reference_path)
