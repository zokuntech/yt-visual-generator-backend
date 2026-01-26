import json
import os
import logging
from typing import Tuple
from openai import OpenAI
from app.models.scene import ScenePlan, VisualPrompt, StyleConfig, Character, Composition, Camera, Expression, Pose
from app.models.job import StyleConfig as JobStyleConfig

logger = logging.getLogger(__name__)

# OpenAI pricing
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input": 0.150 / 1_000_000,
        "output": 0.600 / 1_000_000,
    }
}


class CinematographerService:
    """The Cinematographer - converts scene plan into visual prompt"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def generate_visual_prompt(
        self,
        scene_plan: ScenePlan,
        global_style: JobStyleConfig
    ) -> Tuple[VisualPrompt, float, int]:
        """
        🎥 THE CINEMATOGRAPHER
        Converts the director's plan into a detailed visual prompt
        Returns: (VisualPrompt, cost, tokens)
        """
        
        system_prompt = self._build_cinematographer_prompt(global_style)
        user_prompt = self._build_user_prompt(scene_plan)
        
        try:
            logger.debug(f"🎥 Cinematographer translating plan...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.6,  # Slightly lower - we want precision here
            )
            
            # Calculate cost
            usage = response.usage
            input_cost = usage.prompt_tokens * OPENAI_PRICING[self.model]["input"]
            output_cost = usage.completion_tokens * OPENAI_PRICING[self.model]["output"]
            total_cost = input_cost + output_cost
            total_tokens = usage.total_tokens
            
            # Parse response
            content = response.choices[0].message.content
            logger.info(f"   📋 Raw LLM Response length: {len(content)} chars")
            logger.info(f"   📋 First 300 chars: {content[:300]}")
            
            prompt_data = json.loads(content)
            logger.info(f"   📋 Parsed JSON keys: {list(prompt_data.keys())}")
            
            # Check if LLM included 'style' despite our instructions
            if 'style' in prompt_data:
                logger.warning(f"   ⚠️ LLM included 'style' field, removing it. Value: {prompt_data['style']}")
                del prompt_data['style']
            
            # Add required fields that aren't from LLM
            prompt_data["scene_id"] = scene_plan.scene_id
            prompt_data["sentence_text"] = scene_plan.sentence
            
            # Convert JobStyleConfig to scene.StyleConfig
            from app.models.scene import StyleConfig as SceneStyleConfig
            logger.info(f"   📋 Creating StyleConfig object...")
            style_obj = SceneStyleConfig(
                art_style=global_style.art_style,
                lighting=global_style.lighting,
                color_palette=global_style.color_palette,
                background=global_style.background,
                character_description=global_style.character_description,
                camera_angle=global_style.camera_angle,
                framing=global_style.framing,
                aspect_ratio=global_style.aspect_ratio
            )
            logger.info(f"   📋 StyleConfig created: {type(style_obj)}")
            prompt_data["style"] = style_obj
            logger.info(f"   📋 Added style to prompt_data. Final keys: {list(prompt_data.keys())}")
            
            # Create VisualPrompt
            logger.info(f"   📋 Creating VisualPrompt with data...")
            logger.info(f"   📋 prompt_data['style'] type: {type(prompt_data['style'])}")
            visual_prompt = VisualPrompt(**prompt_data)
            logger.info(f"   ✅ VisualPrompt created successfully!")
            
            logger.debug(f"   📸 Visual: {visual_prompt.composition.camera.shot_type}")
            
            return visual_prompt, total_cost, total_tokens
            
        except Exception as e:
            logger.error(f"❌ Cinematographer FAILED!")
            logger.error(f"   Error: {e}")
            logger.error(f"   Error type: {type(e).__name__}")
            
            import traceback
            logger.error(f"   Full traceback:")
            for line in traceback.format_exc().split('\n'):
                logger.error(f"     {line}")
            
            # Log what we were trying to do
            try:
                logger.error(f"   Scene ID: {scene_plan.scene_id}")
                logger.error(f"   Data keys available: {list(prompt_data.keys()) if 'prompt_data' in locals() else 'N/A'}")
                if 'prompt_data' in locals() and 'style' in prompt_data:
                    logger.error(f"   Style value type: {type(prompt_data['style'])}")
                    logger.error(f"   Style value: {prompt_data['style']}")
            except:
                pass
            
            # Fallback to basic prompt
            logger.info(f"   Using fallback prompt...")
            return self._create_fallback_prompt(scene_plan, global_style), 0.0, 0
    
    def generate_visual_prompt_with_instruction(
        self,
        scene_plan: ScenePlan,
        global_style: JobStyleConfig,
        instruction: str
    ) -> Tuple[VisualPrompt, float, int]:
        """
        🎥 THE CINEMATOGRAPHER (with user instruction)
        Modifies the visual prompt based on user instruction
        Returns: (VisualPrompt, cost, tokens)
        """
        
        system_prompt = self._build_cinematographer_prompt(global_style)
        user_prompt = f"""ORIGINAL SCENE PLAN:

