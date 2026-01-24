from typing import List
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models import Job, JobOptions, CreateJobRequest, StyleConfig, CostBreakdown
from app.storage import store
from app.services.job_processor import job_processor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=Job, status_code=201)
async def create_job(
    request: CreateJobRequest,
    background_tasks: BackgroundTasks
) -> Job:
    """
    Create a new storyboard generation job.
    
    Provide:
    - `script_text`: Your script text (required)
    - `generate_images`: Whether to generate images (default: true)
    - `style_config`: Custom style configuration (optional)
    
    The job will be processed in the background.
    """
    # Create job with custom style or defaults
    style_config = request.style_config if request.style_config else StyleConfig()
    
    job = Job(
        script_text=request.script_text,
        options=JobOptions(
            generate_images=request.generate_images,
            style_config=style_config
        )
    )
    
    # Save job
    store.save_job(job)
    
    logger.info(f"✅ Job created: {job.id}")
    logger.info(f"   Script length: {len(request.script_text)} characters")
    logger.info(f"   Generate images: {request.generate_images}")
    logger.info(f"   Style: {style_config.art_style}")
    logger.info(f"   Character: {style_config.character_description}")
    
    # Process in background
    background_tasks.add_task(job_processor.process_job, job)
    
    return job


@router.get("/{job_id}", response_model=Job)
async def get_job(job_id: str) -> Job:
    """
    Get job status and details.
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("", response_model=List[Job])
async def list_jobs() -> List[Job]:
    """
    List all jobs.
    """
    return store.list_jobs()


@router.get("/{job_id}/cost", response_model=CostBreakdown)
async def get_job_cost(job_id: str) -> CostBreakdown:
    """
    Get the current cost breakdown for a job.
    
    This endpoint is perfect for the UI to poll and update a live cost counter.
    Returns real-time cost information including:
    - Total cost
    - Breakdown by prompt generation, image generation, and video generation
    - Number of items generated
    - Token usage
    
    Example UI implementation:
    ```javascript
    // Poll every 2-3 seconds while job is processing
    const response = await fetch(`/jobs/${jobId}/cost`);
    const cost = await response.json();
    displayCostCounter(cost.total_cost); // Show: "$0.0234"
    ```
    """
    job = store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.cost
