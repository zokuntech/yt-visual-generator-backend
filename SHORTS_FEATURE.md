# 🎬 YouTube Shorts Feature - Timelapse/Transformation Content

**NEW FEATURE**: Generate viral "satisfying" YouTube Shorts with NO narration/script needed!

## ⚡ Quick Summary

This tool generates:
- ✅ **6 keyframe images** (Empty → Prep → Installation → Finishing → Complete → Furnished)
- ✅ **CONSISTENT VISUALS**: Same camera angle, same room, same lighting across all stages
- ✅ **5 detailed transition prompts** (150-300 words each describing motion & continuity)
- ✅ **MORE PEOPLE**: Stages 2, 3, 4 feature 2-4 workers actively working
- ✅ **Ready to export** for use with Runway, Pika, Kling, or any video tool
- 💰 **Cost**: ~$0.10-0.15 per short (much cheaper than built-in video generation)

---

## 🎯 What Is This?

A completely separate workflow from the script-based storyboards. This generates visual-only content perfect for:

- **Epoxy flooring installations** (satisfying transformations)
- **Furniture building** (woodworking, construction)
- **Room renovations** (before/after reveals)
- **Crafting & making** (any satisfying process)
- **Construction timelapses** (multi-stage builds)

### Key Differences from Script Feature

| Script-Based Storyboards | Shorts/Timelapse |
|---------------------------|------------------|
| Requires text narration | **NO narration needed** |
| Character-driven scenes | **Process & transformation driven** |
| Dialogue & expressions | **Visual progression only** |
| Many short scenes | **4 keyframe stages** |
| 16:9 landscape | **9:16 vertical (Shorts)** |
| Video generation included | **Prompts only** (export for external tools) |

---

## 🔄 The Workflow

```
1. POST /shorts/concepts
   ↓ Returns 10 transformation ideas
   ↓ User selects one (index 0-9)
   
2. POST /shorts/create (with concept_index)
   ↓ Generates 6-stage image prompts
   ↓ Generates 5 transition prompts (text descriptions)
   ↓ Creates images in background
   
3. GET /shorts/{id} (poll until images done)
   ↓ Stage 1: Empty/Before (image + prompt)
   ↓ Stage 2: Prep Work - 2-3 workers (image + prompt)
   ↓ Stage 3: Active Installation - 3-4 workers 👷 (image + prompt)
   ↓ Stage 4: Finishing Touches - 2-3 workers (image + prompt)
   ↓ Stage 5: Completed Empty (image + prompt)
   ↓ Stage 6: Furnished/Final (image + prompt)
   ↓
   ↓ PLUS 5 transition prompts:
   ↓ Transition 1: Empty → Prep (workers entering)
   ↓ Transition 2: Prep → Installation (main work begins)
   ↓ Transition 3: Installation → Finishing (hero moment completing)
   ↓ Transition 4: Finishing → Complete (workers exiting)
   ↓ Transition 5: Complete → Furnished (styling reveal)
   
4. Export and use!
   ↓ Use the 6 images as keyframes
   ↓ Use the 5 transition prompts for video generation (external tool)
```

---

## 📡 API Endpoints

### 1. Generate Concepts

**`POST /shorts/concepts`**

Get 10 transformation ideas to choose from.

```javascript
const response = await fetch('/shorts/concepts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    category: "epoxy_flooring",  // or "furniture_build", "room_renovation", etc.
    num_concepts: 10
  })
});

const data = await response.json();
// {
//   concepts: [
//     {
//       index: 0,
//       title: "Modern Kitchen Epoxy Floor",
//       description: "A spacious contemporary kitchen with island...",
//       category: "epoxy_flooring"
//     },
//     ... 9 more
//   ],
//   cost: 0.0234,
//   message: "Please select one concept (index 0-9) to develop."
// }
```

