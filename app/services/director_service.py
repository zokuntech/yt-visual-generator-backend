import json
import os
import logging
from typing import Tuple
from openai import OpenAI
from app.models.scene import ScenePlan, SceneCharacter, SceneProp, SceneSetting, CameraIntent

logger = logging.getLogger(__name__)

# OpenAI pricing
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input": 0.150 / 1_000_000,
        "output": 0.600 / 1_000_000,
    }
}


class DirectorService:
    """The Director - analyzes narrative and plans the scene"""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def generate_scene_plan(
        self,
        scene_id: str,
        sentence: str,
        previous_plan: ScenePlan = None,
        global_style = None
    ) -> Tuple[ScenePlan, float, int]:
        """
        🎬 THE DIRECTOR
        Analyzes the sentence and creates a scene plan
        Returns: (ScenePlan, cost, tokens)
        """
        
        system_prompt = self._build_director_prompt(previous_plan, global_style)
        user_prompt = f"Analyze this sentence and create a scene plan:\n\n\"{sentence}\""
        
        try:
            logger.debug(f"🎬 Director analyzing: {sentence[:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.95,  # MAX creativity!
            )
            
            # Calculate cost
            usage = response.usage
            input_cost = usage.prompt_tokens * OPENAI_PRICING[self.model]["input"]
            output_cost = usage.completion_tokens * OPENAI_PRICING[self.model]["output"]
            total_cost = input_cost + output_cost
            total_tokens = usage.total_tokens
            
            # Parse response
            content = response.choices[0].message.content
            plan_data = json.loads(content)
            
            # Add scene_id and sentence
            plan_data["scene_id"] = scene_id
            plan_data["sentence"] = sentence
            
            # Create ScenePlan
            scene_plan = ScenePlan(**plan_data)
            
            logger.debug(f"   📋 Plan: {scene_plan.narrative_role} | {scene_plan.emotional_tone}")
            logger.debug(f"   🎥 Camera: {scene_plan.camera_intent.shot} | {scene_plan.camera_intent.framing}")
            
            return scene_plan, total_cost, total_tokens
            
        except Exception as e:
            logger.warning(f"Director failed: {e}")
            # Fallback to basic plan
            return self._create_fallback_plan(scene_id, sentence), 0.0, 0
    
    def _build_director_prompt(self, previous_plan: ScenePlan = None, global_style = None) -> str:
        """Build the director's system prompt"""
        
        style_context = ""
        if global_style:
            style_context = f"""
🎨 GLOBAL STYLE CONTEXT:
- Art Style: {global_style.art_style}
- Character: {global_style.character_description}
- Overall Mood: {global_style.lighting} with {global_style.color_palette} palette

Keep this visual style in mind when choosing settings and props.
"""
            
            # Add user-specified locations if provided
            if global_style.preferred_settings and len(global_style.preferred_settings) > 0:
                settings_list = ", ".join(global_style.preferred_settings)
                style_context += f"""
🎯 USER-SPECIFIED LOCATIONS (USE THESE PRIORITIZED):
{settings_list}

⚠️ IMPORTANT: Choose locations from this list when possible! These are the user's preferred backgrounds.
Cycle through them to create variety across scenes.
"""
        
        previous_context = ""
        if previous_plan:
            previous_context = f"""
🎬 PREVIOUS SCENE CONTEXT:
- Emotional tone: {previous_plan.emotional_tone}
- Camera: {previous_plan.camera_intent.shot}
- Setting: {previous_plan.setting.environment}

🚨 MANDATORY VARIATION:
- You MUST use a DIFFERENT setting than "{previous_plan.setting.environment}"
- You MUST use a DIFFERENT camera shot than "{previous_plan.camera_intent.shot}"
- Add visual contrast to prevent monotony
"""
        
        return f"""You are THE DIRECTOR of a visual storytelling project for YouTube.

{style_context}

🔥 YOUR MISSION: Create WILDLY DIVERSE, VISUALLY STUNNING scenes that DEMAND attention!

🚫 FORBIDDEN: Boring, repetitive, bland scenes. Every scene must be VISUALLY DISTINCT!

{previous_context}

RESPOND WITH THIS EXACT JSON STRUCTURE:

{{
  "narrative_role": "Choose: emotional_low_point | realization | tension | release | reflection | contrast | peak_moment | turning_point | buildup | confrontation | breakthrough",
  "emotional_tone": "Choose: conflicted | hopeful | detached | overwhelmed | calm | tense | distant | resigned | energized | anxious | curious | melancholic | determined | excited | frustrated | relieved | confused | focused",
  "energy_level": "Choose: low | medium | high",
  "visual_focus": "Choose: internal_state | character | environment | interaction | symbolic | action | group_dynamic | contrast",
  
  "characters": [
    {{
      "role": "Choose: main_character | friend | stranger | group_of_people | passerby | NO_CHARACTER (b-roll shot, no people visible)",
      "presence": "Choose: primary | background | multiple | NONE (pure b-roll/environmental shot)",
      "interaction": "Choose: isolated | engaging_in_conversation | laughing_together | working_side_by_side | walking_past | sitting_nearby | making_eye_contact | ignoring_each_other | in_motion | gesturing | collaborating | debating | observing | NOT_APPLICABLE (no people in shot)",
      "activity": "🔥 WHAT IS THE CHARACTER DOING? Be SPECIFIC and VARIED:
      
      💪 ACTIVE POSES:
      - stretching | exercising | running | walking | dancing | jumping | climbing | reaching_up | bending_down | kneeling | crouching | leaning_against | lying_down | sitting_cross_legged | standing_on_tiptoes
      
      🖐️ HAND GESTURES & ACTIONS:
      - typing | writing | drawing | painting | pointing | waving | covering_face | holding_phone | scrolling | texting | taking_photo | holding_coffee | eating | drinking | cooking | cleaning | organizing | fixing_something | building | creating
      
      😊 FACIAL EXPRESSIONS & HEAD:
      - looking_up | looking_down | looking_away | staring_intently | eyes_closed | smiling | laughing | thinking_hand_on_chin | tilting_head | nodding | shaking_head | looking_over_shoulder
      
      🎭 EMOTIONAL BODY LANGUAGE:
      - arms_crossed | hands_in_pockets | fidgeting | pacing | sitting_hunched | sitting_upright | leaning_forward | leaning_back | sprawled_out | curled_up | tense_posture | relaxed_posture | confident_stance | defensive_posture
      
      🎨 CREATIVE ACTIVITIES:
      - sketching | photographing | filming | recording | playing_instrument | singing | crafting | sculpting | knitting | sewing | reading | studying | researching | experimenting
      
      🏃 MOVEMENT & MOTION:
      - walking_purposefully | strolling_casually | jogging | sprinting | skipping | spinning | turning | entering | exiting | approaching | retreating | climbing_stairs | descending_stairs
      
      ⚡ PICK ACTIVITIES THAT MATCH THE EMOTION! Examples:
      - Anxious → pacing, fidgeting, hands_in_hair, looking_around
      - Determined → focused_typing, purposeful_walking, leaning_forward
      - Contemplative → staring_out_window, hand_on_chin, looking_up
      - Excited → jumping, arms_raised, dancing, animated_gestures
      - Exhausted → slouched, head_in_hands, lying_down, eyes_closed
      - Curious → leaning_in, reaching_out, examining_object, tilting_head"
    }}
    
    ⚠️ VARY YOUR PEOPLE STRATEGY - CHARACTER DOESN'T HAVE TO BE IN EVERY SCENE!:
    - 60% of scenes: B-ROLL (NO character visible - just objects, environments, details)
    - 40% character visible:
      * Sometimes: Character completely alone
      * Sometimes: Character + 1-2 specific people  
    - Sometimes: Character in crowd/background people (1/3 of scenes)
    
    DON'T put "background people" in EVERY scene! Mix it up!
  ],
  
  "props": [
    {{
      "type": "Choose MULTIPLE interesting objects: phone | laptop | coffee_cup | book | journal | headphones | backpack | keys | water_bottle | notebook | pen | tablet | mirror | window | plant | bicycle | shopping_bags | food_tray | gym_bag | art_supplies | skateboard | camera | musical_instrument | suitcase | umbrella | sunglasses | watch | wallet | earbuds | gaming_controller | whiteboard | sticky_notes | calendar | map | magazine | newspaper | painting | sculpture | vase | flowers | candles | pillow | blanket | poster | photo_frame | clock | lamp | desk_organizer | mouse | keyboard | screen | charger | cables | speakers | vinyl_record | guitar_pick | drumsticks | paintbrush | sketchpad | easel | pottery | fabric | scissors | thread | yarn | knitting_needles | cookbook | cutting_board | knife | pan | plate | bowl | mug | thermos | lunch_box | snack | fruit | sandwich | pizza_box | takeout_bag | receipt | tickets | boarding_pass | ID_card | badge | lanyard | name_tag | business_card | flyer | brochure | menu | sign | banner | flag",
      "symbolism": "What does it represent?",
      "interaction": "Choose: holding | using | ignoring | looking_at | setting_down | picking_up | background | interacting_with | surrounded_by"
    }}
    
    🎯 ADD 2-4 PROPS! Make scenes rich with detail!
    Examples:
    - Coffee cup + laptop + notebook (working)
    - Phone + keys + jacket (leaving)
    - Book + coffee + window view (reading)
    - Skateboard + backpack + headphones (commuting)
  ],
  "setting": {{
    "location": "Choose: interior | exterior | transitional | unexpected",
    "environment": "🎨 BE CREATIVE! Choose from user-specified locations if provided above, otherwise choose VISUALLY INTERESTING locations:
    
    🏠 HOME (but make it interesting):
    - bedroom_messy_desk | cozy_living_room_golden_hour | kitchen_cooking_chaos | bathroom_mirror_foggy | home_office_plants_everywhere | hallway_photo_wall | stairs_dramatic_lighting | balcony_city_view | rooftop_sunset
    
    ☕ PUBLIC SPACES (bustling with life):
    - coffee_shop_window_rainy_day | library_stacks_dramatic_shadows | bookstore_cozy_reading_nook | mall_food_court_crowd | shopping_center_escalator | gym_during_class | yoga_studio_sunrise | art_gallery_modern | museum_ancient_artifacts | movie_theater_empty_seats | arcade_neon_lights | bowling_alley | pool_hall
    
    🏢 WORK/SCHOOL (varied):
    - office_cubicle_late_night | conference_room_presentation | empty_classroom_sunset | school_hallway_lockers | campus_quad_students | lecture_hall_back_row | study_lounge_group | lab_equipment_everywhere | studio_creative_chaos | workshop | factory_floor
    
    🌳 OUTDOOR (dynamic):
    - park_bench_autumn_leaves | walking_path_joggers | city_street_busy | bus_stop_rain | train_platform_crowd | parking_lot_golden_hour | rooftop_city_lights | garden_overgrown | beach_sunset | bridge_river_view | playground_empty | skate_park | basketball_court | hiking_trail | pier | dock | waterfront
    
    🚗 TRANSPORT (in motion):
    - car_interior_traffic | bus_seat_window_view | train_car_commuters | subway_platform_rush_hour | bike_path_scenic | taxi | uber | airplane_window | ferry | boat
    
    🎉 SOCIAL (energy):
    - restaurant_date_night | bar_counter_friends | house_party_living_room | concert_crowd | sports_field_game | dance_floor | karaoke_room | game_night | picnic | barbecue | celebration
    
    🎯 UNIQUE/UNEXPECTED:
    - elevator | stairwell | parking_garage | laundromat | convenience_store | gas_station | waiting_room | hotel_lobby | airport_terminal | post_office | bank | dmv | pharmacy | clinic | vet_office | pet_store | flower_shop | farmers_market | flea_market | thrift_store | record_store | comic_shop | hobby_store
    
    ⚡ GO BOLD! Pick unexpected but emotionally resonant locations!",
    "symbolic_elements": ["Choose 2-4: window_with_view | dramatic_shadow | golden_light | mirror_reflection | bustling_crowd | empty_space | plants | urban_backdrop | screens_glowing | isolation_visual | connection_visual | movement_blur | stillness_frozen | weather_element | time_of_day | clutter | minimalism | height | depth"]
  }},
  "camera_intent": {{
    "shot": "Choose DRAMATICALLY VARIED shots: close_up | extreme_close_up | medium_shot | medium_close_up | full_shot | wide_shot | extreme_wide_shot | over_shoulder | dutch_angle | profile | birds_eye | worms_eye | two_shot | group_shot | establishing_shot | detail_shot",
    "angle": "Choose DYNAMIC angles: eye_level | low_angle | high_angle | slightly_low | slightly_high | ground_level | overhead | canted | tilted | dutch",
    "framing": "Choose INTERESTING framing: centered | rule_of_thirds | off_center | dynamic | leading_lines | frame_within_frame | negative_space | symmetrical | asymmetrical | foreground_interest | depth_layers"
  }},
  "motion": "🎬 PICK A SPECIFIC ACTION! Don't just say 'still':
  
  Choose from: typing_intensely | scrolling_phone | writing_notes | sketching | reading_book | sipping_coffee | eating | cooking | cleaning | organizing | exercising | stretching | yoga_pose | running | walking_purposefully | sitting_down | standing_up | leaning_against_wall | looking_out_window | staring_at_screen | gesturing_while_talking | laughing | crying | sighing | thinking_deeply | hand_on_chin | covering_face | rubbing_eyes | stretching_arms | cracking_knuckles | fidgeting | pacing | dancing | jumping | reaching_up | bending_down | turning_around | looking_over_shoulder | tilting_head | nodding | shaking_head | waving | pointing | taking_photo | playing_instrument | painting | drawing | building | fixing_something | playing_with_object | tying_shoes | putting_on_jacket | adjusting_clothes | checking_watch | looking_at_phone | putting_down_phone | picking_up_item | setting_down_item",
  
  "variation_from_previous": true
}}

🔥 MANDATORY CREATIVITY RULES (FOLLOW THESE OR FAIL):

1. **WHAT IS THE CHARACTER DOING? BE SPECIFIC!**
   - ❌ DON'T: Just say "still" or generic "sitting"
   - ✅ DO: Describe SPECIFIC actions, poses, and body language
   - Examples:
     * "I felt overwhelmed" → Character hunched over desk, head in hands, surrounded by papers
     * "I had an idea" → Character leaning back, eyes lighting up, hand reaching for pen
     * "I was tired" → Character slouched on couch, eyes half-closed, coffee cup slipping
     * "I felt free" → Character arms spread wide, spinning, head thrown back laughing
     * "I worked late" → Character typing intensely, leaning into screen, coffee nearby
     * "I called my friend" → Character pacing, gesturing while talking on phone
   
   🎯 MATCH POSE TO EMOTION:
   - Anxious → fidgeting, pacing, hands in hair
   - Confident → upright posture, purposeful movements, direct gaze
   - Sad → hunched, looking down, slow movements
   - Excited → animated gestures, bouncing, leaning forward
   - Contemplative → hand on chin, looking up/away, still
   - Exhausted → slouched, head back, eyes closed

2. **CHARACTER DOESN'T NEED TO BE IN EVERY SCENE! USE B-ROLL!**
   - ❌ DON'T: Force the character into every single scene
   - ✅ DO: Mix character shots with creative b-roll
   - Rule: ~40% character visible, ~60% b-roll/environmental shots
   - 
   - 🎬 B-ROLL IDEAS (NO CHARACTER VISIBLE):
     * Objects: Close-up of phone screen, coffee steaming, keyboard typing, book pages turning
     * Environment: Empty street at dawn, rain on window, city skyline, nature shots
     * Details: Hands typing (no face), feet walking, door opening, light switching
     * Atmospheric: Shadows, reflections, textures, weather, time passing
     * Symbolic: Clock ticking, calendar pages, sunset, sunrise, seasons changing
   - 
   - 👤 WHEN CHARACTER IS VISIBLE, VARY CONTEXT:
     * Sometimes alone: Character in empty space, isolated, contemplative
     * Sometimes with specific people: Friend, colleague, stranger interaction
     * Sometimes in crowds: Busy street, party, public space

3. **ADD MULTIPLE PROPS! MAKE SCENES RICH!**
   - ❌ DON'T: Empty scenes with no objects
   - ✅ DO: 2-4 props per scene minimum
   - Examples:
     * Working → laptop + coffee + notebook + phone
     * Leaving → keys + jacket + backpack + phone
     * Reading → book + coffee + blanket + window
     * Commuting → headphones + phone + bag + transit_pass

4. **LOCATION VARIETY IS NON-NEGOTIABLE**
   - ❌ DON'T: Repeat locations within 5 scenes
   - ✅ DO: Jump between locations frequently
   - Flow example for a 10-scene story:
     1. Bedroom_morning → 2. Kitchen_coffee → 3. Car_commute → 4. Office_desk → 5. Coffee_shop_meeting → 
     6. Park_walking → 7. Gym_workout → 8. Restaurant_dinner → 9. Street_night → 10. Bedroom_evening

5. **CAMERA ANGLES MUST BE DYNAMIC**
   - ❌ DON'T: Use medium_shot + eye_level for everything
   - ✅ DO: Mix it up aggressively
   - Sequence example:
     Wide_shot → Close_up → Over_shoulder → Birds_eye → Medium_shot → Low_angle → Dutch_angle → Profile

6. **MATCH VISUAL STYLE TO EMOTION** (be specific!)
   - Isolated/lonely → Empty space, single character, distant framing, cold colors
   - Anxious → Crowded space, tilted angle, tight framing, people everywhere
   - Hopeful → Bright lighting, open space, windows, upward angle, warm tones
   - Contemplative → Quiet space, thoughtful pose, soft lighting, props like books/coffee
   - Energized → Movement, bright colors, active space, multiple people, dynamic angle
   - Confused → Clutter, crowd, dutch angle, distracted character, many props
   - Determined → Clear focus, dramatic lighting, purposeful pose, minimal distractions

7. **MAKE EVERY SCENE MEMORABLE WITH SPECIFIC ACTIONS**
   - Think: "What makes THIS scene visually unique? What is the character DOING?"
   - Examples:
     * ❌ Boring: "Character sits at desk"
     * ✅ Interesting: "Character hunched over messy desk, typing intensely, late night, surrounded by coffee cups and papers, dramatic lamp lighting, rubbing tired eyes"
     
     * ❌ Boring: "Character walks outside"
     * ✅ Interesting: "Character walks purposefully through busy street, sunset golden hour, people blur past, checking phone while holding coffee, determined expression"
     
     * ❌ Boring: "Character looks sad"
     * ✅ Interesting: "Character alone on bench, head in hands, autumn leaves falling around them, empty park, hunched posture, shoulders shaking"

8. **LAYER YOUR VISUALS**
   - Foreground + Subject + Background = DEPTH
   - Examples:
     * Coffee shop: Blurred customers in foreground → Character sipping coffee at table → Window with street view in background
     * Park: Tree branches frame → Character stretching on bench → Playground in background
     * Office: Monitor glow foreground → Character typing intensely → Window city view background

9. **USE UNEXPECTED COMBINATIONS**
   - Sad moment in bright sunny park (contrast)
   - Happy moment in dimly lit bar (intimate)
   - Anxious moment in peaceful library (internal vs external)
   - Calm moment in busy street (finding peace)

🚨 CRITICAL REMINDERS:
- ALWAYS describe SPECIFIC character actions/poses (not just "still" or "sitting")
- VARY people presence: 1/3 alone, 1/3 with specific people, 1/3 in crowds
- NEVER make 3+ consecutive scenes in the same type of location
- NEVER use the same camera shot 2 scenes in a row
- ALWAYS include at least 2-4 props per scene
- CONSTANTLY vary camera angles and character activities
- MATCH CHARACTER POSE/ACTION TO EMOTION
- MAKE SCENES VISUALLY DISTINCT AND MEMORABLE!

🎬 You are a VISIONARY DIRECTOR, not a boring documentarian. THINK BIG! BE BOLD! SURPRISE US!
"""
    
    def _create_fallback_plan(self, scene_id: str, sentence: str) -> ScenePlan:
        """Create a basic fallback plan if director fails"""
        return ScenePlan(
            scene_id=scene_id,
            sentence=sentence,
            narrative_role="reflection",
            emotional_tone="calm",
            energy_level="medium",
            visual_focus="character",
            characters=[SceneCharacter(
                role="main_character",
                presence="primary",
                interaction="neutral"
            )],
            props=[],
            setting=SceneSetting(
                location="interior",
                environment="simple_room",
                symbolic_elements=[]
            ),
            camera_intent=CameraIntent(
                shot="medium_shot",
                angle="eye_level",
                framing="centered"
            ),
            motion="still"
        )


# Global singleton
director_service = DirectorService() if os.getenv("OPENAI_API_KEY") else None
