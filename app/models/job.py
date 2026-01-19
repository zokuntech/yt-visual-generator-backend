from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class JobStatus(str, Enum):
    """Status of a storyboard generation job"""
    PENDING = "pending"
    GENERATING_PROMPTS = "generating_prompts"
    GENERATING_IMAGES = "generating_images"
    COMPLETED = "completed"
    FAILED = "failed"


class StyleConfig(BaseModel):
    """Detailed style configuration for visual generation"""
    art_style: str = "professional_youtube_style"
    lighting: str = "natural_lighting"
    color_palette: str = "warm_neutral"
    background: str = "clean_simple"
    character_description: str = "content creator, approachable, professional casual"
    camera_angle: str = "medium_shot"
    framing: str = "centered"


class JobOptions(BaseModel):
    """Options for job processing"""
    generate_images: bool = True
    style_config: Optional[StyleConfig] = Field(default_factory=StyleConfig)


class CostBreakdown(BaseModel):
    """Cost tracking for API usage"""
    prompt_generation_cost: float = 0.0  # OpenAI cost
    image_generation_cost: float = 0.0   # Gemini cost
    total_cost: float = 0.0
    prompt_tokens_used: int = 0
    image_tokens_used: int = 0
    num_prompts_generated: int = 0
    num_images_generated: int = 0


class Job(BaseModel):
    """Represents one storyboard generation request"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None
    script_text: str
    options: JobOptions = Field(default_factory=JobOptions)
    scene_ids: list[str] = Field(default_factory=list)
    cost: CostBreakdown = Field(default_factory=CostBreakdown)


class CreateJobRequest(BaseModel):
    """Request to create a new storyboard job"""
    script_text: str
    generate_images: bool = True
    style_config: Optional[StyleConfig] = None  # If not provided, uses defaults
