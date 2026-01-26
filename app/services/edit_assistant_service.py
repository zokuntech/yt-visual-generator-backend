import json
import os
import logging
from typing import List, Dict, Tuple
from openai import OpenAI
from app.models.scene import Scene, VisualPrompt

logger = logging.getLogger(__name__)

# OpenAI pricing
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input": 0.150 / 1_000_000,
        "output": 0.600 / 1_000_000,
    }
}


class EditSuggestion(dict):
    """A suggested edit for a scene"""
    def __init__(self, category: str, description: str, example_instruction: str):
        super().__init__({
            "category": category,
            "description": description,
            "example_instruction": example_instruction
        })


class EditAssistantService:
    """
    Helps users edit scenes by:
    1. Analyzing what can be changed in a scene
    2. Suggesting improvements
    3. Translating vague instructions into specific edits
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def analyze_scene_for_edits(self, scene: Scene) -> Dict:
        """
        Analyze a scene and return what can be edited
        
        Returns a structured breakdown of editable elements:
        - Character (pose, expression, activity)
        - Setting (location, lighting, time of day)
        - Props (add, remove, modify)
        - Camera (angle, shot type, framing)
        - Mood (emotional tone, atmosphere)
        """
        if not scene.visual_prompt:
            return {
                "error": "Scene has no visual prompt to analyze",
                "suggestions": []
            }
        
        vp = scene.visual_prompt
        
        # Extract character info from first character if available
        main_char = vp.characters[0] if vp.characters and len(vp.characters) > 0 else None
        
        return {
            "scene_id": scene.id,
            "sentence": scene.sentence_text,
            "current_state": {
                "character": {
                    "pose": main_char.pose.stance if main_char and main_char.pose else "unknown",
                    "expression": main_char.expression.primary if main_char and main_char.expression else "unknown",
                    "activity": main_char.pose.hand_position if main_char and main_char.pose else "unknown"
                },
                "setting": vp.setting if vp.setting else "unknown",
                "camera": {
                    "shot": vp.composition.camera.shot_type if vp.composition and vp.composition.camera else "unknown",
                    "angle": vp.composition.camera.angle if vp.composition and vp.composition.camera else "unknown"
                },
                "props": vp.props if vp.props else []
            },
            "edit_categories": [
                {
                    "category": "Character Pose & Expression",
                    "suggestions": [
                        EditSuggestion(
                            "pose",
                            "Change what the character is doing",
                            f"make the character {self._suggest_alternative_pose(vp)}"
                        ),
                        EditSuggestion(
                            "expression",
                            "Change facial expression",
                            f"make the character look {self._suggest_alternative_expression(vp)}"
                        ),
                        EditSuggestion(
                            "activity",
                            "Change hand activity",
                            "make the character hold a phone / type on laptop / sip coffee"
                        )
                    ]
                },
                {
                    "category": "Setting & Atmosphere",
                    "suggestions": [
                        EditSuggestion(
                            "location",
                            "Change the location",
                            "move this to a coffee shop / park / office / home"
                        ),
                        EditSuggestion(
                            "lighting",
                            "Change lighting/time of day",
                            "make it golden hour / nighttime / rainy / bright sunny day"
                        ),
                        EditSuggestion(
                            "atmosphere",
                            "Change the mood of the environment",
                            "make the setting more cozy / modern / busy / quiet"
                        )
                    ]
                },
                {
                    "category": "Props & Objects",
                    "suggestions": [
                        EditSuggestion(
                            "add_props",
                            "Add objects to the scene",
                            "add a laptop / coffee cup / notebook / plant"
                        ),
                        EditSuggestion(
                            "remove_props",
                            "Remove objects from the scene",
                            f"remove the {vp.props[0] if vp.props else 'object'}"
                        ),
                        EditSuggestion(
                            "change_props",
                            "Replace objects",
                            "replace the phone with a book"
                        )
                    ]
                },
                {
                    "category": "Camera & Composition",
                    "suggestions": [
                        EditSuggestion(
                            "camera_shot",
                            "Change camera distance",
                            "zoom in for close-up / pull back for wide shot"
                        ),
                        EditSuggestion(
                            "camera_angle",
                            "Change camera angle",
                            "shoot from above / low angle / eye level"
                        ),
                        EditSuggestion(
                            "framing",
                            "Change composition",
                            "center the character / use rule of thirds / add depth"
                        )
                    ]
                },
                {
                    "category": "People & Interaction",
                    "suggestions": [
                        EditSuggestion(
                            "add_people",
                            "Add other people to the scene",
                            "add a friend / add background people / add a crowd"
                        ),
                        EditSuggestion(
                            "remove_people",
                            "Make character alone",
                            "remove other people / make it just the main character"
                        ),
                        EditSuggestion(
                            "interaction",
                            "Change how people interact",
                            "make them talking / laughing together / working side by side"
                        )
                    ]
                }
            ]
        }
    
    def refine_edit_instruction(
        self,
        scene: Scene,
        raw_instruction: str
    ) -> Tuple[str, float, int]:
        """
        Take a vague edit instruction and make it more specific and actionable
        
        Example:
        - Input: "make it happier"
        - Output: "Change character expression to smiling with eyes crinkling, add warm golden lighting, brighten the atmosphere"
        
        Returns: (refined_instruction, cost, tokens)
        """
        if not scene.visual_prompt:
            return raw_instruction, 0.0, 0
        
        vp = scene.visual_prompt
        main_char = vp.characters[0] if vp.characters and len(vp.characters) > 0 else None
        
        char_pose = main_char.pose.stance if main_char and main_char.pose else 'unknown'
        char_expr = main_char.expression.primary if main_char and main_char.expression else 'unknown'
        
        prompt = f"""You are a visual editing assistant helping refine user instructions for scene edits.

