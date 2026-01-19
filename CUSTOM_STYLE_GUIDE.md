# 🎨 Custom Style Configuration Guide

## Overview

You can now fully customize the visual style of your storyboards! Instead of being locked into a single "bratz_doll_style", you can specify:

- Art style
- Lighting
- Color palette
- Background
- Character description
- Camera angles
- Framing

---

## ✨ How to Use Custom Styles

### Option 1: Use Defaults (Easiest)

Just create a job without specifying `style_config`:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Your script here...",
    "generate_images": true
  }'
```

**Defaults:**
- Art style: `bratz_doll_style`
- Lighting: `soft_even_studio_lighting`
- Color palette: `warm_neutral_with_contrast`
- Background: `contextually_relevant_environment`
- Character: `alternative latina girl, nose ring, bangs, glasses`
- Camera: `medium_shot`
- Framing: `centered`

### Option 2: Custom Style (Full Control)

Specify your own style configuration:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Your script here...",
    "generate_images": true,
    "style_config": {
      "art_style": "anime_style",
      "lighting": "dramatic_lighting",
      "color_palette": "vibrant",
      "background": "blurred",
      "character_description": "young entrepreneur, confident, casual business attire",
      "camera_angle": "close_up",
      "framing": "rule_of_thirds"
    }
  }'
```

---

## 🎨 Style Options

### Art Style

Choose the overall aesthetic:

- `bratz_doll_style` - Bold, stylized, Instagram-ready
- `anime_style` - Japanese animation aesthetic
- `realistic` - Photo-realistic renders
- `cartoon` - Western cartoon style
- `oil_painting` - Traditional art style
- `watercolor` - Soft, artistic look
- `minimalist` - Clean, simple design
- `cyberpunk` - Futuristic, neon aesthetic
- `retro_80s` - Vintage 80s vibes
- **Custom:** Any descriptive style you want!

### Lighting

Set the mood with lighting:

- `soft_even_studio_lighting` - Professional, even lighting
- `dramatic_lighting` - High contrast, moody
- `natural_lighting` - Sunlight, realistic
- `golden_hour` - Warm, sunset vibes
- `neon_lighting` - Cyberpunk, colorful
- `backlit` - Silhouette effect
- `spotlight` - Stage/presentation feel
- **Custom:** Describe any lighting you want!

### Color Palette

Choose your color scheme:

- `warm_neutral_with_contrast` - Balanced, appealing
- `vibrant` - Bold, saturated colors
- `muted` - Subtle, professional
- `monochrome` - Black and white
- `pastel` - Soft, light colors
- `neon` - Bright, electric colors
- `earthy` - Natural, brown/green tones
- `cool_tones` - Blues and purples
- **Custom:** Describe any palette!

### Background

Set the scene:

- `contextually_relevant_environment` - Matches the content
- `solid_color` - Clean, simple backdrop
- `blurred` - Bokeh effect, focus on subject
- `studio` - Professional backdrop
- `outdoor` - Natural setting
- `office` - Professional workspace
- `urban` - City environment
- `abstract` - Artistic, non-literal
- **Custom:** Describe any background!

### Character Description

Describe your on-screen persona:

- `alternative latina girl, nose ring, bangs, glasses`
- `young entrepreneur, confident, casual business attire`
- `professional woman, corporate suit, minimal jewelry`
- `creative artist, colorful outfit, energetic`
- `tech expert, hoodie, casual vibe`
- **Custom:** Any detailed description!

**Tips:**
- Be specific about physical features
- Include clothing/style details
- Mention accessories if important
- Keep it consistent across all scenes

### Camera Angle

Control the shot:

- `medium_shot` - Waist up, standard
- `close_up` - Face and shoulders
- `wide_shot` - Full body and environment
- `extreme_close_up` - Just face
- `over_shoulder` - Behind subject
- `dutch_angle` - Tilted for effect
- **Custom:** Any camera angle!

### Framing

Composition style:

- `centered` - Subject in center
- `rule_of_thirds` - Professional composition
- `dynamic` - Energetic, off-center
- `symmetrical` - Balanced composition
- **Custom:** Any framing style!

---

## 📝 Example Use Cases

### Use Case 1: Tech YouTube Channel