**Available Categories:**
- `"epoxy_flooring"` - Artistic floor installations
- `"furniture_build"` - Building tables, chairs, etc.
- `"room_renovation"` - Complete room transformations
- `"painting"` - Painting projects
- `"woodworking"` - Wood crafting
- `"concrete_pouring"` - Concrete work
- `"crafting"` - General crafting
- `"food_preparation"` - Cooking/food content
- `"custom"` - Any satisfying process

---

### 2. Create Short Project

**`POST /shorts/create`**

Creates a short project from a selected concept.

```javascript
const response = await fetch('/shorts/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    category: "epoxy_flooring",
    concept_index: 2,  // User selected concept #2
    aspect_ratio: "9:16"  // Vertical for Shorts (or "16:9" for landscape)
  })
});

const project = await response.json();
// {
//   id: "abc-123-def",
//   category: "epoxy_flooring",
//   selected_concept: { ... },
//   room_type: "Modern Kitchen Epoxy Floor",
//   stages: [
//     { stage_number: 1, stage_type: "empty_room", image_status: "not_generated" ... },
//     { stage_number: 2, stage_type: "mid_construction", workers_present: true ... },
//     { stage_number: 3, stage_type: "completed_empty" ... },
//     { stage_number: 4, stage_type: "fully_furnished" ... }
//   ],
//   transitions: [ ... 3 transition prompts ... ],
//   status: "generating_images",
//   progress_percentage: 30,
//   total_cost: 0.0567
// }
```

**Alternative: Custom Description**

Instead of `concept_index`, you can provide a custom transformation:

```javascript
{
  category: "furniture_build",
  custom_description: "Building a walnut live-edge dining table from a raw slab...",
  aspect_ratio: "9:16"
}
```

---

### 3. Poll for Image Completion

**`GET /shorts/{project_id}`**

Poll this endpoint to check when all stage images are ready.

```javascript
const checkStatus = async (projectId) => {
  const response = await fetch(`/shorts/${projectId}`);
  const project = await response.json();
  
  console.log(`Status: ${project.status}`);
  console.log(`Progress: ${project.progress_percentage}%`);
  
  // Check if all images are done
  const allImagesReady = project.stages.every(
    stage => stage.image_status === "generated"
  );
  
  if (allImagesReady) {
    console.log("All images ready! Can now animate.");
    return project;
  }
  
  // Keep polling
  await sleep(3000);
  return checkStatus(projectId);
};
```

**Status Values:**
- `"pending"` - Just created
- `"generating_stages"` - Creating prompts
- `"generating_images"` - Creating images (poll here)
- `"completed"` - Images done, ready to animate
- `"failed"` - Something went wrong

---

### 4. Display Stage Images

Each stage has an `image_url` (data URI) once generated:

```javascript
function StageGallery({ project, onRegenerateStage, onEditStage }) {
  const [editingStage, setEditingStage] = useState(null);
  const [editInstruction, setEditInstruction] = useState("");

  const handleEdit = async (stageNumber) => {
    if (!editInstruction.trim()) return;
    
    await onEditStage(stageNumber, editInstruction);
    setEditingStage(null);
    setEditInstruction("");
  };

  return (
    <div className="stages-grid">
      {project.stages.map((stage) => (
        <div key={stage.id} className="stage-card">
          <h3>Stage {stage.stage_number}: {stage.stage_type}</h3>
          
          {stage.image_status === "generated" ? (
            <>
              <img 
                src={stage.image_url} 
                alt={`Stage ${stage.stage_number}`}
                style={{ aspectRatio: project.aspect_ratio.replace(':', '/') }}
              />
              
              <div className="stage-actions">
                <button 
                  onClick={() => onRegenerateStage(stage.stage_number)}
                  className="btn-regenerate"
                >
                  🔄 Regenerate
                </button>
                <button 
                  onClick={() => setEditingStage(stage.stage_number)}
                  className="btn-edit"
                >
                  ✏️ Edit
                </button>
              </div>
              
              {editingStage === stage.stage_number && (
                <div className="edit-form">
                  <input
                    type="text"
                    value={editInstruction}
                    onChange={(e) => setEditInstruction(e.target.value)}
                    placeholder="e.g., make the floor more blue, add more workers..."
                  />
                  <button onClick={() => handleEdit(stage.stage_number)}>
                    Apply
                  </button>
                  <button onClick={() => setEditingStage(null)}>
                    Cancel
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="loading">Generating...</div>
          )}
          
          {stage.workers_present && (
            <span className="badge">👷 Workers Present</span>
          )}
          
          <p className="description">
            {stage.detailed_description.substring(0, 150)}...
          </p>
          
          <small>Cost: ${stage.image_generation_cost.toFixed(4)}</small>
        </div>
      ))}
    </div>
  );
}
```

