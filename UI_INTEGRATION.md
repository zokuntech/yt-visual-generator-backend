# 🎬 YouTube Visual Generator - Complete UI Integration Guide

**Last Updated**: January 2026

This is the ONLY guide you need to integrate with the backend. Everything else is here.

---

## 📚 Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Creating Jobs](#creating-jobs)
4. [Scene Management](#scene-management)
5. [Scene Editing](#scene-editing)
6. [Video Animation (Veo 3.1)](#video-animation)
7. [Cost Tracking](#cost-tracking)
8. [Edit Assistant](#edit-assistant)
9. [Custom Styles & Backgrounds](#custom-styles)
10. [B-Roll & Creative Visuals](#b-roll)
11. [Complete React Examples](#react-examples)

---

## 🚀 Quick Start

### Base URL
```
http://localhost:8000
```

### Basic Flow
```
1. POST /jobs          → Create job with script
2. GET /jobs/{id}      → Poll for completion
3. GET /scenes/job/{id} → Get all scenes
4. Edit scenes if needed
5. POST /scenes/{id}/animate → Turn into videos
```

---

## 📡 API Endpoints

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/jobs` | Create new storyboard job |
| GET | `/jobs/{id}` | Get job status |
| GET | `/jobs/{id}/cost` | Get live cost breakdown |

### Scenes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/scenes/job/{job_id}` | Get all scenes for a job |
| GET | `/scenes/{id}` | Get specific scene |
| POST | `/scenes/{id}/regenerate-image` | Regenerate image |
| POST | `/scenes/{id}/regenerate-with-instruction` | Edit with text |
| GET | `/scenes/{id}/edit-suggestions` | Get edit suggestions |
| POST | `/scenes/{id}/refine-instruction` | Refine vague edits |
| POST | `/scenes/{id}/animate` | Turn image into video |
| GET | `/scenes/{id}/video-status` | Check video status |

---

## 1️⃣ Creating Jobs

### Request
```javascript
const response = await fetch('/jobs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    script_text: "Your YouTube script here...",
    generate_images: true,
    style_config: {
      art_style: "professional_youtube_style",
      character_description: "young content creator, casual",
      aspect_ratio: "16:9",  // or "9:16", "1:1", "4:3"
      preferred_settings: ["coffee_shop", "park", "home_office"]
    }
  })
});

const job = await response.json();
console.log(job.id);  // Save this!
```

### Response
```json
{
  "id": "job_abc123",
  "status": "pending",
  "script_text": "...",
  "scene_ids": [],
  "cost": {
    "total_cost": 0,
    "num_prompts_generated": 0,
    "num_images_generated": 0,
    "num_videos_generated": 0
  }
}
```

### Polling for Completion
```javascript
const pollJob = async (jobId) => {
  const response = await fetch(`/jobs/${jobId}`);
  const job = await response.json();
  
  if (job.status === 'completed') {
    return job;
  } else if (job.status === 'failed') {
    throw new Error(job.error_message);
  }
  
  // Poll every 2 seconds
  await new Promise(r => setTimeout(r, 2000));
  return pollJob(jobId);
};
```

### Job Status Values
- `pending` → Just created
- `analyzing_script` → Director working
- `generating_images` → Creating images
- `completed` → ✅ Done!
- `failed` → ❌ Error

---

## 2️⃣ Scene Management

### Get All Scenes
```javascript
const response = await fetch(`/scenes/job/${jobId}`);
const scenes = await response.json();

// Scenes are already sorted by index
scenes.forEach(scene => {
  console.log(scene.sentence_text);
  console.log(scene.image_url);  // data:image/png;base64,...
});
```

### Scene Object Structure
```json
{
  "id": "scene_xyz",
  "job_id": "job_abc",
  "index": 0,
  "sentence_text": "I felt overwhelmed.",
  "image_status": "generated",
  "image_url": "data:image/png;base64,...",
  "video_status": "not_requested",
  "video_url": null,
  "generation_cost": 0.002145,
  "last_operation_cost": 0
}
```

---

## 3️⃣ Scene Editing

### Method 1: Simple Regeneration
Just regenerate with same prompt:
```javascript
const response = await fetch(`/scenes/${sceneId}/regenerate-image`, {
  method: 'POST'
});
const scene = await response.json();
console.log(`Cost: $${scene.last_operation_cost}`);
```

### Method 2: Edit with Text Instructions (RECOMMENDED)
```javascript
const response = await fetch(`/scenes/${sceneId}/regenerate-with-instruction`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    instruction: "make the character smile and add a laptop"
  })
});

const scene = await response.json();
// scene.image_url is the new image
// scene.last_operation_cost is the cost
```

**Example Instructions**:
- "make the character smile"
- "change setting to a coffee shop"
- "add a laptop on the desk"
- "make it nighttime with dramatic lighting"
- "zoom in for close-up"
- "add other people in the background"

---

## 4️⃣ Video Animation (Veo 3.1)

### Start Video Generation
```javascript
const response = await fetch(`/scenes/${sceneId}/animate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    aspect_ratio: "16:9",  // or "9:16"
    custom_prompt: null    // optional: override scene text
  })
});

const scene = await response.json();
// scene.video_status = "pending"
// scene.last_operation_cost = 0.09 (estimated)
```

### Poll for Video Completion
```javascript
const pollVideo = async (sceneId) => {
  const response = await fetch(`/scenes/${sceneId}/video-status`);
  const scene = await response.json();
  
  if (scene.video_status === 'generated') {
    return scene.video_url;  // data:video/mp4;base64,...
  } else if (scene.video_status === 'failed') {
    throw new Error(scene.last_error);
  }
  
  // Still processing, poll every 5 seconds
  await new Promise(r => setTimeout(r, 5000));
  return pollVideo(sceneId);
};

// Usage
const videoUrl = await pollVideo(sceneId);
```

### Video Status Values
- `not_requested` → No video yet
- `pending` → Just started
- `processing` → Generating (11s - 6min)
- `generated` → ✅ Done! Check `video_url`
- `failed` → ❌ Error

---

## 5️⃣ Cost Tracking

### Live Cost Counter
```javascript
const CostCounter = ({ jobId }) => {
  const [cost, setCost] = useState(0);

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch(`/jobs/${jobId}/cost`);
      const data = await res.json();
      setCost(data.total_cost);
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return <div>💰 ${cost.toFixed(4)}</div>;
};
```

### Cost Breakdown
```javascript
const response = await fetch(`/jobs/${jobId}/cost`);
const cost = await response.json();

console.log(cost);
// {
//   "total_cost": 0.1234,
//   "prompt_generation_cost": 0.0012,  // GPT for scene planning
//   "image_generation_cost": 0.0222,   // Gemini images
//   "video_generation_cost": 0.1000,   // Veo videos
//   "num_prompts_generated": 10,
//   "num_images_generated": 10,
//   "num_videos_generated": 1
// }
```

### Typical Costs
| Operation | Cost | Notes |
|-----------|------|-------|
| Scene generation | ~$0.00015 | Director + Cinematographer (GPT) |
| Image generation | ~$0.002 | Gemini image |
| Image regeneration | ~$0.002 | Just image |
| Scene edit (text) | ~$0.00215 | Cinematographer + image |
| Video animation | ~$0.09 | Veo 3.1 Fast, 6-8 seconds |

**Example**: 10 scenes, all with videos = ~$0.94 total

---

## 6️⃣ Edit Assistant

### Get Edit Suggestions
See what can be changed in a scene:

```javascript
const response = await fetch(`/scenes/${sceneId}/edit-suggestions`);
const data = await response.json();

console.log(data);
// {
//   "current_state": {
//     "character": { "pose": "sitting", "expression": "worried" },
//     "setting": { "location": "office", "lighting": "harsh" },
//     "camera": { "shot": "medium_shot", "angle": "eye_level" }
//   },
//   "edit_categories": [
//     {
//       "category": "Character Pose & Expression",
//       "suggestions": [
//         {
//           "description": "Change what the character is doing",
//           "example_instruction": "make the character standing and stretching"
//         }
//       ]
//     }
//   ]
// }
```

### Refine Vague Instructions
Turn "make it better" into something specific:

```javascript
const response = await fetch(`/scenes/${sceneId}/refine-instruction`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    instruction: "make it happier"  // Vague
  })
});

const data = await response.json();
// {
//   "original": "make it happier",
//   "refined": "change character expression to bright smile with relaxed posture, add warm golden hour lighting, create uplifting atmosphere",
//   "cost": 0.0001
// }

// Then use the refined version
await editScene(sceneId, data.refined);
```

---

## 7️⃣ Custom Styles & Backgrounds

### Custom Style Config
```javascript
{
  style_config: {
    art_style: "professional_youtube_style",
    lighting: "natural_lighting",  // or "golden_hour", "dramatic", "soft"
    color_palette: "warm_neutral",  // or "vibrant", "cool", "moody"
    character_description: "young female content creator, casual streetwear",
    aspect_ratio: "16:9",  // "16:9", "9:16", "1:1", "4:3", "3:4"
    
    // NEW: Specify locations to use
    preferred_settings: [
      "coffee_shop",
      "home_office",
      "park_bench",
      "city_street",
      "gym"
    ]
  }
}
```

### Available Settings (100+ options)
**Home**: bedroom, kitchen, living_room, bathroom, balcony, rooftop  
**Public**: coffee_shop, library, bookstore, mall, gym, park  
**Work**: office, conference_room, classroom, lab, studio  
**Outdoor**: park, street, bus_stop, train_platform, beach, bridge  
**Transport**: car, bus, train, subway, bike  
**Social**: restaurant, bar, party, concert, picnic  
**Unique**: elevator, laundromat, gas_station, airport, thrift_store

---

## 8️⃣ Complete React Examples

### Full Job Flow Component
```jsx
import React, { useState, useEffect } from 'react';

function StoryboardGenerator() {
  const [jobId, setJobId] = useState(null);
  const [job, setJob] = useState(null);
  const [scenes, setScenes] = useState([]);
  const [loading, setLoading] = useState(false);

  const createJob = async (scriptText) => {
    setLoading(true);
    
    const response = await fetch('/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script_text: scriptText,
        generate_images: true,
        style_config: {
          aspect_ratio: "16:9",
          character_description: "content creator, casual"
        }
      })
    });
    
    const newJob = await response.json();
    setJobId(newJob.id);
    pollJob(newJob.id);
  };

  const pollJob = async (id) => {
    const response = await fetch(`/jobs/${id}`);
    const updatedJob = await response.json();
    setJob(updatedJob);
    
    if (updatedJob.status === 'completed') {
      loadScenes(id);
      setLoading(false);
    } else if (updatedJob.status !== 'failed') {
      setTimeout(() => pollJob(id), 2000);
    }
  };

  const loadScenes = async (id) => {
    const response = await fetch(`/scenes/job/${id}`);
    const sceneData = await response.json();
    setScenes(sceneData);
  };

  const editScene = async (sceneId, instruction) => {
    const response = await fetch(`/scenes/${sceneId}/regenerate-with-instruction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction })
    });
    
    const updatedScene = await response.json();
    setScenes(scenes.map(s => s.id === sceneId ? updatedScene : s));
  };

  const animateScene = async (sceneId) => {
    await fetch(`/scenes/${sceneId}/animate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aspect_ratio: "16:9" })
    });
    
    pollVideo(sceneId);
  };

  const pollVideo = async (sceneId) => {
    const response = await fetch(`/scenes/${sceneId}/video-status`);
    const scene = await response.json();
    
    setScenes(scenes.map(s => s.id === sceneId ? scene : s));
    
    if (scene.video_status === 'processing' || scene.video_status === 'pending') {
      setTimeout(() => pollVideo(sceneId), 5000);
    }
  };

  return (
    <div>
      <h1>YouTube Storyboard Generator</h1>
      
      {!jobId && (
        <ScriptInput onCreate={createJob} />
      )}
      
      {loading && (
        <div>
          <p>Status: {job?.status}</p>
          <p>Cost so far: ${job?.cost?.total_cost?.toFixed(4) || 0}</p>
        </div>
      )}
      
      {scenes.length > 0 && (
        <div className="scenes-grid">
          {scenes.map(scene => (
            <SceneCard
              key={scene.id}
              scene={scene}
              onEdit={editScene}
              onAnimate={animateScene}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SceneCard({ scene, onEdit, onAnimate }) {
  const [editMode, setEditMode] = useState(false);
  const [instruction, setInstruction] = useState('');

  const handleEdit = () => {
    onEdit(scene.id, instruction);
    setEditMode(false);
    setInstruction('');
  };

  return (
    <div className="scene-card">
      <img src={scene.image_url} alt={scene.sentence_text} />
      <p>{scene.sentence_text}</p>
      
      <div className="actions">
        {!editMode ? (
          <>
            <button onClick={() => setEditMode(true)}>Edit</button>
            <button
              onClick={() => onAnimate(scene.id)}
              disabled={scene.video_status === 'processing'}
            >
              {scene.video_status === 'generated' ? '✓ Video' : 
               scene.video_status === 'processing' ? 'Processing...' : 
               'Animate'}
            </button>
          </>
        ) : (
          <div>
            <input
              value={instruction}
              onChange={(e) => setInstruction(e.target.value)}
              placeholder="make the character smile"
            />
            <button onClick={handleEdit}>Apply</button>
            <button onClick={() => setEditMode(false)}>Cancel</button>
          </div>
        )}
      </div>
      
      {scene.video_status === 'generated' && (
        <video src={scene.video_url} controls />
      )}
      
      <small>Cost: ${scene.generation_cost?.toFixed(6) || 0}</small>
    </div>
  );
}

export default StoryboardGenerator;
```

---

## 🎬 B-Roll & Creative Visuals {#b-roll}

### What Changed?

**The character doesn't have to be in every scene!** The Director now creates more dynamic, creative visuals by mixing:

- **~40% Character Scenes**: Your main person talking, doing activities, reacting
- **~60% B-Roll Scenes**: Objects, environments, details, atmosphere - NO character visible

### Examples of B-Roll Scenes

The system will now automatically generate scenes like:

#### Object Close-ups
```
- Phone screen lighting up on a desk
- Coffee cup steaming
- Keyboard being typed on
- Book pages turning
- Clock showing time passing
```

#### Environmental Shots
```
- Empty street at dawn
- Rain streaming down a window
- City skyline at sunset
- Park bench under a tree
- Bedroom at night
```

#### Detail Shots (Hands/Feet Only)
```
- Hands typing (no face shown)
- Feet walking down a street
- Hand reaching for a door handle
- Fingers scrolling on phone
```

#### Atmospheric/Symbolic
```
- Shadows on a wall
- Reflections in water
- Light streaming through window
- Weather transitions
- Season changes
```

### How to Handle in UI

B-roll scenes will have an **empty `characters` array**:

```javascript
// Character scene
{
  "characters": [{
    "role": "main_character",
    "expression": { "primary": "thoughtful" },
    "pose": { "stance": "seated", "hand_position": "on_chin" }
  }],
  "setting": "bedroom at desk with laptop and coffee",
  "props": ["laptop", "coffee_cup", "notebook"]
}

// B-roll scene (NO character)
{
  "characters": [],  // ← Empty!
  "setting": "close-up of steaming coffee cup on wooden desk with morning light",
  "props": ["coffee_cup", "steam", "desk", "window_light"]
}
```

### UI Display Recommendations

```javascript
function SceneCard({ scene }) {
  const isCharacterScene = scene.visual_prompt?.characters?.length > 0;
  
  return (
    <div className="scene-card">
      {isCharacterScene ? (
        <div className="badge">Character Scene</div>
      ) : (
        <div className="badge b-roll">B-Roll</div>
      )}
      
      <img src={scene.image_url} alt={scene.sentence_text} />
      
      {isCharacterScene ? (
        <div>
          <p>Pose: {scene.visual_prompt.characters[0].pose.stance}</p>
          <p>Expression: {scene.visual_prompt.characters[0].expression.primary}</p>
        </div>
      ) : (
        <div>
          <p>Focus: Environmental / Objects</p>
          <p>Props: {scene.visual_prompt.props.join(', ')}</p>
        </div>
      )}
    </div>
  );
}
```

### Editing B-Roll Scenes

When using the edit assistant or text instructions for b-roll scenes:

```javascript
// B-roll edit examples
await editScene(sceneId, "zoom in closer on the coffee cup");
await editScene(sceneId, "add more steam and warmth");
await editScene(sceneId, "change to nighttime with city lights in background");
await editScene(sceneId, "make it look like early morning with soft light");

// The system won't try to add a character - it will stay b-roll
```

### Why This Improves Your Videos

1. **More Visual Variety**: Prevents every scene from looking the same
2. **Professional Polish**: Mimics real YouTube editing with cutaways
3. **Better Storytelling**: Shows what's being talked about, not just who's talking
4. **Smoother Pacing**: Gives viewers' eyes something new to look at
5. **Engagement**: Keeps the visual experience dynamic and interesting

---

## 🎯 Best Practices

### 1. Always Poll, Never Block
```javascript
// ❌ Bad: Blocking wait
await fetch('/jobs', { method: 'POST' });
await sleep(60000);  // Wait 1 minute

// ✅ Good: Poll with UI updates
const pollWithUI = async (jobId) => {
  while (true) {
    const job = await fetch(`/jobs/${jobId}`).then(r => r.json());
    updateUI(job.status);  // Show progress
    if (job.status === 'completed') break;
    await sleep(2000);
  }
};
```

### 2. Show Costs in Real-Time
```javascript
// Poll cost endpoint while job is running
useEffect(() => {
  if (jobStatus !== 'completed') {
    const interval = setInterval(async () => {
      const cost = await fetch(`/jobs/${jobId}/cost`).then(r => r.json());
      setCost(cost.total_cost);
    }, 2000);
    return () => clearInterval(interval);
  }
}, [jobId, jobStatus]);
```

### 3. Handle Errors Gracefully
```javascript
try {
  const scene = await editScene(id, instruction);
} catch (error) {
  if (error.status === 400) {
    showError("Invalid instruction. Try being more specific.");
  } else if (error.status === 503) {
    showError("Service temporarily unavailable. Try again in a moment.");
  } else {
    showError("Something went wrong. Please try again.");
  }
}
```

### 4. Optimize Data URIs
Video data URIs are LARGE (1-3 MB). Consider:
- Only load videos when user scrolls to them
- Store in IndexedDB for caching
- Offer download option instead of embedding all

```javascript
// Lazy load videos
<video
  src={scene.video_url}
  loading="lazy"
  onLoadStart={() => console.log('Loading video...')}
/>
```

---

## 🐛 Common Issues & Solutions

### Issue: "Job stuck in 'pending'"
**Solution**: Check backend logs. Usually means OPENAI_API_KEY or GOOGLE_GEMINI_API_KEY is missing.

### Issue: "Image not displaying"
**Solution**: Check that `image_url` starts with `data:image/png;base64,`. If it's just base64, prepend the prefix.

### Issue: "Video generation fails"
**Solution**: Check `scene.last_error`. Common causes:
- Scene has no image (generate image first)
- Veo safety filters blocked the content
- Invalid aspect ratio (use "16:9" or "9:16")

### Issue: "Costs not updating"
**Solution**: Poll `/jobs/{id}/cost` instead of `/jobs/{id}`. The cost endpoint updates in real-time.

---

## 📞 Support

Backend runs on: `http://localhost:8000`  
API docs: `http://localhost:8000/docs`  

If something's not working, check the backend logs in the terminal where you ran `python run.py`.

---

That's everything! 🎉
