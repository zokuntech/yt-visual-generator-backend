"""
Data models for YouTube Shorts (visual-only, no narration)
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class ShortCategory(str, Enum):
    """Types of satisfying/timelapse content"""
    EPOXY_FLOORING = "epoxy_flooring"
    FURNITURE_BUILD = "furniture_build"
    ROOM_RENOVATION = "room_renovation"
    PAINTING = "painting"
    WOODWORKING = "woodworking"
    CONCRETE_POURING = "concrete_pouring"
    CRAFTING = "crafting"
    FOOD_PREPARATION = "food_preparation"
    CUSTOM = "custom"


class ShortStatus(str, Enum):
    """Status of a short generation job"""
    PENDING = "pending"
    GENERATING_CONCEPTS = "generating_concepts"
    AWAITING_SELECTION = "awaiting_selection"
    GENERATING_STAGES = "generating_stages"
    GENERATING_IMAGES = "generating_images"
    GENERATING_VIDEOS = "generating_videos"
    COMPLETED = "completed"
    FAILED = "failed"


class TransformationConcept(BaseModel):
    """A single transformation idea (e.g., 'Modern Kitchen Epoxy Floor')"""
    index: int
    title: str
    description: str
    category: ShortCategory


class StageType(str, Enum):
    """The six stages of transformation"""
    EMPTY_ROOM = "empty_room"              # Stage 1: Raw/before
    PREP_WORK = "prep_work"                # Stage 2: Workers preparing (2-3 people)
    ACTIVE_INSTALLATION = "active_installation"  # Stage 3: Main work (3-4 people, key moment)
    FINISHING_TOUCHES = "finishing_touches"      # Stage 4: Workers finishing up (2-3 people)
    COMPLETED_EMPTY = "completed_empty"    # Stage 5: Finished, workers leaving
    FULLY_FURNISHED = "fully_furnished"    # Stage 6: Styled and complete


class TransformationStage(BaseModel):
    """One stage of the transformation (e.g., 'Empty Room')"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage_type: StageType
    stage_number: int  # 1-4
    
    # Visual details
    detailed_description: str  # Full prompt for image generation
    required_elements: List[str] = Field(default_factory=list)
    workers_present: bool = False
    worker_count: Optional[int] = None
    
    # Generated assets
    image_url: Optional[str] = None
    image_status: str = "not_generated"
    
    # Cost tracking
    image_generation_cost: float = 0.0


class TransitionVideo(BaseModel):
    """Video animating between two stages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Which stages this connects
    from_stage: StageType
    to_stage: StageType
    transition_number: int  # 1-3
    
    # Video details
    motion_description: str  # Detailed motion prompt for Veo
    duration_seconds: int = 8
    
    # Generated assets
    video_url: Optional[str] = None
    video_status: str = "not_generated"
    video_operation_name: Optional[str] = None
    
    # Cost tracking
    video_generation_cost: float = 0.0


class ShortProject(BaseModel):
    """A complete timelapse/transformation short project"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Project metadata
    category: ShortCategory
    selected_concept: Optional[TransformationConcept] = None
    
    # Transformation details
    room_type: str  # "Modern Kitchen", "Garage Workshop", etc.
    transformation_description: str
    
    # Visual style
    visual_quality: str = "8K cinematic photorealistic"
    camera_angle: str = "static wide angle timelapse"
    aspect_ratio: str = "9:16"  # Shorts default to vertical
    
    # Generation stages
    stages: List[TransformationStage] = Field(default_factory=list)
    transitions: List[TransitionVideo] = Field(default_factory=list)
    
    # Status tracking
    status: ShortStatus = ShortStatus.PENDING
    progress_percentage: int = 0
    current_step: str = ""
    last_error: Optional[str] = None
    
    # Cost tracking
    total_cost: float = 0.0
    prompt_generation_cost: float = 0.0
    image_generation_cost: float = 0.0
    video_generation_cost: float = 0.0
    
    # Timestamps
    created_at: Optional[str] = None
    completed_at: Optional[str] = None


class CreateShortRequest(BaseModel):
    """Request to create a new short"""
    category: ShortCategory
    concept_index: Optional[int] = None  # If user already selected from concepts
    custom_description: Optional[str] = None  # For custom transformations
    aspect_ratio: str = "9:16"  # "9:16" for Shorts, "16:9" for landscape


class ConceptGenerationRequest(BaseModel):
    """Request to generate transformation concepts"""
    category: ShortCategory
    num_concepts: int = 10


class ConceptSelectionRequest(BaseModel):
    """User selecting a concept to develop"""
    project_id: str
    concept_index: int  # 1-10


class AnimateShortRequest(BaseModel):
    """Request to generate transition videos for a short"""
    project_id: str
    generate_all: bool = True  # Generate all 3 transitions
    specific_transition: Optional[int] = None  # Or just one (1-3)
