import os
import logging
import base64
import httpx
from typing import Optional, Tuple
from google import genai
from google.genai import types
from app.models.scene import Scene

logger = logging.getLogger(__name__)

# Veo 3.1 pricing (as of January 2026)
# https://ai.google.dev/pricing
VEO_PRICING = {
    "veo-3.1-generate-preview": {
        "per_second": 0.025,  # $0.025 per second (8 seconds = $0.20)
        "duration": 8  # seconds
    },
    "veo-3.1-fast-generate-preview": {
        "per_second": 0.015,  # $0.015 per second (8 seconds = $0.12)
        "duration": 8  # seconds
    }
}


class VideoService:
    """Service for generating videos using Google Veo 3.1"""
    
    def __init__(self):
        api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_GEMINI_API_KEY environment variable is required")
        
        # Using Google Gen AI SDK for Veo 3.1
        # https://ai.google.dev/gemini-api/docs/video
        logger.info("🎬 Initializing Google Veo 3.1 SDK")
        os.environ["GOOGLE_API_KEY"] = api_key
        self.client = genai.Client()
        # Using Veo 3.1 Fast for speed (can switch to regular veo-3.1-generate-preview for higher quality)
        self.model_name = "veo-3.1-fast-generate-preview"
    
    def generate_video_from_scene(
        self, 
        scene: Scene, 
        custom_prompt: Optional[str] = None,
        aspect_ratio: str = "16:9"
    ) -> Tuple[str, float]:
        """
        Start video generation from a scene's image
        
        Args:
            scene: Scene with generated image
            custom_prompt: Optional custom prompt for video generation (defaults to sentence_text)
            aspect_ratio: "16:9" (landscape) or "9:16" (portrait)
            
        Returns:
            (operation_name, estimated_cost)
        """
        try:
            if not scene.image_url:
                raise ValueError(f"Scene {scene.id} has no generated image")
            
            # Use custom prompt or scene text
            prompt = custom_prompt if custom_prompt else scene.sentence_text
            
            logger.info(f"🎬 Starting Veo 3.1 video generation for scene {scene.id[:8]}...")
            logger.info(f"   Model: {self.model_name}")
            logger.info(f"   Aspect Ratio: {aspect_ratio}")
            logger.info(f"   Prompt: {prompt[:100]}...")
            
            # Extract image bytes from data URI
            image_bytes = self._extract_image_from_data_uri(scene.image_url)
            
            # Create proper Image object using SDK types
            logger.info(f"   📦 Preparing image for Veo API...")
            
            # Create Image using the types module
            image_obj = types.Image(
                image_bytes=image_bytes,
                mime_type="image/png"
            )
            logger.info(f"   ✅ Image prepared: {len(image_bytes)} bytes")
            
            # Generate video using Veo 3.1 with Image object
            # https://ai.google.dev/gemini-api/docs/video#generate-from-images
            operation = self.client.models.generate_videos(
                model=self.model_name,
                prompt=prompt,
                image=image_obj,  # Pass proper Image object
                config={
                    "aspectRatio": aspect_ratio,
                    # Can add more config options here:
                    # "duration": 8,  # seconds (default is 8)
                    # "resolution": "720p",  # or "1080p", "4k"
                }
            )
            
            # Calculate estimated cost
            pricing = VEO_PRICING[self.model_name]
            estimated_cost = pricing["per_second"] * pricing["duration"]
            
            logger.info(f"   ✅ Video generation started!")
            logger.info(f"   Operation: {operation.name}")
            logger.info(f"   💰 Estimated cost: ${estimated_cost:.4f}")
            logger.info(f"   ⏱️  Processing time: 11s - 6min")
            
            return operation.name, estimated_cost
            
        except Exception as e:
            logger.error(f"❌ Video generation failed: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            raise RuntimeError(f"Video generation failed: {str(e)}")
    
    def check_video_status(self, operation_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check status of video generation
        
        Args:
            operation_name: The operation name returned from generate_video_from_scene
            
        Returns:
            (is_done, video_url, error_message)
        """
        try:
            logger.info(f"📊 Checking video generation status: {operation_name[:50]}...")
            
            # Since we're checking from a different request (not in the same loop),
            # use the REST API directly instead of the SDK's operations.get()
            api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
            url = f"https://generativelanguage.googleapis.com/v1beta/{operation_name}"
            
            logger.info(f"   Making REST API call to: {url[:80]}...")
            response = httpx.get(
                url,
                headers={"x-goog-api-key": api_key}
            )
            response.raise_for_status()
            
            operation_data = response.json()
            logger.info(f"   Response received: {operation_data.get('done', False)}")
            
            # Check if operation is done
            is_done = operation_data.get('done', False)
            
            if not is_done:
                logger.info(f"   ⏳ Still processing...")
                return False, None, None
            
            # Check for errors
            if 'error' in operation_data:
                error_msg = operation_data['error'].get('message', str(operation_data['error']))
                logger.error(f"   ❌ Video generation failed: {error_msg}")
                return True, None, error_msg
            
            # Video is ready! Extract from REST response
            if 'response' in operation_data:
                logger.info(f"   Response available, extracting video...")
                response_data = operation_data['response']
                
                # The response structure from REST API:
                # response.generateVideoResponse.generatedSamples[0].video.uri
                if 'generateVideoResponse' in response_data:
                    generated_samples = response_data['generateVideoResponse'].get('generatedSamples', [])
                    
                    if generated_samples and len(generated_samples) > 0:
                        video_info = generated_samples[0].get('video', {})
                        video_uri = video_info.get('uri')
                        
                        if video_uri:
                            logger.info(f"   ✅ Video ready! Downloading from URI...")
                            logger.info(f"   Video URI: {video_uri[:80]}...")
                            
                            # Download the video from the URI
                            video_response = httpx.get(
                                video_uri,
                                headers={"x-goog-api-key": api_key},
                                follow_redirects=True
                            )
                            video_response.raise_for_status()
                            video_bytes = video_response.content
                            
                            # Convert to data URI for storage
                            video_data_uri = self._encode_video_to_data_uri(video_bytes)
                            
                            logger.info(f"   💾 Video downloaded ({len(video_bytes)} bytes)")
                            
                            return True, video_data_uri, None
            
            # Unexpected state
            logger.error(f"   ❌ Unexpected operation state")
            logger.error(f"   Operation data: {operation_data}")
            return True, None, "Unexpected operation state - no video generated"
            
        except Exception as e:
            logger.error(f"❌ Error checking video status: {type(e).__name__}")
            logger.error(f"   Message: {str(e)}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            return True, None, f"Error checking status: {str(e)}"
    
    def _extract_image_from_data_uri(self, data_uri: str) -> bytes:
        """Extract image bytes from data URI"""
        try:
            # Data URI format: data:image/png;base64,iVBORw0KG...
            if not data_uri.startswith('data:'):
                raise ValueError("Invalid data URI format")
            
            # Split on comma to get base64 data
            parts = data_uri.split(',', 1)
            if len(parts) != 2:
                raise ValueError("Invalid data URI format - no comma separator")
            
            base64_data = parts[1]
            image_bytes = base64.b64decode(base64_data)
            
            logger.info(f"   📷 Extracted image: {len(image_bytes)} bytes")
            return image_bytes
            
        except Exception as e:
            logger.error(f"   ❌ Failed to extract image from data URI: {e}")
            raise
    
    def _encode_video_to_data_uri(self, video_bytes: bytes) -> str:
        """Convert video bytes to data URI for storage"""
        if not isinstance(video_bytes, bytes):
            raise TypeError(f"Expected bytes, got {type(video_bytes)}")
        
        if len(video_bytes) == 0:
            raise ValueError("Video data is empty")
        
        # Encode to base64
        base64_data = base64.b64encode(video_bytes).decode('utf-8')
        
        # Create data URI (MP4 format from Veo)
        data_uri = f"data:video/mp4;base64,{base64_data}"
        
        logger.info(f"   📹 Encoded video to data URI: {len(base64_data)} chars")
        
        return data_uri


# Create singleton instance (optional, will be initialized when needed)
video_service = None

def get_video_service() -> VideoService:
    """Get or create video service instance"""
    global video_service
    if video_service is None:
        try:
            video_service = VideoService()
        except Exception as e:
            logger.warning(f"⚠️ Could not initialize video service: {e}")
            video_service = None
    return video_service
