import re
import asyncio
import logging
from typing import List
from app.models import Job, JobStatus, Scene, ImageStatus
from app.storage import store
from app.services.llm_service import llm_service
from app.services.image_service import image_service

logger = logging.getLogger(__name__)


class JobProcessor:
    """Handles the complete job processing pipeline"""
    
    def __init__(self):
        self.store = store
        self.llm = llm_service
        self.image_gen = image_service
    
    async def process_job(self, job: Job) -> None:
        """
        Process a job end-to-end:
        1. Split script into sentences
        2. Generate visual prompts for each sentence
        3. Optionally generate images
        """
        try:
            logger.info(f"🚀 Starting job processing: {job.id}")
            
            # Step 1: Split script into sentences
            logger.info(f"📝 Splitting script into sentences...")
            sentences = self._split_into_sentences(job.script_text)
            logger.info(f"   Found {len(sentences)} sentences")
            
            # Step 2: Generate visual prompts
            logger.info(f"🤖 Generating visual prompts using AI...")
            job.status = JobStatus.GENERATING_PROMPTS
            self.store.save_job(job)
            
            scenes = await self._generate_visual_prompts(job, sentences)
            logger.info(f"   ✅ Generated {len(scenes)} visual prompts")
            
            # Update job with scene IDs
            job.scene_ids = [scene.id for scene in scenes]
            self.store.save_job(job)
            
            # Step 3: Generate images if requested
            if job.options.generate_images:
                logger.info(f"🎨 Generating images using AI...")
                job.status = JobStatus.GENERATING_IMAGES
                self.store.save_job(job)
                
                await self._generate_images(scenes, job)
                logger.info(f"   ✅ Generated {job.cost.num_images_generated} images")
            else:
                logger.info(f"⏭️  Skipping image generation (disabled)")
            
            # Mark as completed
            job.status = JobStatus.COMPLETED
            self.store.save_job(job)
            logger.info(f"✅ Job completed successfully: {job.id}")
            logger.info(f"💰 Total cost: ${job.cost.total_cost:.4f}")
            logger.info(f"   - Prompts: ${job.cost.prompt_generation_cost:.4f} ({job.cost.prompt_tokens_used} tokens)")
            logger.info(f"   - Images: ${job.cost.image_generation_cost:.4f} ({job.cost.num_images_generated} images)")
            
        except Exception as e:
            logger.error(f"❌ Job failed: {job.id}")
            logger.error(f"   Error: {str(e)}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self.store.save_job(job)
            raise
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with NLTK/spaCy)
        # Split on periods, exclamation marks, and question marks followed by space
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    async def _generate_visual_prompts(self, job: Job, sentences: List[str]) -> List[Scene]:
        """Generate visual prompts for all sentences"""
        scenes = []
        
        for index, sentence in enumerate(sentences):
            logger.info(f"   Scene {index + 1}/{len(sentences)}: {sentence[:50]}...")
            
            scene = Scene(
                job_id=job.id,
                index=index,
                sentence_text=sentence
            )
            
            # Generate visual prompt using LLM
            if self.llm:
                try:
                    visual_prompt, cost, tokens = self.llm.generate_visual_prompt(
                        scene_id=scene.id,
                        sentence_text=sentence,
                        style_config=job.options.style_config
                    )
                    scene.visual_prompt = visual_prompt
                    
                    # Track costs
                    job.cost.prompt_generation_cost += cost
                    job.cost.prompt_tokens_used += tokens
                    job.cost.num_prompts_generated += 1
                    job.cost.total_cost = job.cost.prompt_generation_cost + job.cost.image_generation_cost
                    
                    logger.info(f"      ✅ Prompt generated (${cost:.6f}, {tokens} tokens)")
                except Exception as e:
                    logger.error(f"      ❌ Prompt failed: {str(e)}")
                    scene.last_error = f"Prompt generation failed: {str(e)}"
            
            # Save scene
            self.store.save_scene(scene)
            scenes.append(scene)
        
        return scenes
    
    async def _generate_images(self, scenes: List[Scene], job: Job) -> None:
        """Generate images for all scenes"""
        for idx, scene in enumerate(scenes):
            if not scene.visual_prompt:
                logger.warning(f"   Scene {idx + 1}: Skipping (no prompt)")
                continue
            
            logger.info(f"   Scene {idx + 1}/{len(scenes)}: Generating image...")
            
            scene.image_status = ImageStatus.PENDING
            self.store.save_scene(scene)
            
            try:
                if self.image_gen:
                    image_url, cost, tokens = self.image_gen.generate_image(scene.visual_prompt)
                    scene.image_url = image_url
                    scene.image_status = ImageStatus.GENERATED
                    
                    # Track costs
                    job.cost.image_generation_cost += cost
                    job.cost.image_tokens_used += tokens
                    job.cost.num_images_generated += 1
                    job.cost.total_cost = job.cost.prompt_generation_cost + job.cost.image_generation_cost
                    
                    logger.info(f"      ✅ Image generated (${cost:.6f}, ~{tokens} tokens)")
                else:
                    scene.image_status = ImageStatus.FAILED
                    scene.last_error = "Image service not available"
                    logger.error(f"      ❌ Image service not available")
            except Exception as e:
                scene.image_status = ImageStatus.FAILED
                scene.last_error = f"Image generation failed: {str(e)}"
                logger.error(f"      ❌ Image failed: {str(e)}")
            
            self.store.save_scene(scene)
    
    async def regenerate_scene_image(self, scene_id: str) -> Scene:
        """Regenerate image for a specific scene"""
        scene = self.store.get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene not found: {scene_id}")
        
        if not scene.visual_prompt:
            raise ValueError("Scene has no visual prompt")
        
        scene.image_status = ImageStatus.PENDING
        scene.last_error = None
        self.store.save_scene(scene)
        
        try:
            if self.image_gen:
                image_url, cost, tokens = self.image_gen.generate_image(scene.visual_prompt)
                scene.image_url = image_url
                scene.image_status = ImageStatus.GENERATED
                logger.info(f"✅ Scene image regenerated (${cost:.6f})")
                
                # Update job costs if possible
                job = self.store.get_job(scene.job_id)
                if job:
                    job.cost.image_generation_cost += cost
                    job.cost.image_tokens_used += tokens
                    job.cost.total_cost = job.cost.prompt_generation_cost + job.cost.image_generation_cost
                    self.store.save_job(job)
            else:
                raise RuntimeError("Image service not available")
        except Exception as e:
            scene.image_status = ImageStatus.FAILED
            scene.last_error = f"Image generation failed: {str(e)}"
        
        self.store.save_scene(scene)
        return scene


# Global singleton
job_processor = JobProcessor()
