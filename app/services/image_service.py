import os
import base64
import logging
import re
from typing import Optional, Tuple
from google import genai
from google.genai import types
from app.models.scene import VisualPrompt

logger = logging.getLogger(__name__)

# Gemini pricing (as of January 2024)
# https://ai.google.dev/pricing
GEMINI_PRICING = {
    "gemini-2.5-flash-image": {
        "per_image": 0.00032,  # $0.00032 per image (~1290 tokens)
    },
    "gemini-3-pro-image-preview": {
        "1K": 0.00028,  # $0.00028 per image at 1K resolution
        "2K": 0.00028,  # Same price for 2K
        "4K": 0.00050,  # $0.00050 per image at 4K resolution
    }
}


class ImageService:
    """Service for generating images using Google Gemini (Nano Banana)"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY environment variable is required")
        
        self.model_name = "gemini-2.5-flash-image"
        
        # Using NEW Google Gen AI SDK with aspect ratio support
        # https://ai.google.dev/gemini-api/docs/image-generation#aspect_ratios_and_image_size
        logger.info("🎨 Initializing Google Gen AI SDK with aspect ratio support")
        os.environ["GOOGLE_API_KEY"] = api_key
        self.client = genai.Client()
    
    def _save_debug_image(self, image_bytes: bytes, scene_id: str):
        """Save image to disk for debugging (optional)"""
        try:
            debug_dir = "debug_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
            
            filename = f"{debug_dir}/scene_{scene_id[:8]}.png"
            with open(filename, 'wb') as f:
                f.write(image_bytes)
            logger.info(f"   💾 Debug: Saved image to {filename}")
        except Exception as e:
            logger.warning(f"   ⚠️ Could not save debug image: {e}")
    
    def generate_image(self, visual_prompt: VisualPrompt) -> Tuple[str, float, int]:
        """
        Generate an image from a structured visual prompt
        Returns: (data_uri, cost_in_usd, tokens_used)
        """
        try:
            # Convert structured prompt to natural language
            prompt_text = self._convert_to_text_prompt(visual_prompt)
            
            # Get aspect ratio from style config (default to 16:9)
            aspect_ratio = "16:9"
            if visual_prompt.style and hasattr(visual_prompt.style, 'aspect_ratio'):
                aspect_ratio = visual_prompt.style.aspect_ratio
            
            logger.info(f"🎨 Calling Gemini API with NEW SDK (aspect ratio support)...")
            logger.info(f"   Model: {self.model_name}")
            logger.info(f"   Aspect Ratio: {aspect_ratio}")
            logger.info(f"   Prompt: {prompt_text[:100]}...")
            
            # Generate image with proper aspect ratio configuration
            # https://ai.google.dev/gemini-api/docs/image-generation#aspect_ratios_and_image_size
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt_text],
                config={
                    "imageConfig": {
                        "aspectRatio": aspect_ratio
                    }
                }
            )
            
            logger.info(f"   Response received from Gemini")
            
            # Extract image from response
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    logger.info(f"   Found text part: {part.text[:100]}...")
                elif hasattr(part, 'inline_data') and part.inline_data:
                    logger.info(f"   ✅ Image found! Extracting...")
                    image_bytes = part.inline_data.data
                    logger.info(f"   Image bytes length: {len(image_bytes)}")
                    
                    if visual_prompt.scene_id:
                        self._save_debug_image(image_bytes, visual_prompt.scene_id)
                    
                    cost = GEMINI_PRICING[self.model_name]["per_image"]
                    tokens = 1290
                    
                    logger.info(f"   💰 Cost: ${cost:.6f}")
                    logger.info(f"   🎫 Tokens: ~{tokens}")
                    
                    data_uri = self._encode_image_to_data_uri(image_bytes)
                    return data_uri, cost, tokens
            
            raise RuntimeError("No image generated in response")
            
        except Exception as e:
            logger.error(f"   ❌ Exception in image generation: {type(e).__name__}")
            logger.error(f"   Exception message: {str(e)}")
            raise RuntimeError(f"Image generation failed: {str(e)}")
    
    def _convert_to_text_prompt(self, visual_prompt: VisualPrompt) -> str:
        """Convert structured JSON prompt to natural language for image generation"""
        parts = []
        
        # Style
        style = visual_prompt.style
        parts.append(f"Style: {style.art_style}")
        parts.append(f"Lighting: {style.lighting}")
        parts.append(f"Color palette: {style.color_palette}")
        parts.append(f"Background: {style.background}")
        
        # Characters
        if visual_prompt.characters:
            parts.append("\nCharacters:")
            for char in visual_prompt.characters:
                # Handle new Character structure with Expression and Pose objects
                expression_str = char.expression.primary if hasattr(char.expression, 'primary') else str(char.expression)
                pose_str = char.pose.body_language if hasattr(char.pose, 'body_language') else str(char.pose)
                parts.append(
                    f"- {char.role}: {char.description}, "
                    f"expression: {expression_str}, pose: {pose_str}"
                )
        
        # Composition - Handle new Camera structure
        comp = visual_prompt.composition
        camera = comp.camera
        parts.append(f"\nCamera: {camera.shot_type} at {camera.angle} angle")
        if camera.movement and camera.movement != "static":
            parts.append(f"Camera movement: {camera.movement}")
        parts.append(f"Framing: {comp.framing}")
        parts.append(f"Important: {comp.extras}")
        
        # Add the original sentence for context
        parts.append(f"\nScene context: {visual_prompt.sentence_text}")
        
        return "\n".join(parts)
    
    def _encode_image_to_data_uri(self, image_data: bytes) -> str:
        """Convert image bytes to base64 data URI"""
        if not isinstance(image_data, bytes):
            raise TypeError(f"Expected bytes, got {type(image_data)}")
        
        if len(image_data) == 0:
            raise ValueError("Image data is empty")
        
        # Encode to base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # Validate base64 (should only contain valid base64 characters)
        import re
        if not re.match(r'^[A-Za-z0-9+/]*={0,2}$', base64_data):
            logger.error(f"❌ Invalid base64 generated! First 100 chars: {base64_data[:100]}")
            raise ValueError("Generated invalid base64 string")
        
        logger.info(f"   Base64 length: {len(base64_data)} chars")
        logger.info(f"   Base64 preview: {base64_data[:50]}...")
        logger.info(f"   Valid base64: ✅")
        
        data_uri = f"data:image/png;base64,{base64_data}"
        return data_uri
    
    def generate_image_from_text(
        self,
        prompt_text: str,
        aspect_ratio: str = "16:9"
    ) -> Tuple[str, float]:
        """
        Generate an image from a simple text prompt (for shorts/timelapse)
        Returns: (data_uri, cost_in_usd)
        """
        try:
            logger.info(f"🎨 Generating image from text prompt")
            logger.debug(f"   Prompt: {prompt_text[:150]}...")
            logger.debug(f"   Aspect ratio: {aspect_ratio}")
            
            # Build generation config with aspect ratio
            generation_config = {
                "temperature": 1.0,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            
            # Map aspect ratio to Gemini's format
            aspect_ratio_map = {
                "1:1": "1:1",
                "16:9": "16:9",
                "9:16": "9:16",
                "4:3": "4:3",
                "3:4": "3:4"
            }
            
            gemini_aspect_ratio = aspect_ratio_map.get(aspect_ratio, "16:9")
            
            # Generate image
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    temperature=generation_config["temperature"],
                    top_p=generation_config["top_p"],
                    top_k=generation_config["top_k"],
                    imageConfig={
                        "aspectRatio": gemini_aspect_ratio
                    }
                )
            )
            
            # Check for safety blocks
            if hasattr(response, 'candidates') and response.candidates:
                finish_reason = getattr(response.candidates[0], 'finish_reason', None)
                if finish_reason in [3, 8]:  # SAFETY or RECITATION
                    error_msg = f"Image generation blocked by Gemini safety filters (reason: {finish_reason})"
                    logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg)
            
            # Extract image
            if not response.candidates or not response.candidates[0].content.parts:
                raise ValueError("No image generated by Gemini")
            
            image_part = None
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_part = part
                    break
            
            if not image_part:
                raise ValueError("No image data in response")
            
            image_data = image_part.inline_data.data
            logger.info(f"   ✅ Image generated: {len(image_data)} bytes")
            
            # Convert to data URI
            data_uri = self._encode_image_to_data_uri(image_data)
            
            # Calculate cost (estimate: ~$0.01 per image for Gemini 2.5 Flash Image)
            cost = 0.01
            
            logger.info(f"   💰 Image generation cost: ${cost:.4f}")
            
            return data_uri, cost
            
        except Exception as e:
            logger.error(f"❌ Error generating image from text: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
            raise


# Global singleton
image_service = ImageService() if os.getenv("GOOGLE_GEMINI_API_KEY") else None
