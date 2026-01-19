import os
import base64
import logging
import re
import google.generativeai as genai
from typing import Optional, Tuple
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
        
        genai.configure(api_key=api_key)
        # Using Gemini 2.5 Flash Image (Nano Banana) for fast image generation
        self.model_name = "gemini-2.5-flash-image"
    
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
            logger.info(f"🎨 Calling Gemini API...")
            logger.info(f"   Model: {self.model_name}")
            logger.info(f"   Prompt: {prompt_text[:100]}...")
            
            # Generate image using Gemini
            model = genai.GenerativeModel(self.model_name)
            
            # For Gemini image generation, we use text-to-image
            response = model.generate_content(
                prompt_text,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 2048,
                }
            )
            
            logger.info(f"   Response received from Gemini")
            
            # Extract image from response following official Nano Banana documentation
            # https://ai.google.dev/gemini-api/docs/image-generation
            if hasattr(response, 'candidates') and response.candidates:
                logger.info(f"   Checking {len(response.candidates)} candidate(s)...")
                
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part_idx, part in enumerate(candidate.content.parts):
                            # Check for text parts (optional, just for logging)
                            if hasattr(part, 'text') and part.text:
                                logger.info(f"   Part {part_idx}: Found text: {part.text[:100]}...")
                            
                            # Check for image in inline_data
                            if hasattr(part, 'inline_data') and part.inline_data:
                                mime_type = getattr(part.inline_data, 'mime_type', 'unknown')
                                logger.info(f"   Part {part_idx}: Found inline_data with mime_type: {mime_type}")
                                
                                if mime_type.startswith('image/'):
                                    logger.info(f"   ✅ Image found! Extracting...")
                                    
                                    # Get the image data
                                    image_data = part.inline_data.data
                                    logger.info(f"   Data type: {type(image_data)}")
                                    
                                    # Check if data is bytes or base64 string
                                    if isinstance(image_data, bytes):
                                        logger.info(f"   Data is bytes, length: {len(image_data)}")
                                        image_bytes = image_data
                                    elif isinstance(image_data, str):
                                        logger.info(f"   Data is base64 string, length: {len(image_data)}")
                                        # It's a base64 string, decode it
                                        image_bytes = base64.b64decode(image_data)
                                    else:
                                        logger.error(f"   ❌ Unexpected data type: {type(image_data)}")
                                        raise RuntimeError(f"Unexpected image data type: {type(image_data)}")
                                    
                                    # Verify we got valid PNG data
                                    if len(image_bytes) > 0:
                                        logger.info(f"   Image bytes length: {len(image_bytes)}")
                                        logger.info(f"   First 20 bytes: {image_bytes[:20]}")
                                        logger.info(f"   Starts with PNG header: {image_bytes[:8] == b'\\x89PNG\\r\\n\\x1a\\n'}")
                                    
                                    # Save first image for debugging
                                    if visual_prompt.scene_id:
                                        self._save_debug_image(image_bytes, visual_prompt.scene_id)
                                    
                                    # Calculate cost (approximate - based on model)
                                    cost = GEMINI_PRICING[self.model_name]["per_image"]
                                    tokens = 1290  # Approximate tokens for flash-image model
                                    
                                    logger.info(f"   💰 Cost: ${cost:.6f}")
                                    logger.info(f"   🎫 Tokens: ~{tokens}")
                                    
                                    data_uri = self._encode_image_to_data_uri(image_bytes)
                                    return data_uri, cost, tokens
            
            # If no image found, log error
            logger.error(f"   ❌ No image found in response")
            logger.error(f"   Response structure: candidates={hasattr(response, 'candidates')}")
            if hasattr(response, 'text'):
                logger.error(f"   Response text: {response.text[:200] if response.text else 'None'}")
            raise RuntimeError("No image generated in response - model may not support image generation")
            
        except Exception as e:
            logger.error(f"   ❌ Exception in image generation: {type(e).__name__}")
            logger.error(f"   Exception message: {str(e)}")
            raise RuntimeError(f"Image generation failed: {str(e)}")  # This will be caught by job_processor
    
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
                parts.append(
                    f"- {char.role}: {char.description}, "
                    f"expression: {char.expression}, pose: {char.pose}"
                )
        
        # Composition
        comp = visual_prompt.composition
        parts.append(f"\nCamera: {comp.camera_angle}")
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


# Global singleton
image_service = ImageService() if os.getenv("GOOGLE_GEMINI_API_KEY") else None
