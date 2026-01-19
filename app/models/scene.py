from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ImageStatus(str, Enum):
    """Status of image generation for a scene"""
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"


class StyleConfig(BaseModel):
    """Visual style configuration"""
    art_style: str = "bratz_doll_style"
    lighting: str = "soft_even_studio_lighting"
    color_palette: str = "warm_neutral_with_contrast"
    background: str = "contextually_relevant_environment"


class Character(BaseModel):
    """Character description in a scene"""
    role: str = "main_subject"
    description: str
    expression: str = "confident_calm"
    pose: str = "3_4_view"


class Composition(BaseModel):
    """Scene composition details"""
    camera_angle: str = "medium_shot"
    framing: str = "centered"
    extras: str = "no_text_no_logos_no_watermarks"


class VisualPrompt(BaseModel):
    """Structured visual prompt for image generation"""
    scene_id: str
    sentence_text: str
    style: StyleConfig
    characters: list[Character] = Field(default_factory=list)
    composition: Composition


class Scene(BaseModel):
    """Represents one sentence/scene in the storyboard"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    index: int
    sentence_text: str
    visual_prompt: Optional[VisualPrompt] = None
    image_status: ImageStatus = ImageStatus.NOT_REQUESTED
    image_url: Optional[str] = None
    last_error: Optional[str] = None


class UpdateSceneRequest(BaseModel):
    """Request to update a scene's visual prompt"""
    visual_prompt: VisualPrompt
