import re
import asyncio
import logging
import traceback
from typing import List, Optional
from app.models import Job, JobStatus, Scene, ImageStatus, ScenePlan
from app.storage import store
from app.services.director_service import director_service
from app.services.cinematographer_service import cinematographer_service
from app.services.image_service import image_service

logger = logging.getLogger(__name__)


class JobProcessor:
    """Handles the complete job processing pipeline"""
    
    def __init__(self):
        self.store = store
        self.director = director_service
        self.cinematographer = cinematographer_service
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
            
            # Track start time
            from datetime import datetime
            job.started_at = datetime.utcnow()
            self.store.save_job(job)
            
            # Step 1: Split script into sentences
            logger.info(f"📝 Splitting script into sentences...")
            sentences = self._split_into_sentences(job.script_text)
            logger.info(f"   Found {len(sentences)} sentences")
            
            # Step 2: Generate scene plans (Director) and visual prompts (Cinematographer)
            logger.info(f"🎬 Director analyzing script...")
            job.status = JobStatus.ANALYZING_SCRIPT
            self.store.save_job(job)
            
            scenes = await self._generate_visual_prompts(job, sentences)
            logger.info(f"   ✅ Generated {len(scenes)} scene plans and visual prompts")
            
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
            
            # Mark as completed and calculate duration
            from datetime import datetime
            job.completed_at = datetime.utcnow()
            if job.started_at:
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            job.status = JobStatus.COMPLETED
            self.store.save_job(job)
            logger.info(f"✅ Job completed successfully: {job.id}")
            if job.duration_seconds:
                logger.info(f"⏱️  Duration: {job.duration_seconds:.1f}s")
            logger.info(f"💰 Total cost: ${job.cost.total_cost:.4f}")
            logger.info(f"   - Prompts: ${job.cost.prompt_generation_cost:.4f} ({job.cost.prompt_tokens_used} tokens)")
            logger.info(f"   - Images: ${job.cost.image_generation_cost:.4f} ({job.cost.num_images_generated} images)")
            
        except Exception as e:
            logger.error(f"❌ Job failed: {job.id}")
            logger.error(f"   Error: {str(e)}")
            
            # Track failure time
            from datetime import datetime
            job.completed_at = datetime.utcnow()
            if job.started_at:
                job.duration_seconds = (job.completed_at - job.started_at).total_seconds()
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            self.store.save_job(job)
            raise
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into scene-appropriate segments.
        
        Groups sentences to match typical speaking pace (5-6 seconds per scene).
        Average speaking rate: ~2.5 words/second, so target 12-15 words per scene.
        """
        # First, split into individual sentences
        raw_sentences = re.split(r'(?<=[.!?])\s+', text)
        raw_sentences = [s.strip() for s in raw_sentences if s.strip()]
        
        # Now group sentences into scenes based on word count
        scenes = []
        current_scene = []
        current_word_count = 0
        
        TARGET_WORDS_PER_SCENE = 12  # ~5 seconds at 2.5 words/sec (more scenes)
        MAX_WORDS_PER_SCENE = 20     # Max ~8 seconds
        MAX_SENTENCES_PER_SCENE = 2  # Don't combine too many sentences
        
        for sentence in raw_sentences:
            word_count = len(sentence.split())
            
            # If this sentence alone is long enough, make it its own scene
            if word_count >= TARGET_WORDS_PER_SCENE:
                # Save any accumulated sentences first
                if current_scene:
                    scenes.append(' '.join(current_scene))
                    current_scene = []
                    current_word_count = 0
                
                # Add the long sentence as its own scene
                scenes.append(sentence)
                continue
            
            # Check if adding this sentence would exceed limits
            would_exceed_words = (current_word_count + word_count) > MAX_WORDS_PER_SCENE
            would_exceed_count = len(current_scene) >= MAX_SENTENCES_PER_SCENE
            
            if current_scene and (would_exceed_words or would_exceed_count):
                # Save current scene and start new one
                scenes.append(' '.join(current_scene))
                current_scene = [sentence]
                current_word_count = word_count
            else:
                # Add to current scene
                current_scene.append(sentence)
                current_word_count += word_count
                
                # If we've reached target, save it
                if current_word_count >= TARGET_WORDS_PER_SCENE:
                    scenes.append(' '.join(current_scene))
                    current_scene = []
                    current_word_count = 0
        
        # Add any remaining sentences
        if current_scene:
            scenes.append(' '.join(current_scene))
        
        logger.info(f"   📊 Grouped {len(raw_sentences)} sentences into {len(scenes)} scenes")
        logger.info(f"   ⏱️  Estimated duration: ~{len(scenes) * 5.5:.0f} seconds")
        
        return scenes
    
    async def _generate_visual_prompts(self, job: Job, sentences: List[str]) -> List[Scene]:
        """
        🎬 DIRECTOR → CINEMATOGRAPHER PIPELINE
        Generate visual prompts using 2-step process
        """
        scenes = []
        previous_plan: Optional[ScenePlan] = None
        
        for index, sentence in enumerate(sentences):
            logger.info(f"   Scene {index + 1}/{len(sentences)}: {sentence[:50]}...")
            
            scene = Scene(
                job_id=job.id,
                index=index,
                sentence_text=sentence
            )
            
            # Step 1: 🎬 DIRECTOR - Analyze and plan the scene
            if self.director:
                try:
                    scene_plan, plan_cost, plan_tokens = self.director.generate_scene_plan(
                        scene_id=scene.id,
                        sentence=sentence,
                        previous_plan=previous_plan,
                        global_style=job.options.style_config
                    )
                    scene.scene_plan = scene_plan
                    previous_plan = scene_plan  # For next scene's context
                    
                    # Track director costs
                    job.cost.prompt_generation_cost += plan_cost
                    job.cost.prompt_tokens_used += plan_tokens
                    
                    logger.info(f"      🎬 Director: {scene_plan.narrative_role} | {scene_plan.emotional_tone}")
                    
                    # Step 2: 🎥 CINEMATOGRAPHER - Convert plan to visual prompt
                    if self.cinematographer:
                        try:
                            visual_prompt, prompt_cost, prompt_tokens = self.cinematographer.generate_visual_prompt(
                                scene_plan=scene_plan,
                                global_style=job.options.style_config
                            )
                            scene.visual_prompt = visual_prompt
                            
                            # Track cinematographer costs
                            job.cost.prompt_generation_cost += prompt_cost
                            job.cost.prompt_tokens_used += prompt_tokens
                            job.cost.num_prompts_generated += 1
                            job.cost.total_cost = job.cost.prompt_generation_cost + job.cost.image_generation_cost
                            
                            total_scene_cost = plan_cost + prompt_cost
                            total_scene_tokens = plan_tokens + prompt_tokens
                            
                            # Track scene-level cost for UI counter
                            scene.generation_cost = total_scene_cost
                            
                            logger.info(f"      🎥 Cinematographer: {visual_prompt.composition.camera.shot_type}")
                            logger.info(f"      ✅ Scene ready (${total_scene_cost:.6f}, {total_scene_tokens} tokens)")
                            
                        except Exception as e:
                            logger.error(f"      ❌ Cinematographer failed: {str(e)}")
                            import traceback
                            logger.error(f"      Full error traceback:")
                            for line in traceback.format_exc().split('\n'):
                                if line:
                                    logger.error(f"        {line}")
                            scene.last_error = f"Cinematographer failed: {str(e)}"
                    
                except Exception as e:
                    logger.error(f"      ❌ Director failed: {str(e)}")
                    scene.last_error = f"Director failed: {str(e)}"
            
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
                    
                    # Add image cost to scene's generation cost
                    scene.generation_cost += cost
                    
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
                
                # Track operation cost for UI counter
                scene.last_operation_cost = cost
                
                logger.info(f"✅ Scene image regenerated (${cost:.6f})")
                
                # Update job costs if possible
                job = self.store.get_job(scene.job_id)
                if job:
                    job.cost.image_generation_cost += cost
                    job.cost.image_tokens_used += tokens
                    job.cost.total_cost = job.cost.prompt_generation_cost + job.cost.image_generation_cost + job.cost.video_generation_cost
                    self.store.save_job(job)
            else:
                raise RuntimeError("Image service not available")
        except Exception as e:
            scene.image_status = ImageStatus.FAILED
            scene.last_error = f"Image generation failed: {str(e)}"
        
        self.store.save_scene(scene)
        return scene
    
    async def regenerate_scene_with_instruction(self, scene_id: str, instruction: str) -> Scene:
        """
        Regenerate scene with text instruction (e.g. "make character smile", "add laptop")
        This modifies the visual prompt based on the instruction, then generates a new image
        """
        scene = self.store.get_scene(scene_id)
        if not scene:
            raise ValueError(f"Scene not found: {scene_id}")
        
        if not scene.visual_prompt:
            raise ValueError("Scene has no visual prompt")
        
        logger.info(f"🎨 Regenerating scene with instruction: '{instruction}'")
        
        scene.image_status = ImageStatus.PENDING
        scene.last_error = None
        self.store.save_scene(scene)
        
        try:
            # Get the job for style config
            job = self.store.get_job(scene.job_id)
            if not job:
                raise ValueError("Job not found")
            
            # Use cinematographer to modify the visual prompt based on instruction
            if self.cinematographer and scene.scene_plan:
                logger.info(f"   🎬 Updating visual prompt with instruction...")
                
                # Create a modified scene plan with the instruction
                modified_plan = scene.scene_plan
                
                # Call cinematographer with instruction context
                visual_prompt, prompt_cost, prompt_tokens = self.cinematographer.generate_visual_prompt_with_instruction(
                    scene_plan=modified_plan,
                    global_style=job.options.style_config,
                    instruction=instruction
                )
                
                # Update scene with new prompt
                scene.visual_prompt = visual_prompt
                
                # Track costs
                job.cost.prompt_generation_cost += prompt_cost
                job.cost.prompt_tokens_used += prompt_tokens
                self.store.save_job(job)
                
                # Start tracking operation cost
                scene.last_operation_cost = prompt_cost
                
                logger.info(f"   ✅ Visual prompt updated")
            
            # Generate new image
            if self.image_gen:
                logger.info(f"   🖼️ Generating new image...")
                image_url, image_cost, tokens = self.image_gen.generate_image(scene.visual_prompt)
                scene.image_url = image_url
                scene.image_status = ImageStatus.GENERATED
                
                # Update costs
                job.cost.image_generation_cost += image_cost
                job.cost.image_tokens_used += tokens
                job.cost.total_cost = job.cost.prompt_generation_cost + job.cost.image_generation_cost + job.cost.video_generation_cost
                self.store.save_job(job)
                
                # Add image cost to operation cost for UI counter
                scene.last_operation_cost += image_cost
                
                logger.info(f"✅ Scene regenerated with instruction (prompt: ${scene.last_operation_cost - image_cost:.6f}, image: ${image_cost:.6f}, total: ${scene.last_operation_cost:.6f})")
            else:
                raise RuntimeError("Image service not available")
                
        except Exception as e:
            scene.image_status = ImageStatus.FAILED
            scene.last_error = f"Regeneration failed: {str(e)}"
            logger.error(f"❌ Regeneration with instruction failed: {str(e)}")
            logger.error(f"   Full Traceback:\n{traceback.format_exc()}")
        
        self.store.save_scene(scene)
        return scene


# Global singleton
job_processor = JobProcessor()
