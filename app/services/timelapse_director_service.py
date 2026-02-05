"""
Timelapse Director Service - Generates transformation shorts (epoxy, construction, etc.)
Handles visual-only content with no narration
"""
import json
import os
import logging
from typing import List, Tuple
from openai import OpenAI
from app.models.short import (
    TransformationConcept, 
    ShortCategory,
    TransformationStage,
    TransitionVideo,
    StageType
)

logger = logging.getLogger(__name__)

# OpenAI pricing
OPENAI_PRICING = {
    "gpt-4o": {
        "input": 2.50 / 1_000_000,
        "output": 10.00 / 1_000_000,
    },
    "gpt-4o-mini": {
        "input": 0.150 / 1_000_000,
        "output": 0.600 / 1_000_000,
    }
}


class TimelapseDirectorService:
    """
    The Timelapse Director - Creates visual-only transformation content
    (epoxy flooring, construction, crafting, etc.)
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Using the more powerful model for detailed prompts
    
    def generate_concepts(
        self,
        category: ShortCategory,
        num_concepts: int = 10
    ) -> Tuple[List[TransformationConcept], float, int]:
        """
        STEP 1: Generate transformation concept ideas
        Returns: (concepts, cost, tokens)
        """
        
        system_prompt = self._build_concept_generation_prompt(category)
        
        try:
            logger.info(f"🎬 Generating {num_concepts} concepts for {category}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate exactly {num_concepts} transformation concepts."}
                ],
                response_format={"type": "json_object"},
                temperature=0.8,  # Higher creativity for diverse ideas
            )
            
            # Calculate cost
            usage = response.usage
            input_cost = usage.prompt_tokens * OPENAI_PRICING[self.model]["input"]
            output_cost = usage.completion_tokens * OPENAI_PRICING[self.model]["output"]
            total_cost = input_cost + output_cost
            total_tokens = usage.total_tokens
            
            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Convert to TransformationConcept objects
            concepts = []
            for item in data.get("concepts", []):
                concepts.append(TransformationConcept(
                    index=item["index"],
                    title=item["title"],
                    description=item["description"],
                    category=category
                ))
            
            logger.info(f"✅ Generated {len(concepts)} concepts, cost: ${total_cost:.4f}")
            return concepts, total_cost, total_tokens
            
        except Exception as e:
            logger.error(f"❌ Error generating concepts: {e}")
            raise
    
    def generate_stage_prompts(
        self,
        concept: TransformationConcept,
        aspect_ratio: str = "9:16"
    ) -> Tuple[List[TransformationStage], float, int]:
        """
        STEP 2: Generate detailed image prompts for each stage
        Returns: (stages, cost, tokens)
        """
        
        system_prompt = self._build_stage_generation_prompt(concept, aspect_ratio)
        
        try:
            logger.info(f"🎨 Generating 6-stage prompts for: {concept.title}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate the 6 transformation stages for: {concept.title}\n\n{concept.description}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,  # Balanced for detailed, consistent output
            )
            
            # Calculate cost
            usage = response.usage
            input_cost = usage.prompt_tokens * OPENAI_PRICING[self.model]["input"]
            output_cost = usage.completion_tokens * OPENAI_PRICING[self.model]["output"]
            total_cost = input_cost + output_cost
            total_tokens = usage.total_tokens
            
            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Convert to TransformationStage objects
            stages = []
            for stage_data in data.get("stages", []):
                stages.append(TransformationStage(
                    stage_type=StageType(stage_data["stage_type"]),
                    stage_number=stage_data["stage_number"],
                    detailed_description=stage_data["detailed_description"],
                    required_elements=stage_data.get("required_elements", []),
                    workers_present=stage_data.get("workers_present", False),
                    worker_count=stage_data.get("worker_count")
                ))
            
            logger.info(f"✅ Generated {len(stages)} stage prompts, cost: ${total_cost:.4f}")
            return stages, total_cost, total_tokens
            
        except Exception as e:
            logger.error(f"❌ Error generating stage prompts: {e}")
            raise
    
    def generate_transition_prompts(
        self,
        concept: TransformationConcept,
        stages: List[TransformationStage]
    ) -> Tuple[List[TransitionVideo], float, int]:
        """
        STEP 3: Generate video transition prompts (stage-to-stage animations)
        Returns: (transitions, cost, tokens)
        """
        
        system_prompt = self._build_transition_generation_prompt(concept, stages)
        
        # Build detailed context with stage descriptions for consistency
        stages_context = "\n\n".join([
            f"STAGE {s.stage_number} ({s.stage_type.value}):\n{s.detailed_description[:300]}..."
            for s in stages
        ])
        
        try:
            logger.info(f"🎥 Generating 5 transition prompts for: {concept.title}")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate the 5 transition video prompts that maintain visual consistency.\n\nSTAGE DESCRIPTIONS (for context):\n{stages_context}\n\nEnsure each transition explicitly references the starting and ending visual states."}
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
            
            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Convert to TransitionVideo objects
            transitions = []
            for trans_data in data.get("transitions", []):
                transitions.append(TransitionVideo(
                    from_stage=StageType(trans_data["from_stage"]),
                    to_stage=StageType(trans_data["to_stage"]),
                    transition_number=trans_data["transition_number"],
                    motion_description=trans_data["motion_description"],
                    duration_seconds=trans_data.get("duration_seconds", 8)
                ))
            
            logger.info(f"✅ Generated {len(transitions)} transition prompts, cost: ${total_cost:.4f}")
            return transitions, total_cost, total_tokens
            
        except Exception as e:
            logger.error(f"❌ Error generating transition prompts: {e}")
            raise
    
    def _build_concept_generation_prompt(self, category: ShortCategory) -> str:
        """Build the system prompt for concept generation"""
        
        category_context = {
            ShortCategory.EPOXY_FLOORING: """
