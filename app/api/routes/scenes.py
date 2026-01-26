from typing import List, Optional, Dict
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.models import Scene, UpdateSceneRequest, VideoStatus
from app.storage import store
from app.services.job_processor import job_processor
from app.services.video_service import get_video_service
from app.services.edit_assistant_service import edit_assistant_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scenes", tags=["scenes"])


class RegenerateWithInstructionRequest(BaseModel):
    """Request to regenerate with text instructions"""
    instruction: str  # e.g. "make the character smile" or "add a laptop on the desk"


class AnimateSceneRequest(BaseModel):
    """Request to animate a scene (convert image to video)"""
    custom_prompt: Optional[str] = None  # Optional: override the scene text
    aspect_ratio: str = "16:9"  # "16:9" (landscape) or "9:16" (portrait)


class RefineInstructionRequest(BaseModel):
    """Request to refine a vague edit instruction"""
    instruction: str  # e.g. "make it better" or "different vibe"


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


@router.post("/{scene_id}/animate", response_model=Scene)
async def animate_scene(
    scene_id: str,
    request: AnimateSceneRequest
) -> Scene:
    """
    🎬 Animate a scene - Convert the generated image into a 6-second video using Veo 3.1
    
    This endpoint starts the video generation process. The video generation is asynchronous
    and can take 11 seconds to 6 minutes to complete.
    
    After calling this endpoint, poll GET /scenes/{scene_id}/video-status to check progress.
    
    Requirements:
    - Scene must have a generated image (image_status = "generated")
    
    Returns:
    - Scene with video_status = "pending" and video_operation_name set
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # Check if image exists
    if not scene.image_url:
        raise HTTPException(
            status_code=400,
            detail="Scene has no generated image. Generate an image first before animating."
        )
    
    # Get video service
    video_service = get_video_service()
    if not video_service:
        raise HTTPException(
            status_code=503,
            detail="Video service not available. Check GOOGLE_GEMINI_API_KEY."
        )
    
    try:
        # Start video generation
        operation_name, estimated_cost = video_service.generate_video_from_scene(
            scene=scene,
            custom_prompt=request.custom_prompt,
            aspect_ratio=request.aspect_ratio
        )
        
        # Update scene
        scene.video_status = VideoStatus.PENDING
        scene.video_operation_name = operation_name
        scene.last_error = None
        scene.last_operation_cost = estimated_cost  # Track estimated cost for UI counter
        store.save_scene(scene)
        
        return scene
        
    except Exception as e:
        scene.video_status = VideoStatus.FAILED
        scene.last_error = f"Failed to start video generation: {str(e)}"
        store.save_scene(scene)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scene_id}/video-status", response_model=Scene)
async def check_video_status(scene_id: str) -> Scene:
    """
    📊 Check the status of video generation for a scene
    
    Poll this endpoint after calling POST /scenes/{scene_id}/animate to check if the
    video is ready.
    
    Video Status:
    - "not_requested": No video generation requested yet
    - "pending": Video generation just started (operation submitted)
    - "processing": Video is being generated (checked at least once, still not done)
    - "generated": Video is ready! Check scene.video_url
    - "failed": Video generation failed, check scene.last_error
    
    Polling Strategy:
    - Poll every 5-10 seconds
    - Video generation typically takes 11s - 6min
    - Videos are stored for 2 days after generation
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    # If no video operation, return current state
    if not scene.video_operation_name:
        return scene
    
    # If already done (generated or failed), return current state
    if scene.video_status in [VideoStatus.GENERATED, VideoStatus.FAILED]:
        return scene
    
    # Check status with video service
    video_service = get_video_service()
    if not video_service:
        raise HTTPException(
            status_code=503,
            detail="Video service not available"
        )
    
    try:
        is_done, video_url, error_message = video_service.check_video_status(
            scene.video_operation_name
        )
        
        if not is_done:
            # Still processing
            scene.video_status = VideoStatus.PROCESSING
        elif error_message:
            # Failed
            scene.video_status = VideoStatus.FAILED
            scene.last_error = error_message
        elif video_url:
            # Success!
            scene.video_status = VideoStatus.GENERATED
            scene.video_url = video_url
            scene.last_error = None
            
            logger.info(f"✅ Video generated for scene {scene_id[:8]}, size: {len(video_url)} chars")
            
            # Update job costs with actual video generation cost
            job = store.get_job(scene.job_id)
            if job and scene.last_operation_cost > 0:
                job.cost.video_generation_cost += scene.last_operation_cost
                job.cost.num_videos_generated += 1
                job.cost.total_cost = (
                    job.cost.prompt_generation_cost +
                    job.cost.image_generation_cost +
                    job.cost.video_generation_cost
                )
                store.save_job(job)
                logger.info(f"💰 Job cost updated: ${job.cost.total_cost:.6f}")
        else:
            # Unexpected state
            scene.video_status = VideoStatus.FAILED
            scene.last_error = "Unexpected state - operation done but no video or error"
        
        store.save_scene(scene)
        logger.info(f"Scene saved, returning response...")
        return scene
        
    except Exception as e:
        logger.error(f"❌ Error in check_video_status endpoint: {type(e).__name__}")
        logger.error(f"   Message: {str(e)}")
        import traceback
        logger.error(f"   Traceback:\n{traceback.format_exc()}")
        
        scene.video_status = VideoStatus.FAILED
        scene.last_error = f"Error checking video status: {str(e)}"
        store.save_scene(scene)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scene_id}/edit-suggestions", response_model=Dict)