---

### 5. Animate Transitions

**`POST /shorts/{project_id}/animate`**

Once all images are ready, start video generation.

```javascript
const response = await fetch(`/shorts/${projectId}/animate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_id: projectId,
    generate_all: true  // Generate all 3 transitions
  })
});

const project = await response.json();
// status: "generating_videos"
// transitions[0].video_status: "processing"
// transitions[1].video_status: "processing"
// transitions[2].video_status: "processing"
```

---

### 6. Poll for Video Completion

**`GET /shorts/{project_id}/transition/{transition_number}/status`**

Poll each transition individually (1, 2, 3).

```javascript
const checkTransitionStatus = async (projectId, transitionNumber) => {
  const response = await fetch(
    `/shorts/${projectId}/transition/${transitionNumber}/status`
  );
  const project = await response.json();
  
  const transition = project.transitions.find(
    t => t.transition_number === transitionNumber
  );
  
  if (transition.video_status === "generated") {
    console.log(`✅ Transition ${transitionNumber} done!`);
    return transition.video_url;
  } else if (transition.video_status === "failed") {
    console.error(`❌ Transition ${transitionNumber} failed`);
    return null;
  }
  
  // Still processing
  console.log(`⏳ Transition ${transitionNumber} processing...`);
  await sleep(5000);
  return checkTransitionStatus(projectId, transitionNumber);
};

