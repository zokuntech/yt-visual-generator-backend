import json
import os
import logging
from typing import Optional, Tuple
from openai import OpenAI
from app.models.scene import VisualPrompt, StyleConfig, Character, Composition
from app.models.job import StyleConfig as JobStyleConfig

logger = logging.getLogger(__name__)

# OpenAI pricing (as of 2024)
# https://openai.com/api/pricing/
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input": 0.150 / 1_000_000,   # $0.150 per 1M input tokens
        "output": 0.600 / 1_000_000,  # $0.600 per 1M output tokens
    },
    "gpt-4o": {
        "input": 2.50 / 1_000_000,
        "output": 10.00 / 1_000_000,
    }
}


class LLMService:
    """Service for generating structured visual prompts using ChatGPT"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Fast and cost-effective
    
    def generate_visual_prompt(
        self,
        scene_id: str,
        sentence_text: str,
        style_config: Optional[JobStyleConfig] = None
    ) -> Tuple[VisualPrompt, float, int]:
        """
        Generate a structured visual prompt for a sentence
        Returns: (VisualPrompt, cost_in_usd, tokens_used)
        """
        if not style_config:
            style_config = JobStyleConfig()
        
        system_prompt = self._build_system_prompt(style_config)
        user_prompt = f"Generate a visual prompt for this sentence:\n\n{sentence_text}"
        
        try:
            logger.debug(f"Calling OpenAI API for scene: {scene_id}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            
            # Calculate cost
            usage = response.usage
            input_cost = usage.prompt_tokens * OPENAI_PRICING[self.model]["input"]
            output_cost = usage.completion_tokens * OPENAI_PRICING[self.model]["output"]
            total_cost = input_cost + output_cost
            total_tokens = usage.total_tokens
            
            logger.debug(f"   Tokens: {usage.prompt_tokens} in + {usage.completion_tokens} out = {total_tokens} total")
            logger.debug(f"   Cost: ${total_cost:.6f}")
            
            # Parse the JSON response
            content = response.choices[0].message.content
            prompt_data = json.loads(content)
            
            # Add scene_id and sentence_text to the response
            prompt_data["scene_id"] = scene_id
            prompt_data["sentence_text"] = sentence_text
            
            # Create and validate the VisualPrompt model
            visual_prompt = VisualPrompt(**prompt_data)
            return visual_prompt, total_cost, total_tokens
            
        except Exception as e:
            logger.warning(f"LLM generation failed, using fallback: {str(e)}")
            # Return a basic fallback prompt if generation fails
            fallback_prompt = self._create_fallback_prompt(scene_id, sentence_text, style_config)
            return fallback_prompt, 0.0, 0
    
    def _build_system_prompt(self, style_config: JobStyleConfig) -> str:
        """Build the system prompt for the LLM"""
        return f"""You are an expert visual director for YouTube content creation.

Your task is to convert script sentences into STRUCTURED visual prompts for image generation.

CRITICAL: You MUST respond with valid JSON following this EXACT schema:

{{
  "style": {{
    "art_style": "{style_config.art_style}",
    "lighting": "{style_config.lighting}",
    "color_palette": "{style_config.color_palette}",
    "background": "{style_config.background}"
  }},
  "characters": [
    {{
      "role": "main_subject",
      "description": "{style_config.character_description}",
      "expression": "confident_calm | excited | thoughtful | neutral | surprised | pensive",
      "pose": "{style_config.camera_angle} angle, {style_config.framing} framing"
    }}
  ],
  "composition": {{
    "camera_angle": "{style_config.camera_angle}",
    "framing": "{style_config.framing}",
    "extras": "no_text_no_logos_no_watermarks"
  }}
}}

STYLE GUIDE:
- Art Style: {style_config.art_style}
- Lighting: {style_config.lighting}
- Color Palette: {style_config.color_palette}
- Background: {style_config.background}
- Character: {style_config.character_description}
- Camera: {style_config.camera_angle}
- Framing: {style_config.framing}

RULES:
1. Use EXACTLY the style settings provided above
2. Keep the character description consistent: {style_config.character_description}
3. Adapt the expression and minor pose details based on the sentence content
4. Only vary: expression and subtle pose adjustments
5. Respond ONLY with valid JSON (no markdown, no extra text)
6. Ensure all scenes maintain visual consistency across the video
"""
    
    def _create_fallback_prompt(
        self,
        scene_id: str,
        sentence_text: str,
        style_config: JobStyleConfig
    ) -> VisualPrompt:
        """Create a basic fallback prompt if LLM fails"""
        return VisualPrompt(
            scene_id=scene_id,
            sentence_text=sentence_text,
            style=StyleConfig(
                art_style=style_config.art_style,
                lighting=style_config.lighting,
                color_palette=style_config.color_palette,
                background=style_config.background
            ),
            characters=[
                Character(
                    role="main_subject",
                    description=style_config.character_description,
                    expression="confident_calm",
                    pose="front_facing"
                )
            ],
            composition=Composition(
                camera_angle=style_config.camera_angle,
                framing=style_config.framing,
                extras="no_text_no_logos_no_watermarks"
            )
        )


# Global singleton
llm_service = LLMService() if os.getenv("OPENAI_API_KEY") else None
