# Custom Backgrounds Feature

## Overview

The UI can now specify a list of **preferred backgrounds/locations** that the Director will use when generating scenes. This gives you full control over where scenes take place!

## How to Use

### Option 1: Specify Backgrounds in Job Creation

```javascript
const jobRequest = {
  script_text: "Your script here...",
  generate_images: true,
  style_config: {
    art_style: "realistic",
    lighting: "natural_lighting",
    color_palette: "warm_neutral",
    character_description: "young professional, casual attire",
    
    // 🎯 NEW: Specify your preferred locations
    preferred_settings: [
      "coffee_shop_by_window",
      "city_street_sidewalk",
      "park_bench_under_tree",
      "modern_office_desk",
      "cozy_living_room",
      "gym_workout_area"
    ]
  }
};

// Send to backend
fetch('/jobs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(jobRequest)
});
```

### Option 2: Let Users Choose Backgrounds

```jsx
// React Component Example
const BackgroundSelector = () => {
  const [selectedBGs, setSelectedBGs] = useState([]);
  
  const availableBackgrounds = [
    // Interior
    { id: "coffee_shop_by_window", label: "☕ Coffee Shop" },
    { id: "library_study_area", label: "📚 Library" },
    { id: "bedroom_at_desk", label: "🏠 Bedroom" },
    { id: "modern_office_desk", label: "💼 Office" },
    { id: "gym_workout_area", label: "💪 Gym" },
    
    // Outdoor
    { id: "park_bench_under_tree", label: "🌳 Park" },
    { id: "city_street_sidewalk", label: "🏙️ City Street" },
    { id: "beach", label: "🏖️ Beach" },
    { id: "rooftop", label: "🏢 Rooftop" },
    
    // Social
    { id: "restaurant_table", label: "🍽️ Restaurant" },
    { id: "shopping_mall_corridor", label: "🛍️ Mall" },
    { id: "movie_theater_lobby", label: "🎬 Theater" },
  ];
  
  return (
    <div>
      <h3>Select Backgrounds for Your Video</h3>
      <p>Choose 4-8 locations for variety</p>
      
      {availableBackgrounds.map(bg => (
        <label key={bg.id}>
          <input
            type="checkbox"
            checked={selectedBGs.includes(bg.id)}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedBGs([...selectedBGs, bg.id]);
              } else {
                setSelectedBGs(selectedBGs.filter(id => id !== bg.id));
              }
            }}
          />
          {bg.label}
        </label>
      ))}
    </div>
  );
};
```

## Available Backgrounds

### 🏠 Interior Spaces
- `bedroom_at_desk` - Bedroom with work desk
- `cozy_living_room` - Comfortable living space
- `kitchen_counter` - Kitchen area
- `bathroom_mirror` - Bathroom with mirror
- `home_office` - Home workspace
- `hallway` - Indoor hallway
- `stairs` - Staircase area

### ☕ Public Spaces
- `coffee_shop_by_window` - Café with window seat
- `library_study_area` - Library workspace
- `bookstore_aisle` - Bookstore between shelves
- `mall_food_court` - Shopping mall dining area
- `shopping_mall_corridor` - Mall walkway
- `gym_workout_area` - Fitness center
- `yoga_studio` - Yoga/meditation space
- `art_gallery` - Gallery exhibition space
- `museum_room` - Museum interior
- `movie_theater_lobby` - Theater entrance

### 💼 Work/School
- `modern_office_desk` - Office workspace
- `conference_room` - Meeting room
- `empty_classroom` - School classroom
- `school_hallway` - School corridor
- `campus_quad` - College campus outdoor area
- `lecture_hall` - University lecture room
- `study_lounge` - Study area
- `lab_room` - Laboratory space

### 🌳 Outdoor
- `park_bench_under_tree` - Park seating
- `walking_path_in_park` - Park trail
- `city_street_sidewalk` - Urban sidewalk
- `bus_stop` - Public transit stop
- `train_platform` - Train station
- `parking_lot` - Parking area
- `rooftop` - Building rooftop
- `balcony` - Outdoor balcony
- `garden` - Garden space
- `beach` - Beach setting
- `bridge` - Bridge location
- `playground` - Playground area

### 🚗 Transport
- `car_interior` - Inside car
- `bus_seat` - On bus
- `train_car` - In train
- `subway_platform` - Metro station
- `bike_path` - Cycling route

### 🎉 Social
- `restaurant_table` - Dining out
- `bar_counter` - Bar setting
- `friends_living_room` - Social gathering
- `party_space` - Event venue
- `concert_venue` - Music venue
- `sports_field` - Athletic field

## Best Practices

### 1. **Choose 4-8 Locations**
Too few = repetitive. Too many = scattered narrative.

```javascript
preferred_settings: [
  "coffee_shop_by_window",    // Contemplative
  "city_street_sidewalk",     // Active/energized
  "park_bench_under_tree",    // Peaceful
  "modern_office_desk",       // Professional
  "gym_workout_area",         // Determined
]
```

### 2. **Match Locations to Video Theme**

**Self-Help/Motivation:**
```javascript
preferred_settings: [
  "gym_workout_area",
  "park_bench_under_tree",
  "rooftop",
  "beach"
]
```

**Productivity/Work:**
```javascript
preferred_settings: [
  "home_office",
  "coffee_shop_by_window",
  "library_study_area",
  "modern_office_desk"
]
```

**Social/Relationships:**
```javascript
preferred_settings: [
  "coffee_shop_by_window",
  "restaurant_table",
  "park_bench_under_tree",
  "friends_living_room"
]
```

**Personal Growth:**
```javascript
preferred_settings: [
  "bedroom_at_desk",
  "library_study_area",
  "walking_path_in_park",
  "rooftop"
]
```

### 3. **Provide Variety**
Mix indoor/outdoor, public/private, active/contemplative spaces.

### 4. **Optional Field**
If you don't provide `preferred_settings`, the Director will automatically choose diverse locations based on the script's emotional content.

## Response Format

The API response will include the chosen settings in each scene:

```json
{
  "scenes": [
    {
      "scene_plan": {
        "setting": {
          "location": "interior",
          "environment": "coffee_shop_by_window",
          "symbolic_elements": ["window", "light"]
        }
      }
    }
  ]
}
```

## Example: Full Job Request

```javascript
const createStoryboard = async () => {
  const response = await fetch('http://localhost:8000/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_text: `
        Why Your Confidence Feels Exhausting (Nervous System Edition)
        
        Confidence isn't something you build.
        It's something you stop hiding.
        Like eventually, if you cared too much and it didn't work, 
        you'd just shut something off inside yourself.
        You'd stop wanting things as badly.
      `,
      generate_images: true,
      style_config: {
        art_style: "realistic",
        lighting: "natural_lighting",
        color_palette: "warm_neutral",
        character_description: "young adult, casual professional attire, thoughtful",
        
        // Custom backgrounds for this specific video
        preferred_settings: [
          "coffee_shop_by_window",      // Opening - contemplative
          "bedroom_at_desk",            // Internal reflection
          "city_street_sidewalk",       // Moving forward
          "park_bench_under_tree",      // Realization moment
          "rooftop"                     // Hopeful ending
        ]
      }
    })
  });
  
  const job = await response.json();
  console.log('Job created:', job.id);
  
  // Poll for completion...
};
```

## Tips

1. **Start Simple**: Try 4-5 locations for your first videos
2. **Test Different Combos**: See what works for your content style
3. **Theme Consistency**: Choose locations that fit your video's mood
4. **Let AI Help**: If unsure, omit `preferred_settings` and let the Director choose

---

**Questions?** Check the main API docs or test with the example above!