// Poll all 3 transitions
const [video1, video2, video3] = await Promise.all([
  checkTransitionStatus(projectId, 1),
  checkTransitionStatus(projectId, 2),
  checkTransitionStatus(projectId, 3)
]);
```

**Video Status Values:**
- `"not_generated"` - Not started
- `"processing"` - Being generated (poll here)
- `"generated"` - Done! (video_url available)
- `"failed"` - Generation failed

---

## 🎨 The 6-Stage Transformation

Every short follows this structure with MORE people and MORE detail:

### Stage 1: Empty/Before
- **Raw, unfinished state**
- Bare concrete floors, exposed walls
- Construction debris, dust, cracks
- "Before" condition
- **NO workers, NO people**
- Full of potential
- **Duration in final video**: ~2-3 seconds

### Stage 2: Prep Work 👷
- **2-3 workers preparing**
- Workers in full safety gear (hard hats, vests, boots)
- Grinding, measuring, marking surface
- Prep equipment visible (grinders, vacuums, tape)
- Dust in air, active preparation
- Focused, organized energy
- **Duration in final video**: ~3-4 seconds

### Stage 3: Active Installation 👷‍♀️👷👷‍♂️ (HERO SHOT!)
- **3-4 workers collaborating**
- **Main transformation moment** (e.g., pouring epoxy)
- One pouring, another spreading, others preparing
- Most dynamic and energetic scene
- Tools in use, materials being applied
- Liquid epoxy visible (if applicable)
- **Duration in final video**: ~5-6 seconds

### Stage 4: Finishing Touches 👷
- **2-3 workers doing detail work**
- Quality checking, smoothing, perfecting
- Nearly complete, final adjustments
- Workers cleaning up equipment
- Calmer but focused atmosphere
- Transition from build to reveal
- **Duration in final video**: ~3-4 seconds

### Stage 5: Completed (Empty)
- **Main transformation complete**
- Finished floor/product, pristine
- Maybe 1 worker admiring or completely empty
- NO furniture yet
- Showcase quality, ready for reveal
- **Duration in final video**: ~3-4 seconds

### Stage 6: Fully Furnished
- **Final styled version**
- Furniture, decor, lived-in feel
- Complete transformation
- "After" reveal
- **Duration in final video**: ~3-4 seconds

**Total video length**: ~20-25 seconds (perfect for Shorts!)
**Total people shown**: 7-10 workers across stages 2, 3, 4

---

## 🎯 Visual Consistency (How It Works)

### The "Room Anchor"
Every project establishes a "room anchor" that remains constant across all 6 stages:
- **Camera Position**: e.g., "wide angle from doorway, eye-level, capturing entire room"
- **Room Layout**: e.g., "20x15 foot rectangular space, window left wall, exposed brick right"
- **Lighting Setup**: e.g., "natural daylight from left window, overhead construction lights"

### What Changes (The Transformation)
- People entering/working/leaving
- Materials and tools appearing/being used
- Floor/product progressing from raw to finished
- Debris/cleanup happening

### What Stays the Same (The Consistency)
- ✅ Camera angle and framing
- ✅ Room dimensions and walls
- ✅ Window and door positions
- ✅ Lighting direction and sources
- ✅ Architectural features

This ensures all 6 images look like a **true timelapse** from the same camera!

---

## ✏️ Editing Stage Images

Don't like how a stage turned out? You can regenerate or edit any stage!

### Regenerate Stage (Same Prompt)

**`POST /shorts/{project_id}/stage/{stage_number}/regenerate`**

Regenerate a stage with the exact same prompt (useful if you just want a different variation).

```javascript
const response = await fetch(`/shorts/${projectId}/stage/2/regenerate`, {
  method: 'POST'
});

const updatedProject = await response.json();
// Stage 2 will have a new image_url with a fresh generation
```

### Edit Stage (Text Instruction)

**`POST /shorts/{project_id}/stage/{stage_number}/edit`**

Modify a stage using natural language instructions.

```javascript
const response = await fetch(`/shorts/${projectId}/stage/3/edit`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    instruction: "make the epoxy floor more blue and silver with less gold"
  })
});

const updatedProject = await response.json();
// Stage 3 now has edited image
```

**Example Edit Instructions:**

```javascript
// Stage 1 (Empty Room)
"add more construction debris / make it look dustier / darker lighting"

// Stage 2 (Mid-Construction)
"add more workers (need 4-5 people) / more tools visible / messier work site"

// Stage 3 (Completed Floor)
"make the epoxy more glossy / change colors to navy blue and copper / brighter reflections"

// Stage 4 (Furnished)
"add more furniture / change to modern minimalist style / warmer lighting"
```

**Cost Note:** Each regeneration or edit costs the same as generating a new image (~$0.01).

---

## 🎥 The 5 Transition Prompts

These are **detailed text descriptions** of how the stages should animate/transition. You can use these with any video generation tool (Runway, Pika, Kling, etc.).

### Transition 1: Empty → Prep Work
- **Suggested Duration**: 5-7 seconds
- **Describes**: 2-3 workers entering with equipment, setting up, beginning prep
- **Motion Style**: Timelapse pacing, workers arriving and starting
- **Camera**: Static angle (authentic timelapse)

### Transition 2: Prep Work → Active Installation
- **Suggested Duration**: 7-9 seconds
- **Describes**: More workers arriving, main work beginning, key moment starting
- **Motion Style**: Building energy, more people, main transformation begins
- **Camera**: Static angle

### Transition 3: Active Installation → Finishing Touches 🔥 (HERO TRANSITION)
- **Suggested Duration**: 8-10 seconds (longest, most dramatic)
- **Describes**: Main installation completing (e.g., epoxy pouring done), workers shifting to detail work
- **Motion Style**: Peak energy to focused finishing, most satisfying progression
- **Camera**: Static angle

### Transition 4: Finishing Touches → Completed
- **Suggested Duration**: 6-8 seconds
- **Describes**: Final touches completing, workers cleaning up and exiting, reveal of finished work
- **Motion Style**: Workers leaving, space transforming from work site to pristine
- **Camera**: Static angle

### Transition 5: Completed → Furnished
- **Suggested Duration**: 5-7 seconds
- **Describes**: Furniture appearing, decoration, styling, final transformation reveal
- **Motion Style**: Items being placed, room coming to life, final "after" moment
- **Camera**: Static angle

### Accessing Transition Prompts

```javascript
const project = await fetch(`/shorts/${projectId}`).then(r => r.json());

