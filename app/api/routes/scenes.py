from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.models import Scene, UpdateSceneRequest
from app.storage import store
from app.services.job_processor import job_processor

router = APIRouter(prefix="/scenes", tags=["scenes"])


class RegenerateWithInstructionRequest(BaseModel):
    """Request to regenerate with text instructions"""
    instruction: str  # e.g. "make the character smile" or "add a laptop on the desk"


@router.get("/job/{job_id}", response_model=List[Scene])
async def get_job_scenes(job_id: str) -> List[Scene]:
    """
    Get all scenes for a job, ordered by index.
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    scenes = store.get_scenes_by_job(job_id)
    # Sort by index
    scenes.sort(key=lambda s: s.index)
    return scenes


@router.get("/{scene_id}", response_model=Scene)
async def get_scene(scene_id: str) -> Scene:
    """
    Get a specific scene by ID.
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.patch("/{scene_id}", response_model=Scene)
async def update_scene(scene_id: str, request: UpdateSceneRequest) -> Scene:
    """
    Update a scene's visual prompt.
    
    This allows manual editing of the generated prompt.
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Update visual prompt
    scene.visual_prompt = request.visual_prompt
    store.save_scene(scene)
    
    return scene


@router.post("/{scene_id}/regenerate-image", response_model=Scene)
async def regenerate_scene_image(
    scene_id: str,
    background_tasks: BackgroundTasks
) -> Scene:
    """
    Regenerate the image for a specific scene using its current visual prompt.
    
    This is useful after editing a scene's visual prompt.
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    if not scene.visual_prompt:
        raise HTTPException(
            status_code=400,
            detail="Scene has no visual prompt to generate image from"
        )
    
    # Regenerate in background
    background_tasks.add_task(job_processor.regenerate_scene_image, scene_id)
    
    return scene


@router.post("/{scene_id}/regenerate-with-instruction", response_model=Scene)
async def regenerate_with_instruction(
    scene_id: str,
    request: RegenerateWithInstructionRequest,
    background_tasks: BackgroundTasks
) -> Scene:
    """
    Regenerate the image with text instructions (e.g. "make character smile", "add laptop").
    
    This is the EASY way to edit scenes - just provide text instructions!
    The system will:
    1. Take your instruction
    2. Update the visual prompt accordingly
    3. Generate a new image
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    if not scene.visual_prompt:
        raise HTTPException(
            status_code=400,
            detail="Scene has no visual prompt to modify"
        )
    
    # Regenerate with instructions in background
    background_tasks.add_task(
        job_processor.regenerate_scene_with_instruction,
        scene_id,
        request.instruction
    )
    
    return scene
