"""
API routes for YouTube Shorts (timelapse/transformation content)
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
import logging

from app.models.short import (
    ShortProject,
    ShortCategory,
    TransformationConcept,
    CreateShortRequest,
    ConceptGenerationRequest,
    ConceptSelectionRequest,
    AnimateShortRequest
)
from app.services.short_processor import ShortProcessor
from app.storage import store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shorts", tags=["shorts"])

# Initialize processor
short_processor = ShortProcessor()


@router.post("/concepts", response_model=dict)
async def generate_concepts(request: ConceptGenerationRequest):
    """
    STEP 1: Generate transformation concept ideas
    
    Returns 10 concepts for the user to choose from.
    """
    try:
        logger.info(f"📋 Generating concepts for {request.category}")
        
        concepts, cost = await short_processor.generate_concepts(
            category=request.category,
            num_concepts=request.num_concepts
        )
        
        return {
            "concepts": [c.dict() for c in concepts],
            "cost": cost,
            "message": "Please select one concept (index 0-9) to develop."
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating concepts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=ShortProject)
async def create_short(
    request: CreateShortRequest,
    background_tasks: BackgroundTasks
):
    """
    STEP 2: Create a short project from a selected concept
    
    This generates the stage and transition prompts.
    Images will be generated in the background.
    """
    try:
        logger.info(f"🎬 Creating short for {request.category}")
        
        # If concept_index is provided, we need to regenerate concepts first
        if request.concept_index is not None:
            logger.info(f"   Regenerating concepts to get selected concept...")
            concepts, _ = await short_processor.generate_concepts(
                category=request.category,
                num_concepts=10
            )
            
            if request.concept_index < 0 or request.concept_index >= len(concepts):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid concept index. Must be 0-{len(concepts)-1}"
                )
            
            selected_concept = concepts[request.concept_index]
        elif request.custom_description:
            # Create a custom concept
            selected_concept = TransformationConcept(
                index=0,
                title=f"Custom {request.category.value}",
                description=request.custom_description,
                category=request.category
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either concept_index or custom_description must be provided"
            )
        
        # Create the project
        project = await short_processor.create_short_project(
            category=request.category,
            concept=selected_concept,
            aspect_ratio=request.aspect_ratio
        )
        
        # Generate images in the background
        background_tasks.add_task(
            short_processor.generate_stage_images,
            project.id
        )
        
        return project
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating short: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ShortProject)
async def get_short(project_id: str):
    """
    Get a short project by ID (poll for status)
    """
    project = store.get_short(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Short project not found")
    
    return project


@router.get("/", response_model=List[ShortProject])
async def list_shorts():
    """
    List all short projects
    """
    return store.list_shorts()


# Video generation endpoints removed - transition prompts are generated with the project
# and available in project.transitions[].motion_description


@router.post("/{project_id}/stage/{stage_number}/regenerate", response_model=ShortProject)
async def regenerate_stage(project_id: str, stage_number: int):
    """
    Regenerate a specific stage image with the same prompt
    
    stage_number: 1, 2, 3, 4, 5, or 6
    """
    try:
        if stage_number < 1 or stage_number > 6:
            raise HTTPException(
                status_code=400,
                detail="stage_number must be between 1 and 6"
            )
        
        project = await short_processor.regenerate_stage_image(
            project_id,
            stage_number
        )
        
        return project
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error regenerating stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project_id}/stage/{stage_number}/edit", response_model=ShortProject)
async def edit_stage(
    project_id: str,
    stage_number: int,
    request: dict
):
    """
    Edit a stage image using a text instruction
    
    stage_number: 1, 2, 3, 4, 5, or 6
    
    Request body:
    {
      "instruction": "make the floor more blue / add more workers / brighter lighting / etc."
    }
    """
    try:
        if stage_number < 1 or stage_number > 6:
            raise HTTPException(
                status_code=400,
                detail="stage_number must be between 1 and 6"
            )
        
        instruction = request.get("instruction")
        if not instruction:
            raise HTTPException(
                status_code=400,
                detail="instruction is required"
            )
        
        project = await short_processor.edit_stage_with_instruction(
            project_id,
            stage_number,
            instruction
        )
        
        return project
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error editing stage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}")
async def delete_short(project_id: str):
    """
    Delete a short project
    """
    success = store.delete_short(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Short project not found")
    
    return {"message": "Short project deleted successfully"}