async def get_edit_suggestions(scene_id: str) -> Dict:
    """
    🎨 Get edit suggestions for a scene
    
    Analyzes the current scene and returns:
    - What can be edited (character, setting, props, camera)
    - Specific suggestions for each category
    - Example instructions for common edits
    
    Perfect for showing users what they can change in the UI!
    
    Example response:
    ```json
    {
      "current_state": {
        "character": { "pose": "sitting", "expression": "neutral" },
        "setting": { "location": "office", "lighting": "natural" },
        "camera": { "shot": "medium_shot", "angle": "eye_level" }
      },
      "edit_categories": [
        {
          "category": "Character Pose & Expression",
          "suggestions": [
            {
              "category": "pose",
              "description": "Change what the character is doing",
              "example_instruction": "make the character standing up and stretching"
            }
          ]
        }
      ]
    }
    ```
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    if not edit_assistant_service:
        raise HTTPException(
            status_code=503,
            detail="Edit assistant service not available"
        )
    
    try:
        analysis = edit_assistant_service.analyze_scene_for_edits(scene)
        return analysis
    except Exception as e:
        logger.error(f"❌ Error analyzing scene for edits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{scene_id}/refine-instruction", response_model=Dict)
async def refine_edit_instruction(
    scene_id: str,
    request: RefineInstructionRequest
) -> Dict:
    """
    ✨ Refine a vague edit instruction into something specific and actionable
    
    Takes user input like "make it happier" and transforms it into:
    "Change character expression to bright smile with relaxed posture, add warm golden hour lighting"
    
    Usage:
    1. User types vague instruction: "make it better"
    2. Call this endpoint to get refined version
    3. Show refined version to user (optional)
    4. Use refined version for actual edit
    
    Example:
    ```
    POST /scenes/{id}/refine-instruction
    {
      "instruction": "make it more energetic"
    }
    
    Response:
    {
      "original": "make it more energetic",
      "refined": "change character to dynamic jumping pose with excited expression, add bright vibrant lighting, create lively bustling atmosphere with movement",
      "cost": 0.000123
    }
    ```
    """
    scene = store.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    
    if not edit_assistant_service:
        raise HTTPException(
            status_code=503,
            detail="Edit assistant service not available"
        )
    
    try:
        refined, cost, tokens = edit_assistant_service.refine_edit_instruction(
            scene,
            request.instruction
        )
        
        return {
            "original": request.instruction,
            "refined": refined,
            "cost": cost,
            "tokens_used": tokens
        }
    except Exception as e:
        logger.error(f"❌ Error refining instruction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