Focus on: Interior spaces ideal for artistic epoxy flooring installations
Examples: Kitchens, garages, basements, showrooms, retail spaces, home gyms
Emphasis: Luxury transformation, premium finishes, satisfying visual reveals
""",
            ShortCategory.FURNITURE_BUILD: """
Focus on: Furniture construction from raw materials to finished pieces
Examples: Tables, chairs, shelving, desks, beds, storage units
Emphasis: Woodworking, assembly process, satisfying completion
""",
            ShortCategory.ROOM_RENOVATION: """
Focus on: Complete room transformations
Examples: Bedrooms, bathrooms, living rooms, offices, studios
Emphasis: Dramatic before/after, construction process, design reveal
""",
            ShortCategory.WOODWORKING: """
Focus on: Wood crafting and finishing processes
Examples: Cutting, sanding, staining, assembly, fine details
Emphasis: Craftsmanship, satisfying textures, wood transformation
""",
            ShortCategory.CUSTOM: """
Focus on: Any satisfying transformation or build process
Examples: Varied creative projects with visual appeal
Emphasis: Unique, engaging, satisfying progression
"""
        }
        
        context = category_context.get(category, category_context[ShortCategory.CUSTOM])
        
        return f"""You are an expert Transformation Content Creator specializing in viral YouTube Shorts.

CATEGORY: {category.value}

{context}

Your task: Generate exactly 10 unique transformation concepts perfect for timelapse shorts.

REQUIREMENTS:
✅ Each concept must be visually dramatic and satisfying
✅ Clear before/after potential
✅ Realistic to execute (can be visualized authentically)
✅ Appealing to YouTube Shorts audience (vertical video, 15-60 seconds)
✅ Varied locations and contexts (no repetition)

OUTPUT JSON FORMAT:
{{
  "concepts": [
    {{
      "index": 1,
      "title": "Concept title (short, catchy)",
      "description": "2-3 sentences describing the space, transformation, and why it's visually compelling"
    }},
    ...10 total
  ]
}}

IMPORTANT: Be specific, creative, and focus on visual drama!
"""
    
    def _build_stage_generation_prompt(self, concept: TransformationConcept, aspect_ratio: str) -> str:
        """Build the system prompt for generating the 4 transformation stages"""
        
        # Load the full detailed prompt based on category
        if concept.category == ShortCategory.EPOXY_FLOORING:
            stage_instructions = self._get_epoxy_stage_instructions()
        else:
            stage_instructions = self._get_generic_stage_instructions(concept.category)
        
        return f"""You are an expert Architectural Visualizer and AI Prompt Engineer.

SELECTED CONCEPT:
Title: {concept.title}
Description: {concept.description}
Category: {concept.category.value}
Aspect Ratio: {aspect_ratio}

