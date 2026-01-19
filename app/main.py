import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import jobs, scenes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# Set specific loggers
logging.getLogger('app.api').setLevel(logging.INFO)
logging.getLogger('app.services').setLevel(logging.INFO)

app = FastAPI(
    title="YT Visual Generator API",
    description="Convert YouTube scripts into visual storyboards",
    version="0.1.0"
)

# CORS middleware (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router)
app.include_router(scenes.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "YT Visual Generator API",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/test-image")
async def test_image():
    """
    Test endpoint that returns a simple data URI image
    Use this to verify your frontend can display data URI images
    """
    # 1x1 red pixel PNG
    test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    return {
        "test_image_url": f"data:image/png;base64,{test_image_base64}",
        "instructions": "Use this image_url in an <img> tag. If this works, your scenes should work too!",
        "example": '<img src="data:image/png;base64,..." alt="test" />'
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
