from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
import shutil

from controllers.gemini_animation import generate_animated_sticker

router = APIRouter()

TEMP_DIR = "temp_refs"
os.makedirs(TEMP_DIR, exist_ok=True)


@router.post("/generate-gemni-animation")
def generate_gemini_animation(
    concept: str = Form(..., description="Animation concept"),
    frames: int = Form(
        3,
        ge=2,
        le=4,
        description="Number of frames (2–4)"
    ),
    reference_image: UploadFile | None = File(
        None,
        description="Optional reference image"
    ),
):
    """
    Generate animated WhatsApp sticker using:
    GPT-4o-mini → Gemini → rembg → WebP
    """

    if not os.environ.get("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not set"
        )

    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY is not set"
        )

    output_file = f"gemini_animation_{uuid.uuid4().hex}.webp"
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

        result_path = generate_animated_sticker(
            concept=concept,
            reference_image=reference_path,
            num_frames=frames,
            fps=3,
            output_file=output_file,
            save_raw_frames=False
        )

        return FileResponse(
            path=result_path,
            media_type="image/webp",
            filename="whatsapp_sticker.webp"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Cleanup reference image
        if reference_path and os.path.exists(reference_path):
            os.remove(reference_path)
