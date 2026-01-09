from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import uvicorn
from routes.image_generation import router as image_generation_router
from routes.free_sticker import router as sticker_router
from routes.replicate_sticker import router as replicate_router
from routes.gemini_sticker import router as gemini_router
from routes.free_animation import router as free_animation_router
from routes.replicate_animation import router as replicate_animation_router
from routes.gemini_animation import router as gemini_animation_router
from routes.video_model_animation import router as video_model_animation_router

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["x-task-id"],
)

app.include_router(image_generation_router)
app.include_router(sticker_router)
app.include_router(replicate_router)
app.include_router(gemini_router)
app.include_router(free_animation_router)
app.include_router(replicate_animation_router)
app.include_router(gemini_animation_router)

app.include_router(video_model_animation_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)