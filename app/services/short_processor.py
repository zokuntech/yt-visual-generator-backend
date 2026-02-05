"""
Short Processor - Orchestrates the timelapse/transformation short generation workflow
"""
import logging
from typing import List, Optional
from app.models.short import (
    ShortProject,
    ShortCategory,
    ShortStatus,
    TransformationConcept,
    TransformationStage,
    TransitionVideo,
    StageType
)
from app.services.timelapse_director_service import TimelapseDirectorService
from app.services.image_service import ImageService
from app.services.video_service import VideoService
from app.storage import store

logger = logging.getLogger(__name__)


class ShortProcessor:
    """Orchestrates the short generation pipeline"""
    
    def __init__(self):
        self.timelapse_director = TimelapseDirectorService()
        self.image_service = ImageService()
        self.video_service = VideoService()
    
    async def generate_concepts(
        self,
        category: ShortCategory,
        num_concepts: int = 10
    ) -> tuple[List[TransformationConcept], float]:
        """
        Step 1: Generate transformation concept ideas
        Returns: (concepts, cost)
        """
        try:
            logger.info(f"🎬 Starting concept generation for {category}")
            
            concepts, cost, tokens = self.timelapse_director.generate_concepts(
                category=category,
                num_concepts=num_concepts
            )
            
            logger.info(f"✅ Generated {len(concepts)} concepts")
            logger.info(f"   💰 Cost: ${cost:.4f}, Tokens: {tokens}")
            
            return concepts, cost
            
        except Exception as e:
            logger.error(f"❌ Error in concept generation: {e}")
            raise
    
    async def create_short_project(
        self,
        category: ShortCategory,
        concept: TransformationConcept,
        aspect_ratio: str = "9:16"
    ) -> ShortProject:
        """
        Step 2: Create a short project from a selected concept
        Generates stage and transition prompts
        Returns: ShortProject (with prompts, no images/videos yet)
        """
        try:
            logger.info(f"🎨 Creating short project: {concept.title}")
            
            # Create the project
            project = ShortProject(
                category=category,
                selected_concept=concept,
                room_type=concept.title,
                transformation_description=concept.description,
                aspect_ratio=aspect_ratio,
                status=ShortStatus.GENERATING_STAGES
            )
            
            # Generate stage prompts
            logger.info(f"   📝 Generating stage prompts...")
            stages, stage_cost, stage_tokens = self.timelapse_director.generate_stage_prompts(
                concept=concept,
                aspect_ratio=aspect_ratio
            )
            project.stages = stages
            project.prompt_generation_cost += stage_cost
            logger.info(f"   ✅ Generated {len(stages)} stage prompts (${stage_cost:.4f})")
            
            # Generate transition prompts
            logger.info(f"   📝 Generating transition prompts...")
            transitions, trans_cost, trans_tokens = self.timelapse_director.generate_transition_prompts(
                concept=concept,
                stages=stages
            )
            project.transitions = transitions
            project.prompt_generation_cost += trans_cost
            logger.info(f"   ✅ Generated {len(transitions)} transition prompts (${trans_cost:.4f})")
            
            # Update project
            project.total_cost = project.prompt_generation_cost
            project.status = ShortStatus.AWAITING_SELECTION
            project.current_step = "Prompts generated. Ready to generate images."
            project.progress_percentage = 30
            
            # Save project
            store.save_short(project)
            
            logger.info(f"✅ Short project created: {project.id[:8]}")
            logger.info(f"   💰 Total cost so far: ${project.total_cost:.4f}")
            
            return project
            
        except Exception as e:
            logger.error(f"❌ Error creating short project: {e}")
            raise
    
    async def generate_stage_images(self, project_id: str) -> ShortProject:
        """
        Step 3: Generate images for all 4 stages
        """
        try:
            project = store.get_short(project_id)
            if not project:
                raise ValueError(f"Short project {project_id} not found")
            
            logger.info(f"🖼️  Generating images for project: {project.room_type}")
            project.status = ShortStatus.GENERATING_IMAGES
            project.current_step = "Generating stage images..."
            store.save_short(project)
            
            total_image_cost = 0.0
            
            for i, stage in enumerate(project.stages):
                logger.info(f"   📸 Stage {stage.stage_number}/{len(project.stages)}: {stage.stage_type.value}")
                
                try:
                    # Create a minimal VisualPrompt-like structure for the image service
                    # The image service expects a prompt with style and setting
                    from app.models.scene import StyleConfig
                    from app.models.job import StyleConfig as JobStyleConfig
                    
                    # Build a prompt structure
                    style_config = StyleConfig(
                        art_style="8K_cinematic_photorealistic",
                        lighting="professional_architectural_lighting",
                        color_palette="realistic_natural",
                        background=f"construction_timelapse_{stage.stage_type.value}",
                        aspect_ratio=project.aspect_ratio
                    )
                    
                    # For now, use the detailed_description directly as the prompt
                    # The image service can handle raw text prompts
                    image_data, cost = self.image_service.generate_image_from_text(
                        prompt_text=stage.detailed_description,
                        aspect_ratio=project.aspect_ratio
                    )
                    
                    stage.image_url = image_data
                    stage.image_status = "generated"
                    stage.image_generation_cost = cost
                    total_image_cost += cost
                    
                    logger.info(f"      ✅ Image generated (${cost:.4f})")
                    
                except Exception as e:
                    logger.error(f"      ❌ Failed to generate image: {e}")
                    stage.image_status = "failed"
                    stage.image_url = None
                
                # Update progress
                project.progress_percentage = 30 + int((i + 1) / len(project.stages) * 40)
                store.save_short(project)
            
            # Update project costs
            project.image_generation_cost = total_image_cost
            project.total_cost = (
                project.prompt_generation_cost +
                project.image_generation_cost
            )
            
            # Check if all images generated successfully
            all_success = all(stage.image_status == "generated" for stage in project.stages)
            
            if all_success:
                project.status = ShortStatus.COMPLETED
                project.current_step = "All stage images generated. Ready to animate transitions."
                project.progress_percentage = 70
                logger.info(f"✅ All stage images generated successfully")
            else:
                project.status = ShortStatus.FAILED
                project.last_error = "Some stage images failed to generate"
                logger.warning(f"⚠️  Some images failed to generate")
            
            project.total_cost = (
                project.prompt_generation_cost +
                project.image_generation_cost
            )
            store.save_short(project)
            
            logger.info(f"💰 Total cost: ${project.total_cost:.4f}")
            
            return project
            
        except Exception as e:
            logger.error(f"❌ Error generating stage images: {e}")
            project = store.get_short(project_id)
            if project:
                project.status = ShortStatus.FAILED
                project.last_error = str(e)
                store.save_short(project)
            raise
    
    async def animate_transitions(self, project_id: str) -> ShortProject:
        """
        Step 4: Generate transition videos between stages
        """
        try:
            project = store.get_short(project_id)
            if not project:
                raise ValueError(f"Short project {project_id} not found")
            
            logger.info(f"🎥 Animating transitions for project: {project.room_type}")
            project.status = ShortStatus.GENERATING_VIDEOS
            project.current_step = "Generating transition videos..."
            store.save_short(project)
            
            # Map stage types to their images
            stage_images = {
                stage.stage_type: stage.image_url
                for stage in project.stages
                if stage.image_url
            }
            
            for i, transition in enumerate(project.transitions):
                logger.info(f"   🎬 Transition {transition.transition_number}/{len(project.transitions)}: {transition.from_stage.value} → {transition.to_stage.value}")
                
                try:
                    # Get the starting frame image
                    from_image = stage_images.get(transition.from_stage)
                    if not from_image:
                        logger.error(f"      ❌ Missing image for stage {transition.from_stage.value}")
                        transition.video_status = "failed"
                        continue
                    
                    # Start video generation
                    operation_name, cost = await self.video_service.generate_video_from_image(
                        image_data=from_image,
                        prompt=transition.motion_description,
                        aspect_ratio=project.aspect_ratio,
                        duration_seconds=transition.duration_seconds
                    )
                    
                    transition.video_operation_name = operation_name
                    transition.video_status = "processing"
                    transition.video_generation_cost = cost
                    
                    logger.info(f"      ⏳ Video generation started (operation: {operation_name[:20]}...)")
                    
                except Exception as e:
                    logger.error(f"      ❌ Failed to start video generation: {e}")
                    transition.video_status = "failed"
                
                # Update progress
                project.progress_percentage = 70 + int((i + 1) / len(project.transitions) * 30)
                store.save_short(project)
            
            project.current_step = "Transition videos processing. Poll for completion."
            store.save_short(project)
            
            logger.info(f"✅ All transitions initiated")
            
            return project
            
        except Exception as e:
            logger.error(f"❌ Error animating transitions: {e}")
            project = store.get_short(project_id)
            if project:
                project.status = ShortStatus.FAILED
                project.last_error = str(e)
                store.save_short(project)
            raise
    
    async def check_transition_status(self, project_id: str, transition_number: int) -> ShortProject:
        """
        Poll the status of a specific transition video
        """
        try:
            project = store.get_short(project_id)
            if not project:
                raise ValueError(f"Short project {project_id} not found")
            
            # Find the transition
            transition = next(
                (t for t in project.transitions if t.transition_number == transition_number),
                None
            )
            
            if not transition:
                raise ValueError(f"Transition {transition_number} not found")
            
            if not transition.video_operation_name:
                return project
            
            # Check status
            is_done, video_url, error = self.video_service.check_video_status(
                transition.video_operation_name
            )
            
            if is_done:
                if error:
                    transition.video_status = "failed"
                    logger.error(f"❌ Transition {transition_number} failed: {error}")
                elif video_url:
                    transition.video_url = video_url
                    transition.video_status = "generated"
                    project.video_generation_cost += transition.video_generation_cost
                    project.total_cost = (
                        project.prompt_generation_cost +
                        project.image_generation_cost +
                        project.video_generation_cost
                    )
                    logger.info(f"✅ Transition {transition_number} completed")
            
            # Check if all transitions are done
            all_done = all(
                t.video_status in ["generated", "failed"]
                for t in project.transitions
            )
            
            if all_done:
                all_success = all(t.video_status == "generated" for t in project.transitions)
                if all_success:
                    project.status = ShortStatus.COMPLETED
                    project.current_step = "All transitions complete!"
                    project.progress_percentage = 100
                else:
                    project.status = ShortStatus.FAILED
                    project.last_error = "Some transitions failed to generate"
            
            store.save_short(project)
            return project
            
        except Exception as e:
            logger.error(f"❌ Error checking transition status: {e}")
            raise
    
    async def regenerate_stage_image(
        self,
        project_id: str,
        stage_number: int
    ) -> ShortProject:
        """
        Regenerate a specific stage image with the same prompt
        """
        try:
            project = store.get_short(project_id)
            if not project:
                raise ValueError(f"Short project {project_id} not found")
            
            # Find the stage
            stage = next(
                (s for s in project.stages if s.stage_number == stage_number),
                None
            )
            
            if not stage:
                raise ValueError(f"Stage {stage_number} not found")
            
            logger.info(f"🔄 Regenerating stage {stage_number}: {stage.stage_type.value}")
            
            # Regenerate image
            image_data, cost = self.image_service.generate_image_from_text(
                prompt_text=stage.detailed_description,
                aspect_ratio=project.aspect_ratio
            )
            
            stage.image_url = image_data
            stage.image_status = "generated"
            stage.image_generation_cost = cost
            
            # Update project costs
            project.image_generation_cost += cost
            project.total_cost = (
                project.prompt_generation_cost +
                project.image_generation_cost +
                project.video_generation_cost
            )
            
            store.save_short(project)
            
            logger.info(f"✅ Stage {stage_number} regenerated (${cost:.4f})")
            
            return project
            
        except Exception as e:
            logger.error(f"❌ Error regenerating stage: {e}")
            raise
    
    async def edit_stage_with_instruction(
        self,
        project_id: str,
        stage_number: int,
        instruction: str
    ) -> ShortProject:
        """
        Edit a stage image using a text instruction
        """
        try:
            project = store.get_short(project_id)
            if not project:
                raise ValueError(f"Short project {project_id} not found")
            
            # Find the stage
            stage = next(
                (s for s in project.stages if s.stage_number == stage_number),
                None
            )
            
            if not stage:
                raise ValueError(f"Stage {stage_number} not found")
            
            logger.info(f"✏️  Editing stage {stage_number} with instruction: {instruction[:50]}...")
            
            # Build modified prompt
            modified_prompt = f"""{stage.detailed_description}

MODIFICATIONS REQUESTED:
{instruction}

Apply these modifications while maintaining the overall scene context, camera angle, and visual quality standards."""
            
            # Generate new image with modified prompt
            image_data, cost = self.image_service.generate_image_from_text(
                prompt_text=modified_prompt,
                aspect_ratio=project.aspect_ratio
            )
            
            stage.image_url = image_data
            stage.image_status = "generated"
            stage.image_generation_cost += cost
            
            # Update the detailed description to include the modification
            stage.detailed_description = modified_prompt
            
            # Update project costs
            project.image_generation_cost += cost
            project.total_cost = (
                project.prompt_generation_cost +
                project.image_generation_cost +
                project.video_generation_cost
            )
            
            store.save_short(project)
            
            logger.info(f"✅ Stage {stage_number} edited (${cost:.4f})")
            
            return project
            
        except Exception as e:
            logger.error(f"❌ Error editing stage: {e}")
            raise
