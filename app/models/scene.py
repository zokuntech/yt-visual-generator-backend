from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class ImageStatus(str, Enum):
    """Status of image generation for a scene"""
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    GENERATED = "generated"
    FAILED = "failed"


class VideoStatus(str, Enum):
    """Status of video generation for a scene"""
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    PROCESSING = "processing"
    GENERATED = "generated"
    FAILED = "failed"


# ===== DIRECTOR LAYER =====

class SceneCharacter(BaseModel):
    """Character in the scene plan"""
    role: str = "main_character"
    presence: str = "primary"  # primary | background | mentioned
    interaction: str = "neutral"  # isolated | engaging | ignoring | reacting


class SceneProp(BaseModel):
    """Object or prop in the scene"""
    type: str  # phone, mirror, window, etc.
    symbolism: Optional[str] = None
    interaction: str = "present"  # present | interacting | background


class SceneSetting(BaseModel):
    """Setting details for the scene"""
    location: str = "interior"  # interior | exterior | transitional
    environment: str  # bedroom, café, window_side, etc.
    symbolic_elements: List[str] = Field(default_factory=list)


class CameraIntent(BaseModel):
    """Camera direction from the director"""
    shot: str = "medium_shot"  # close_up | medium | wide | over_shoulder | profile
    angle: str = "eye_level"  # eye_level | slightly_low | slightly_high
    framing: str = "centered"  # centered | rule_of_thirds | off_center


class ScenePlan(BaseModel):
    """Director's plan for the scene (BEFORE visual generation)"""
    scene_id: str
    sentence: str
    narrative_role: str  # emotional_low_point | realization | tension | release | reflection
    emotional_tone: str  # conflicted | hopeful | detached | overwhelmed | calm | tense
    energy_level: str = "medium"  # low | medium | high
    visual_focus: str = "character"  # internal_state | character | environment | interaction
    characters: List[SceneCharacter] = Field(default_factory=list)
    props: List[SceneProp] = Field(default_factory=list)
    setting: SceneSetting
    camera_intent: CameraIntent
    motion: str = "still"  # still | subtle_movement | dynamic
    variation_from_previous: bool = True


# ===== CINEMATOGRAPHER LAYER =====


class StyleConfig(BaseModel):
    """Visual style configuration"""
    art_style: str = "professional_youtube_style"
    lighting: str = "natural_lighting"
    color_palette: str = "warm_neutral"
    background: str = "clean_simple"
    character_description: str = "content creator, approachable, professional casual"
    camera_angle: str = "medium_shot"
    framing: str = "centered"
    aspect_ratio: str = "16:9"  # Image aspect ratio: "1:1", "16:9", "9:16", "4:3", "3:4"


class Expression(BaseModel):
    """Detailed expression breakdown"""
    primary: str  # distant | soft | tense | resigned | hopeful | guarded
    micro_expression: Optional[str] = None  # tight_lips | raised_brow | downward_gaze
    eye_focus: str = "neutral"  # off_camera | downward | direct | distant


class Pose(BaseModel):
    """Body language and positioning"""
    body_language: str = "neutral"  # closed | open | guarded | relaxed | tense
    hand_position: str = "at_sides"  # crossed | touching_face | holding_object | at_sides
    stance: str = "standing"  # standing | seated | leaning | walking


class Character(BaseModel):
    """Character description in a scene (from cinematographer)"""
    role: str = "main_subject"
    description: str
    expression: Expression
    pose: Pose


class Camera(BaseModel):
    """Camera setup details"""
    shot_type: str = "medium_shot"  # close_up | medium | wide | over_shoulder | profile
    angle: str = "eye_level"  # eye_level | slightly_low | slightly_high
    movement: str = "static"  # static | implied_motion


class Composition(BaseModel):
    """Scene composition details"""
    camera: Camera
    framing: str = "centered"  # centered | rule_of_thirds | off_center | dynamic
    depth: str = "normal"  # shallow | normal | deep
    extras: str = "no_text_no_logos_no_watermarks"


class VisualPrompt(BaseModel):
    """Structured visual prompt for image generation (from cinematographer)"""
    scene_id: str
    sentence_text: str
    style: StyleConfig
    characters: List[Character] = Field(default_factory=list)
    props: List[str] = Field(default_factory=list)  # Simplified prop list for rendering
    setting: str  # Natural language setting description
    composition: Composition


class Scene(BaseModel):
    """Represents one sentence/scene in the storyboard"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str
    index: int
    sentence_text: str
    scene_plan: Optional[ScenePlan] = None  # Director's plan
    visual_prompt: Optional[VisualPrompt] = None  # Cinematographer's prompt
    image_status: ImageStatus = ImageStatus.NOT_REQUESTED
    image_url: Optional[str] = None
    video_status: VideoStatus = VideoStatus.NOT_REQUESTED
    video_url: Optional[str] = None
    video_operation_name: Optional[str] = None  # For tracking async Veo operation
    last_error: Optional[str] = None


class UpdateSceneRequest(BaseModel):
    """Request to update a scene's visual prompt"""
    visual_prompt: VisualPrompt