// project.transitions is an array of 5 objects
project.transitions.forEach((transition, index) => {
  console.log(`Transition ${transition.transition_number}`);
  console.log(`From: ${transition.from_stage} → To: ${transition.to_stage}`);
  console.log(`Duration: ${transition.duration_seconds} seconds`);
  console.log(`\nPrompt:\n${transition.motion_description}`);
  console.log('\n---\n');
});

// Example output:
// Transition 1
// From: empty_room → To: prep_work
// Duration: 6 seconds
// 
// Prompt:
// The scene opens from a wide-angle static camera position at the doorway, showing the entire 20x15 foot room.
// The concrete floor is bare and dusty, with the large window on the left wall casting natural light.
// As the timelapse begins, from the edges of the frame, 2-3 construction workers in high-visibility vests
// and hard hats enter, carrying grinding equipment...
// The camera never moves, maintaining the same perspective throughout.
// The window remains visible on the left, the exposed brick on the right stays constant.
// The scene ends with the same camera angle, now showing 2-3 workers actively grinding the floor...
// [150-300 words with explicit continuity markers]
```

### How Transition Prompts Maintain Consistency

Each transition prompt includes:
1. **Opening**: References the ending state of the previous stage
2. **Continuity markers**: Explicitly mentions what stays the same (camera, room, lighting)
3. **Motion**: Describes what's changing (people, work, materials)
4. **Closing**: References the starting state of the next stage

This structure helps video generation tools (Runway, Pika, Kling) create smooth, consistent transitions between your keyframe images!

---

## 💰 Cost Tracking

```javascript
function CostDisplay({ project }) {
  return (
    <div className="cost-breakdown">
      <h4>💰 Project Costs</h4>
      <div>Prompt Generation: ${project.prompt_generation_cost.toFixed(4)}</div>
      <div>Image Generation: ${project.image_generation_cost.toFixed(4)}</div>
      <div className="total">
        <strong>Total: ${project.total_cost.toFixed(4)}</strong>
      </div>
      
      <div className="details">
        <small>
          • Stage prompts (6): Included in prompt cost<br/>
          • Transition prompts (5): Included in prompt cost<br/>
          • Stage images (6): ${project.image_generation_cost.toFixed(4)}
        </small>
      </div>
    </div>
  );
}
```

**Estimated Costs (per short):**
- Concept generation: ~$0.02
- Stage prompts (6): ~$0.015
- Transition prompts (5): ~$0.012
- 6 stage images: ~$0.06 (6 × $0.01)
- **Total per short**: ~$0.10-0.15

**Much more affordable than video generation!** Use the prompts with your preferred video tool.

---

## 🎬 Complete React Example

```javascript
import React, { useState, useEffect } from 'react';

