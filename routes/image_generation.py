

# from fastapi import APIRouter, HTTPException
# from fastapi.responses import FileResponse
# from pydantic import BaseModel
# from controllers.image_generation import generate_image
#
# router = APIRouter(prefix="/image", tags=["Image Generation"])
#
#
# class ImageRequest(BaseModel):
#     prompt: str
#     width: int
#     height: int
#
#
# @router.post("/generate-image")
# def generate_image_route(payload: ImageRequest):
#     try:
#         file_path = generate_image(
#             prompt=payload.prompt,
#             width=payload.width,
#             height=payload.height,
#         )
#
#         return FileResponse(file_path, media_type="image/jpeg", filename="generated_image.jpg")
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


############################

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from controllers.image_generation import generate_image

router = APIRouter(prefix="/image", tags=["Image Generation"])


class ImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str


@router.post("/generate-image")
def generate_image_route(payload: ImageRequest):
    try:
        file_path = generate_image(
            prompt=payload.prompt,
            aspect_ratio=payload.aspect_ratio,
        )

        return FileResponse(
            file_path,
            media_type="image/jpeg",
            filename="generated_image.jpg",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