Current Scene:
- Text: "{scene.sentence_text}"
- Character: {char_pose}, {char_expr}
- Setting: {vp.setting if vp.setting else 'unknown'}
- Camera: {vp.composition.camera.shot_type if vp.composition and vp.composition.camera else 'unknown'}
- Props: {', '.join(vp.props) if vp.props else 'none'}

User's Edit Request: "{raw_instruction}"

Task: Transform this vague instruction into a SPECIFIC, ACTIONABLE edit instruction.

Guidelines:
- Be concrete: Instead of "make it better", specify "change character to smiling, add warm lighting"
- Address specific elements: pose, expression, setting, props, camera, lighting
- Keep it natural and conversational
- If the instruction is already specific, just clarify or enhance it slightly

Examples:
- "make it happier" → "change character expression to bright smile with relaxed posture, add warm golden hour lighting, create uplifting atmosphere"
- "add more stuff" → "add a laptop, coffee cup, and notebook on the desk, create a busy working environment"
- "different vibe" → "change setting to nighttime with dramatic lighting, add moody blue tones, make it more contemplative"
- "zoom out" → "change to wide shot showing full environment and context around character"

Respond with ONLY the refined instruction, no explanation or preamble."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            # Calculate cost
            usage = response.usage
            input_cost = usage.prompt_tokens * OPENAI_PRICING[self.model]["input"]
            output_cost = usage.completion_tokens * OPENAI_PRICING[self.model]["output"]
            total_cost = input_cost + output_cost
            total_tokens = usage.total_tokens
            
            refined = response.choices[0].message.content.strip()
            
            logger.info(f"🎨 Refined edit instruction:")
            logger.info(f"   Original: {raw_instruction}")
            logger.info(f"   Refined: {refined}")
            
            return refined, total_cost, total_tokens
            
        except Exception as e:
            logger.error(f"❌ Failed to refine instruction: {e}")
            return raw_instruction, 0.0, 0
    
    def _suggest_alternative_pose(self, vp: VisualPrompt) -> str:
        """Suggest an alternative pose based on current pose"""
        main_char = vp.characters[0] if vp.characters and len(vp.characters) > 0 else None
        current = main_char.pose.stance if main_char and main_char.pose else ""
        
        alternatives = {
            "seated": "standing up and stretching",
            "standing": "sitting down relaxed",
            "walking": "standing still and looking around",
            "leaning": "standing straight",
            "default": "leaning back with arms crossed"
        }
        
        for key, alt in alternatives.items():
            if key in current.lower():
                return alt
        
        return alternatives["default"]
    
    def _suggest_alternative_expression(self, vp: VisualPrompt) -> str:
        """Suggest an alternative expression based on current expression"""
        main_char = vp.characters[0] if vp.characters and len(vp.characters) > 0 else None
        current = main_char.expression.primary if main_char and main_char.expression else ""
        
        alternatives = {
            "neutral": "smiling warmly",
            "smiling": "thoughtfully serious",
            "sad": "hopeful with slight smile",
            "serious": "relaxed and content",
            "worried": "calm and focused",
            "excited": "peacefully happy",
            "confused": "understanding and clear",
            "default": "confident and determined"
        }
        
        for key, alt in alternatives.items():
            if key in current.lower():
                return alt
        
        return alternatives["default"]


# Global singleton
edit_assistant_service = EditAssistantService() if os.getenv("OPENAI_API_KEY") else None