Sentence: "{scene_plan.sentence}"

Narrative Role: {scene_plan.narrative_role}
Emotional Tone: {scene_plan.emotional_tone}
Energy Level: {scene_plan.energy_level}

USER INSTRUCTION:
"{instruction}"

Please modify the visual prompt to incorporate this instruction while maintaining the overall scene context.
For example:
- "make character smile" → adjust expression to smiling/happy
- "add laptop on desk" → add laptop to props and character interaction
- "change to outdoor park" → change setting to park
- "zoom in on face" → change camera to close_up
- "add more light" → adjust lighting description

Convert this plan with the modifications into a detailed visual prompt.
"""
        
        try:
            logger.debug(f"🎥 Cinematographer applying instruction: {instruction[:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,  # Balanced for instruction following
            )
            
            # Calculate cost
            usage = response.usage
            input_cost = usage.prompt_tokens * OPENAI_PRICING[self.model]["input"]
            output_cost = usage.completion_tokens * OPENAI_PRICING[self.model]["output"]
            total_cost = input_cost + output_cost
            total_tokens = usage.total_tokens
            
            # Parse response
            content = response.choices[0].message.content
            logger.debug(f"📋 Raw LLM Response length: {len(content)} chars")
            
            prompt_data = json.loads(content)
            logger.debug(f"📋 Parsed JSON keys: {list(prompt_data.keys())}")
            
            # Remove style if LLM generated it
            if "style" in prompt_data:
                logger.warning("⚠️ LLM generated 'style' field. Removing it.")
                del prompt_data["style"]
            
            # Add required fields
            prompt_data["scene_id"] = scene_plan.scene_id
            prompt_data["sentence_text"] = scene_plan.sentence
            
            # Create style config
            scene_style_config = StyleConfig(
                art_style=global_style.art_style,
                lighting=global_style.lighting,
                color_palette=global_style.color_palette,
                background=global_style.background,
                character_description=global_style.character_description,
                camera_angle=global_style.camera_angle,
                framing=global_style.framing,
                aspect_ratio=global_style.aspect_ratio
            )
            prompt_data["style"] = scene_style_config
            
            # Create VisualPrompt
            visual_prompt = VisualPrompt(**prompt_data)
            
            logger.info(f"✅ Visual prompt modified with instruction")
            
            return visual_prompt, total_cost, total_tokens
            
        except Exception as e:
            logger.error(f"❌ Cinematographer failed with instruction: {e}")
            # Fallback to original scene plan
            return self._create_fallback_prompt(scene_plan, global_style), 0.0, 0
    
    def _build_cinematographer_prompt(self, global_style: JobStyleConfig) -> str:
        """Build the cinematographer's system prompt"""
        
        return f"""You are THE CINEMATOGRAPHER.

The Director has given you a scene plan. Your job: translate it into precise visual instructions for the renderer.

GLOBAL STYLE (use these exactly):
- Art Style: {global_style.art_style}
- Lighting: {global_style.lighting}
- Color Palette: {global_style.color_palette}
- Background Base: {global_style.background}
- Character Base: {global_style.character_description}

IMPORTANT: The global style will be added automatically. DO NOT include a "style" field in your response.

RESPOND WITH THIS EXACT JSON STRUCTURE:

{{
  "characters": [
    {{
      "role": "From scene plan (OR empty array [] if scene plan indicates NO_CHARACTER or NONE presence - for B-ROLL shots)",
      "description": "{global_style.character_description} + specific details from plan (OMIT if no character)",
      "expression": {{
        "primary": "Match emotional tone from plan",
        "micro_expression": "subtle detail based on emotion",
        "eye_focus": "Match interaction type from plan"
      }},
      "pose": {{
        "body_language": "Match energy level and emotion",
        "hand_position": "Match interaction from plan",
        "stance": "Match setting and motion"
      }}
    }}
  ],
  "props": ["List of prop types from plan (REQUIRED even for b-roll - focus on objects in frame)"],
  "setting": "Natural language description combining: setting.environment + symbolic_elements + props (FOR B-ROLL: focus on environment, objects, details, atmosphere)",
  "composition": {{
    "camera": {{
      "shot_type": "From camera_intent in plan (FOR B-ROLL: often extreme_close_up, macro, detail shots)",
      "angle": "From camera_intent in plan",
      "movement": "From motion in plan (FOR B-ROLL: can be static, slow_pan, or focus on object movement)"
    }},
    "framing": "From camera_intent in plan (FOR B-ROLL: emphasize interesting framing, depth, textures)",
    "depth": "Choose: shallow (for close-ups) | normal | deep (for wide shots)",
    "extras": "no_text_no_logos_no_watermarks"
  }}
}}

🎬 B-ROLL SCENES (When plan shows NO_CHARACTER or presence:NONE):
- Leave characters array EMPTY: []
- Focus setting on OBJECTS, ENVIRONMENT, DETAILS, ATMOSPHERE
- Props become the MAIN SUBJECT (phones, coffee cups, windows, nature)
- Camera shots often: extreme_close_up, macro, detail, overhead, abstract angles
- Examples:
  * "Phone buzzing on table" → characters: [], props: ["smartphone", "coffee_cup"], setting: "close-up of phone screen lighting up on wooden desk"
  * "Rain on window" → characters: [], props: ["raindrops", "window_glass"], setting: "raindrops streaming down foggy window with blurred city lights beyond"
  * "Empty street at dawn" → characters: [], props: ["streetlights", "fog"], setting: "quiet urban street with morning mist and golden light"

CRITICAL RULES:
1. ❗ You MUST use the camera shot from the scene plan - no changes
2. ❗ Expression must match emotional_tone from plan
3. ❗ Body language must match energy_level from plan
4. ❗ Setting description must include symbolic_elements from plan
5. Character description is GLOBAL style + small adaptations for this scene
6. Translate director's intent into concrete visual details
7. Props must be naturally integrated into setting description

Example Translation:
Plan: emotional_tone="detached", camera_intent.shot="close_up", props=[{{type:"phone"}}]
Your output: expression.primary="distant", camera.shot_type="close_up", setting="quiet room, phone face-down on table"

You are NOT making creative decisions. You are EXECUTING the director's vision.
"""
    
    def _build_user_prompt(self, scene_plan: ScenePlan) -> str:
        """Build the user prompt with the scene plan"""
        # Format characters, props, etc. properly
        characters_list = [{"role": c.role, "presence": c.presence, "interaction": c.interaction} for c in scene_plan.characters]
        props_list = [{"type": p.type, "symbolism": p.symbolism} for p in scene_plan.props]
        
        return f"""SCENE PLAN:

Sentence: "{scene_plan.sentence}"

Narrative Role: {scene_plan.narrative_role}
Emotional Tone: {scene_plan.emotional_tone}
Energy Level: {scene_plan.energy_level}

Characters: {json.dumps(characters_list, indent=2)}
Props: {json.dumps(props_list, indent=2)}
Setting: {json.dumps(scene_plan.setting.dict(), indent=2)}
Camera Intent: {json.dumps(scene_plan.camera_intent.dict(), indent=2)}
Motion: {scene_plan.motion}

Convert this plan into a detailed visual prompt.
"""
    
    def _create_fallback_prompt(
        self,
        scene_plan: ScenePlan,
        global_style: JobStyleConfig
    ) -> VisualPrompt:
        """Create a basic fallback prompt if cinematographer fails"""
        
        # If the scene plan has no characters (b-roll), don't add a character to fallback
        characters_list = []
        if scene_plan.characters:
            characters_list = [
                Character(
                    role="main_character",
                    description=global_style.character_description,
                    expression=Expression(
                        primary=scene_plan.emotional_tone,
                        eye_focus="neutral"
                    ),
                    pose=Pose(
                        body_language="neutral",
                        hand_position="at_sides",
                        stance="standing"
                    )
                )
            ]
        
        return VisualPrompt(
            scene_id=scene_plan.scene_id,
            sentence_text=scene_plan.sentence,
            style=StyleConfig(
                art_style=global_style.art_style,
                lighting=global_style.lighting,
                color_palette=global_style.color_palette,
                background=global_style.background,
                aspect_ratio=global_style.aspect_ratio
            ),
            characters=characters_list,
            props=[],
            setting=scene_plan.setting.environment,
            composition=Composition(
                camera=Camera(
                    shot_type=scene_plan.camera_intent.shot,
                    angle=scene_plan.camera_intent.angle,
                    movement=scene_plan.motion if scene_plan.motion else "static"
                ),
                framing=scene_plan.camera_intent.framing,
                depth="normal",
                extras="no_text_no_logos_no_watermarks"
            )
        )


# Global singleton
cinematographer_service = CinematographerService() if os.getenv("OPENAI_API_KEY") else None