YOUR MISSION:
Generate 6 highly detailed image generation prompts for each transformation stage.

🔒 FIRST: Establish the "ROOM ANCHOR" - These elements MUST be identical in all 6 stages:
- Camera Position: (e.g., "wide angle from doorway, 5 feet high, capturing entire room")
- Room Dimensions: (e.g., "20x15 foot rectangular space")
- Architectural Features: (e.g., "large window left wall, exposed brick right wall, high ceiling")
- Lighting Setup: (e.g., "natural daylight from left window, overhead construction lights")

Then for each stage, start the description with:
"CAMERA & ROOM (constant across all stages): [Your established anchor]
STAGE-SPECIFIC CHANGES: [What's different in this stage]"

{stage_instructions}

OUTPUT JSON FORMAT:
{{
  "stages": [
    {{
      "stage_type": "empty_room",
      "stage_number": 1,
      "detailed_description": "Complete image generation prompt with all visual details, lighting, textures, atmosphere, camera angle, etc. MINIMUM 200 words.",
      "required_elements": ["bare_floor", "construction_debris", "raw_space"],
      "workers_present": false,
      "worker_count": 0
    }},
    {{
      "stage_type": "prep_work",
      "stage_number": 2,
      "detailed_description": "...",
      "required_elements": ["2-3 workers", "safety gear", "prep tools", "grinding machines"],
      "workers_present": true,
      "worker_count": 2 or 3
    }},
    {{
      "stage_type": "active_installation",
      "stage_number": 3,
      "detailed_description": "...",
      "required_elements": ["3-4 workers", "pouring epoxy/main work", "collaborative action", "key moment"],
      "workers_present": true,
      "worker_count": 3 or 4
    }},
    {{
      "stage_type": "finishing_touches",
      "stage_number": 4,
      "detailed_description": "...",
      "required_elements": ["2-3 workers", "detail work", "cleanup", "final touches"],
      "workers_present": true,
      "worker_count": 2 or 3
    }},
    {{
      "stage_type": "completed_empty",
      "stage_number": 5,
      "detailed_description": "...",
      "required_elements": ["finished_surface", "pristine_space", "showcase_quality"],
      "workers_present": false,
      "worker_count": 0 or 1
    }},
    {{
      "stage_type": "fully_furnished",
      "stage_number": 6,
      "detailed_description": "...",
      "required_elements": ["furniture", "decor", "lived_in", "complete"],
      "workers_present": false,
      "worker_count": 0
    }}
  ]
}}

CRITICAL CONSISTENCY REQUIREMENTS:
- **IDENTICAL CAMERA ANGLE**: Wide angle, static position, eye-level or slightly above
- **IDENTICAL ROOM LAYOUT**: Same walls, same windows, same architectural features, same dimensions
- **IDENTICAL LIGHTING SETUP**: Same light source positions (windows, fixtures)
- **ONLY THE WORK PROGRESSES**: People, materials, and completion state change - NOTHING ELSE
- Stages 2, 3, 4 MUST have workers prominently visible and actively working
- Stage 3 is the hero shot with most workers (3-4 people)
- Ultra-detailed descriptions (200+ words each)
- Photorealistic, cinema-quality specifications

📐 CONSISTENCY CHECKLIST FOR EVERY STAGE:
✅ Describe the EXACT camera position (e.g., "from the doorway, wide angle view capturing the entire room")
✅ Reference the SAME room features (e.g., "window on the left wall, exposed brick on the right")
✅ Maintain the SAME perspective and framing
✅ Keep the SAME lighting direction (e.g., "natural light from left window")
✅ ONLY change: people, tools, materials, floor condition, completion state
"""
    
    def _build_transition_generation_prompt(
        self,
        concept: TransformationConcept,
        stages: List[TransformationStage]
    ) -> str:
        """Build the system prompt for generating transition video prompts"""
        
        stages_summary = "\n".join([
            f"Stage {s.stage_number} ({s.stage_type.value}): {s.detailed_description[:150]}..."
            for s in stages
        ])
        
        return f"""You are an expert Timelapse Director specializing in construction and transformation videos.

CONCEPT: {concept.title}
CATEGORY: {concept.category.value}

STAGES OVERVIEW:
{stages_summary}

YOUR MISSION:
Generate 5 detailed video transition prompts (Frame-to-Video workflow).

Each transition shows the timelapse progression from one stage to the next.

TRANSITION 1: Stage 1 (Empty) → Stage 2 (Prep Work)
Duration: 5-7 seconds
Focus: Workers entering with equipment, setting up, beginning prep work, tools appearing

TRANSITION 2: Stage 2 (Prep Work) → Stage 3 (Active Installation)
Duration: 7-9 seconds
Focus: More workers arriving, main work beginning, key moment starting (e.g., epoxy pouring begins)

TRANSITION 3: Stage 3 (Active Installation) → Stage 4 (Finishing Touches)
Duration: 8-10 seconds (HERO TRANSITION - longest, most dramatic)
Focus: Main installation completing, transition from active pouring/building to detail work, workers shifting tasks

TRANSITION 4: Stage 4 (Finishing Touches) → Stage 5 (Completed Empty)
Duration: 6-8 seconds
Focus: Final touches completing, workers cleaning up and exiting, reveal of finished work

TRANSITION 5: Stage 5 (Completed) → Stage 6 (Furnished)
Duration: 5-7 seconds
Focus: Furniture appearing, decoration, styling, final transformation reveal

OUTPUT JSON FORMAT:
{{
  "transitions": [
    {{
      "from_stage": "empty_room",
      "to_stage": "prep_work",
      "transition_number": 1,
      "duration_seconds": 6,
      "motion_description": "Detailed description of all motion, camera behavior (static), worker movements, material changes, environmental progression. MINIMUM 150 words describing every visual change."
    }},
    {{
      "from_stage": "prep_work",
      "to_stage": "active_installation",
      "transition_number": 2,
      "duration_seconds": 8,
      "motion_description": "..."
    }},
    {{
      "from_stage": "active_installation",
      "to_stage": "finishing_touches",
      "transition_number": 3,
      "duration_seconds": 9,
      "motion_description": "..."
    }},
    {{
      "from_stage": "finishing_touches",
      "to_stage": "completed_empty",
      "transition_number": 4,
      "duration_seconds": 7,
      "motion_description": "..."
    }},
    {{
      "from_stage": "completed_empty",
      "to_stage": "fully_furnished",
      "transition_number": 5,
      "duration_seconds": 6,
      "motion_description": "..."
    }}
  ]
}}

REQUIREMENTS:
✅ Static camera angle (authentic timelapse) - NEVER moves
✅ Natural, realistic physics and motion
✅ Workers move authentically (not robotic)
✅ Satisfying visual progression
✅ Smooth timelapse pacing
✅ No camera movement, no panning, no zooming

🎯 CONSISTENCY & CONTINUITY REQUIREMENTS:
✅ **START with the exact ending state of the previous stage**
✅ **END with the exact starting state of the next stage**
✅ Explicitly reference: same camera angle, same room layout, same lighting
✅ Describe what changes (people arriving/leaving, materials appearing, work progressing)
✅ Describe what stays the same (walls, windows, perspective, framing)
✅ Include specific visual markers (e.g., "the window on the left remains visible throughout")

PROMPT STRUCTURE:
1. Opening: Describe the starting frame (Stage X's final state)
2. Middle: Describe the transformation/progression
3. Ending: Describe the ending frame (Stage Y's starting state)
4. Throughout: Emphasize what stays constant (camera, room, lighting)

EXAMPLE:
"The scene opens from a wide-angle static camera position at the doorway, showing the entire room. 
The concrete floor is bare and dusty, with the window on the left wall casting natural light across the space.
As the timelapse begins, from the edges of the frame, 2-3 construction workers enter carrying grinding equipment...
The camera never moves, maintaining the same perspective as workers prepare the floor.
The scene ends with the same camera angle, now showing 2-3 workers actively grinding the floor, dust visible in the air..."
"""
    
    def _get_epoxy_stage_instructions(self) -> str:
        """Detailed instructions for epoxy flooring stages"""
        return """
STAGE 1: EMPTY / BEFORE
- Bare concrete floor (matte, dusty, unpolished, visible cracks)
- Exposed walls or unfinished surfaces, construction debris
- Raw industrial feel, harsh natural lighting
- Empty space, NO people visible
- Full of potential, waiting to be transformed

STAGE 2: PREP WORK (2-3 WORKERS VISIBLE)
- 2-3 construction workers in full safety gear (hard hats, high-vis vests, boots, gloves)
- Workers grinding concrete floor, preparing surface
- Dust in air, grinding machines, measuring tools visible
- Workers actively measuring, marking, preparing
- Equipment: grinders, vacuum, cleaning supplies, tape measures
- Partially prepped floor, some areas clean, some dusty
- Dynamic, focused atmosphere

STAGE 3: ACTIVE INSTALLATION (3-4 WORKERS - KEY MOMENT!)
- 3-4 workers actively pouring and spreading metallic epoxy
- **MAIN FOCUS**: Workers pouring liquid epoxy from buckets
- One worker pouring, another spreading with squeegee, others preparing next pour
- Visible liquid epoxy with metallic pigments swirling
- Colors: Silver, charcoal, deep blue, warm gold in wet epoxy
- Workers using specialized tools (spiked rollers, trowels, squeegees)
- Partially wet floor with glossy liquid pools
- Most energetic, collaborative scene

STAGE 4: FINISHING TOUCHES (2-3 WORKERS)
- 2-3 workers applying final touches, sealing, smoothing
- Epoxy mostly cured, becoming glossier
- Workers carefully inspecting, touching up edges
- Some areas ultra-glossy, others still being finished
- Workers cleaning up equipment, removing tape
- Transitioning from work site to completed project
- Calmer, detailed work atmosphere

STAGE 5: COMPLETED EMPTY (1 WORKER OR EMPTY)
- **PRIMARY FOCUS**: Premium artistic metallic epoxy flooring
- Flowing organic marble-style patterns with metallic pigments
- Colors: Silver, charcoal, deep blue, warm gold tones swirling and set
- Ultra-high-gloss mirror finish with perfect reflections
- Glass-smooth surface with visible depth
- Maybe 1 worker doing final walkthrough or completely empty
- Walls finished, room spotless, no furniture yet
- Professional lighting showcasing the floor masterpiece

STAGE 6: FULLY FURNISHED
- Appropriate furniture for the space
- High-end interior design, cohesive style
- Epoxy floor still clearly visible and reflective beneath furniture
- Warm ambient lighting, lived-in luxury feel
- Complete transformation success, "after" reveal

CRITICAL: 
- Stages 2, 3, 4 MUST have people (workers) prominently visible
- Stage 3 is the hero shot - most workers, most dynamic
- The epoxy floor must clearly read as poured liquid epoxy art, NOT tiles, NOT marble slabs
- Emphasize: organic flowing patterns, metallic veins, mirror reflections, dimensional depth
"""
    
    def _get_generic_stage_instructions(self, category: ShortCategory) -> str:
        """Generic stage instructions for other categories"""
        return """
STAGE 1: BEFORE / RAW STATE
- Initial state before transformation
- Raw materials or unfinished space
- Realistic "before" condition
- NO people visible
- Clear potential for transformation

STAGE 2: PREP WORK (2-3 PEOPLE)
- 2-3 people preparing materials, setting up
- Measuring, cutting, organizing
- Tools and materials being laid out
- Active preparation phase
- People in appropriate work attire

STAGE 3: ACTIVE BUILD/INSTALLATION (3-4 PEOPLE - HERO SHOT!)
- 3-4 people actively working together
- Main transformation happening (key moment)
- Collaborative work, different tasks
- Tools in use, materials being applied/assembled
- Most dynamic, energetic scene
- People clearly visible and engaged

STAGE 4: FINISHING TOUCHES (2-3 PEOPLE)
- 2-3 people doing detail work, final adjustments
- Quality checking, smoothing, perfecting
- Nearly complete, final touches being added
- Calmer but focused atmosphere
- Transition from build to reveal

STAGE 5: COMPLETED (UNFINISHED)
- Main transformation complete
- Maybe 1 person admiring work or empty
- Finished product or space, clean
- No styling or decoration yet
- Focus on the quality of the work/build

STAGE 6: FINAL STYLED/COMPLETE
- Fully finished with context, styling, or use
- In its final form and purpose
- Satisfying completion reveal
- Lived-in or ready-to-use state

CRITICAL: Stages 2, 3, 4 MUST have people prominently visible and actively working!
"""