```json
{
  "script_text": "Today we're building an AI app...",
  "generate_images": true,
  "style_config": {
    "art_style": "realistic",
    "lighting": "soft_even_studio_lighting",
    "color_palette": "cool_tones",
    "background": "modern_office",
    "character_description": "software developer, hoodie, coding setup visible",
    "camera_angle": "medium_shot",
    "framing": "centered"
  }
}
```

### Use Case 2: Motivational Content

```json
{
  "script_text": "You have the power to change your life...",
  "generate_images": true,
  "style_config": {
    "art_style": "cinematic",
    "lighting": "golden_hour",
    "color_palette": "warm_neutral_with_contrast",
    "background": "urban_landscape",
    "character_description": "confident speaker, stylish casual wear, energetic",
    "camera_angle": "close_up",
    "framing": "rule_of_thirds"
  }
}
```

### Use Case 3: Educational Content

```json
{
  "script_text": "Let's explore the history of...",
  "generate_images": true,
  "style_config": {
    "art_style": "watercolor",
    "lighting": "natural_lighting",
    "color_palette": "earthy",
    "background": "library_setting",
    "character_description": "teacher, professional attire, glasses, welcoming expression",
    "camera_angle": "medium_shot",
    "framing": "centered"
  }
}
```

### Use Case 4: Gaming Channel

```json
{
  "script_text": "Welcome back to another gaming session...",
  "generate_images": true,
  "style_config": {
    "art_style": "anime_style",
    "lighting": "neon_lighting",
    "color_palette": "vibrant",
    "background": "gaming_setup",
    "character_description": "gamer, headset, energetic expression, colorful hair",
    "camera_angle": "close_up",
    "framing": "dynamic"
  }
}
```

---

## 💻 React/JavaScript Example

```javascript
const createJob = async (scriptText, styleConfig) => {
  const response = await fetch('http://localhost:8000/jobs', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      script_text: scriptText,
      generate_images: true,
      style_config: styleConfig
    }),
  });
  
  return await response.json();
};

// Use with default style
const job1 = await createJob("My script text...", null);

// Use with custom style
const job2 = await createJob("My script text...", {
  art_style: "anime_style",
  lighting: "dramatic_lighting",
  color_palette: "vibrant",
  background: "blurred",
  character_description: "young entrepreneur, confident",
  camera_angle: "close_up",
  framing: "rule_of_thirds"
});
```

---

## 🎯 Best Practices

### 1. Consistency is Key

Use the **same style across all videos** in a series to build brand recognition.

### 2. Character Description

Be **specific and detailed**:
- ✅ Good: "young latina woman, nose ring, bangs, black-rimmed glasses, confident expression"
- ❌ Bad: "girl"

### 3. Match Content

Choose styles that **match your content type**:
- Tech: Clean, modern, professional
- Entertainment: Vibrant, energetic
- Education: Clear, approachable
- Gaming: Bold, dynamic

### 4. Test Different Styles

Create a few test jobs with different styles to see what works best for your brand!

---

## 💰 Cost Impact

Different styles don't change the cost! Pricing is based on:
- Number of scenes (sentence count)
- Image generation (per image)

**Not affected by:**
- Style complexity
- Custom vs default styles
- Detailed descriptions

---

## 🔄 Changing Style Mid-Project

Each job uses its own style configuration. To change styles:

1. Create a new job with the new style
2. The old job remains unchanged
3. You can mix and match for different videos

---

## 🆘 Troubleshooting

### Images Don't Match Description

If images don't match your style:
1. Be more specific in descriptions
2. Use established art style names (anime, realistic, etc.)
3. Check spelling in all fields
4. Try a test job with minimal text first

### Style Not Applying

Make sure you're sending `style_config` as a JSON object, not a string:

```json
// ✅ Correct
"style_config": {
  "art_style": "anime_style"
}

// ❌ Wrong
"style_config": "anime_style"
```

---

## 📚 Related Docs

- `API_EXAMPLES.md` - Full API reference
- `UI_INTEGRATION_GUIDE.md` - Frontend integration
- `COST_TRACKING.md` - Cost tracking features

---

## 🎨 Need Help?

1. Start with defaults
2. Modify one field at a time
3. Test with short scripts first
4. Check the generated images in debug_images/ folder

Happy creating! 🚀