function ShortsGenerator() {
  const [step, setStep] = useState(1); // 1-5
  const [category, setCategory] = useState('epoxy_flooring');
  const [concepts, setConcepts] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(false);

  // STEP 1: Generate concepts
  const generateConcepts = async () => {
    setLoading(true);
    const response = await fetch('/shorts/concepts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, num_concepts: 10 })
    });
    const data = await response.json();
    setConcepts(data.concepts);
    setStep(2);
    setLoading(false);
  };

  // STEP 2: Create project
  const createProject = async () => {
    setLoading(true);
    const response = await fetch('/shorts/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        category,
        concept_index: selectedIndex,
        aspect_ratio: "9:16"
      })
    });
    const proj = await response.json();
    setProject(proj);
    setStep(3);
    setLoading(false);
    
    // Start polling for images
    pollForImages(proj.id);
  };

  // STEP 3: Poll for images
  const pollForImages = async (projectId) => {
    const interval = setInterval(async () => {
      const response = await fetch(`/shorts/${projectId}`);
      const proj = await response.json();
      setProject(proj);
      
      const allReady = proj.stages.every(s => s.image_status === 'generated');
      if (allReady) {
        clearInterval(interval);
        setStep(4);
      }
    }, 3000);
  };

  // STEP 4: Export prompts and images
  const exportProject = () => {
    // Prepare export data
    const exportData = {
      title: project.room_type,
      category: project.category,
      aspect_ratio: project.aspect_ratio,
      stages: project.stages.map(s => ({
        number: s.stage_number,
        type: s.stage_type,
        image_url: s.image_url,
        prompt: s.detailed_description
      })),
      transitions: project.transitions.map(t => ({
        number: t.transition_number,
        from: t.from_stage,
        to: t.to_stage,
        duration_seconds: t.duration_seconds,
        prompt: t.motion_description
      }))
    };
    
    // Download as JSON
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${project.room_type.replace(/\s+/g, '_')}_prompts.json`;
    a.click();
  };

  const copyTransitionPrompt = (transitionNumber) => {
    const transition = project.transitions.find(t => t.transition_number === transitionNumber);
    if (transition) {
      navigator.clipboard.writeText(transition.motion_description);
      alert(`Transition ${transitionNumber} prompt copied!`);
    }
  };

  // Edit handlers
  const handleRegenerateStage = async (stageNumber) => {
    setLoading(true);
    const response = await fetch(`/shorts/${project.id}/stage/${stageNumber}/regenerate`, {
      method: 'POST'
    });
    const updatedProject = await response.json();
    setProject(updatedProject);
    setLoading(false);
  };

  const handleEditStage = async (stageNumber, instruction) => {
    setLoading(true);
    const response = await fetch(`/shorts/${project.id}/stage/${stageNumber}/edit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction })
    });
    const updatedProject = await response.json();
    setProject(updatedProject);
    setLoading(false);
  };

  return (
    <div className="shorts-generator">
      <h1>🎬 Create YouTube Short</h1>
      
      {/* Step 1: Select Category */}
      {step === 1 && (
        <div>
          <h2>Step 1: Choose Category</h2>
          <select value={category} onChange={e => setCategory(e.target.value)}>
            <option value="epoxy_flooring">Epoxy Flooring</option>
            <option value="furniture_build">Furniture Building</option>
            <option value="room_renovation">Room Renovation</option>
            <option value="woodworking">Woodworking</option>
            <option value="custom">Custom</option>
          </select>
          <button onClick={generateConcepts}>Generate Ideas →</button>
        </div>
      )}
      
      {/* Step 2: Select Concept */}
      {step === 2 && (
        <div>
          <h2>Step 2: Choose Transformation</h2>
          {concepts.map((concept) => (
            <div 
              key={concept.index}
              className={`concept-card ${selectedIndex === concept.index ? 'selected' : ''}`}
              onClick={() => setSelectedIndex(concept.index)}
            >
              <h3>{concept.title}</h3>
              <p>{concept.description}</p>
            </div>
          ))}
          <button 
            onClick={createProject}
            disabled={selectedIndex === null}
          >
            Create Project →
          </button>
        </div>
      )}
      
      {/* Step 3: Generating Images */}
      {step === 3 && project && (
        <div>
          <h2>Step 3: Generating Stage Images...</h2>
          <div className="progress-bar">
            <div style={{ width: `${project.progress_percentage}%` }} />
          </div>
          <div className="stages">
            {project.stages.map(stage => (
              <div key={stage.id} className="stage-preview">
                <h4>Stage {stage.stage_number}</h4>
                {stage.image_status === 'generated' ? (
                  <>
                    <img src={stage.image_url} alt={`Stage ${stage.stage_number}`} />
                    <span className="checkmark">✓</span>
                  </>
                ) : (
                  <div className="spinner">⏳</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Step 4: Complete - Export */}
      {step === 4 && project && (
        <div>
          <h2>Step 4: All Images & Prompts Ready! 🎉</h2>
          
          {/* Stage Gallery with Edit Options */}
          <StageGallery 
            project={project}
            onRegenerateStage={handleRegenerateStage}
            onEditStage={handleEditStage}
          />
          
          {/* Transition Prompts Section */}
          <div className="transition-prompts">
            <h3>📝 Transition Prompts</h3>
            <p>Use these prompts with any video generation tool (Runway, Pika, Kling, etc.)</p>
            
            {project.transitions.map(transition => (
              <div key={transition.id} className="transition-card">
                <div className="transition-header">
                  <h4>
                    Transition {transition.transition_number}: 
                    {transition.from_stage.replace('_', ' ')} → {transition.to_stage.replace('_', ' ')}
                  </h4>
                  <span className="duration">{transition.duration_seconds}s</span>
                </div>
                
                <div className="prompt-box">
                  <pre>{transition.motion_description}</pre>
                </div>
                
                <button 
                  onClick={() => copyTransitionPrompt(transition.transition_number)}
                  className="btn-copy"
                >
                  📋 Copy Prompt
                </button>
              </div>
            ))}
          </div>
          
          {/* Export Section */}
          <div className="export-section">
            <h3>📥 Export</h3>
            <p>Total Cost: ${project.total_cost.toFixed(4)}</p>
            
            <button onClick={exportProject} className="btn-export">
              💾 Download All (JSON)
            </button>
            
            <div className="export-details">
              <p>Includes:</p>
              <ul>
                <li>✓ 6 stage images (as data URIs)</li>
                <li>✓ 6 stage prompts</li>
                <li>✓ 5 transition prompts</li>
                <li>✓ All metadata</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default ShortsGenerator;
```

---

## 🎯 Best Practices

### 1. Show Progress Clearly

Users need to see what's happening at each stage:
- "Generating concepts..."
- "Creating stage prompts..."
- "Generating image 2/4..."
- "Animating transition 1/3..."

### 2. Display All 4 Stages

Even while generating, show placeholders for all 4 stages so users understand the structure.

### 3. Cost Transparency

Always show the running cost. Shorts are more expensive than storyboard scenes (~$0.70-1.00 vs ~$0.05 per scene).

### 4. Video Previews

Once transition videos are ready, let users preview them before downloading/publishing.

### 5. Aspect Ratio Choice

Offer both 9:16 (Shorts) and 16:9 (landscape) options. Some users may want landscape timelapses.

---

## 🔧 Troubleshooting

### Images not generating

If stage images fail to generate, check:
- Gemini API key is valid
- Prompts aren't being blocked by safety filters (especially for Stage 2 with workers)
- Poll `/shorts/{id}` to check `image_status` for each stage

### Workers not appearing in Stage 2

Stage 2 should always have `workers_present: true`. If not, the timelapse director didn't follow the prompt correctly. Try regenerating the entire project.

### Transition prompts too vague

The transition prompts should be 150-300 words and very detailed. If they're too short or vague:
- The concept description might have been too simple
- Try creating a new project with a more detailed custom description

### Export not working

Make sure all 6 stage images are fully generated (`image_status: "generated"`) before exporting.

### Not enough people in stages 2-4

Stages 2, 3, and 4 should have 2-4 workers visible. Stage 3 (Active Installation) should have the most (3-4 workers). If workers aren't appearing, try regenerating the project or editing the specific stage with instruction: "add 3 workers in safety gear actively working".

### Images don't look consistent (different angles/rooms)

If the 6 stages don't look like they're from the same room:

**Problem**: The AI generated different camera angles or room layouts
**Solution**: 
1. Regenerate the entire project (sometimes the AI needs another try)
2. If issue persists, check the stage prompts - they should all reference the same "camera position" and "room features"
3. Use the edit feature to fix specific stages: "match the camera angle and room layout from stage 1"

**Best Practice**: When exporting, review all 6 images side-by-side. They should look like frames from a timelapse video of the same space.

### Transition videos don't match the images

If your video tool generates transitions that don't match:

**Problem**: The tool isn't respecting the keyframes or prompts
**Solution**:
1. Make sure you're uploading both start AND end images as keyframes
2. Use "image-to-image" or "frame interpolation" mode (not text-to-video)
3. Include the full transition prompt - don't truncate it
4. Try a different tool - Runway Gen-3 and Kling AI are good for consistency

---

## 🎬 Using Prompts with External Tools

The transition prompts are designed to work with any image-to-video or text-to-video tool:

### Recommended Tools:

**Image-to-Video (Frame Interpolation):**
- **Runway Gen-3**: Upload Stage 1 & 2 as start/end frames, paste transition prompt
- **Pika Labs**: Upload keyframes, use prompt for motion guidance
- **Kling AI**: Great for construction/timelapse content
- **Luma AI**: Good for smooth transitions

**Workflow:**
```
1. Export project from backend
2. Save all 6 stage images
3. For Transition 1:
   - Start frame: Stage 1 image
   - End frame: Stage 2 image
   - Prompt: transition.motion_description
4. Repeat for Transitions 2, 3, 4, & 5
5. Stitch 5 videos together in editor
6. Result: ~20-25 second transformation Short
```

### Tips for Best Results:

- **Use Keyframes**: Upload start and end images as keyframes (most tools support this)
- **Static Camera**: All prompts already specify "static camera, no movement"
- **Duration**: Use the suggested durations in each transition (5-10 seconds)
- **Aspect Ratio**: Use the same ratio as your images (9:16 or 16:9)
- **Same Tool**: Generate all 5 transitions with the same tool/settings for consistency
- **Reference Markers**: The prompts mention specific features (windows, walls) to help maintain continuity

---

## 🚀 Future Enhancements

Potential improvements for v2:

1. **Direct Tool Integration**: One-click export to Runway/Pika/Kling
2. **Templates**: Pre-made styles (modern, industrial, luxury)
3. **Batch Generation**: Create multiple shorts at once
4. **Custom Stages**: Allow 5-6 stages instead of just 4
5. **Prompt Refinement**: AI assistant to improve transition prompts
6. **Cost Optimizer**: Suggest cheaper alternatives for concepts

---

## 📞 Questions?

If you run into issues integrating this feature, check:

1. Are you polling until all images are generated before showing export?
2. Are you handling `image_status` correctly for each stage?
3. Are you displaying the transition prompts clearly (they can be long)?
4. Are data URIs working in your `<img>` tags?
5. Is the JSON export downloading correctly?

## 🎯 Workflow Summary

```
User Flow:
1. Choose category (epoxy_flooring, furniture_build, etc.)
2. Pick from 10 AI-generated concepts
3. Wait for 6 images to generate (~45-90 seconds)
4. View + edit any stage if needed
5. Export JSON with all images + prompts
6. Use in Runway/Pika/Kling to create 5 transition videos
7. Stitch together for final ~20-25 second Short
```

**Perfect for**: Epoxy floors, woodworking, construction, crafting, room renovations, and any satisfying transformation content!

**Now with MORE PEOPLE** - Stages 2, 3, 4 feature 2-4 workers for dynamic, engaging content! 👷‍♀️👷👷‍♂️

Good luck creating some viral Shorts! 🎬✨
