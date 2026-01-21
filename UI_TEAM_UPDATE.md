# 🚀 UI Team - Major Backend Updates

## What Changed

We rebuilt the entire visual generation system with **3 major upgrades**:

1. **🎬 Director Architecture** - AI now analyzes narrative BEFORE making images
2. **🎨 Custom Styles** - Full control over art style, lighting, character, etc.
3. **🧙‍♂️ Wizard Mode** - Step-by-step approval flow for better UX

---

## TL;DR - Quick Summary

### Before:
```
Upload Script → Generate Images → Done
```

### Now:
```
Upload Script 
   ↓
Director Analyzes (creates scene plans)
   ↓
USER REVIEWS & APPROVES ← NEW STEP!
   ↓
Generate Images → Done
```

**Why?** Users can now see and edit the AI's plan BEFORE wasting money on images.

---

## 🎬 Part 1: Director Architecture

### The Problem We Solved

**Before:** Every scene looked the same - same camera, same pose, same emotion.

**Why?** AI was guessing. No narrative understanding.

**Now:** AI analyzes the story first, then creates varied visuals.

### The 3-Layer System

```
📝 Script Sentence
      ↓
🎬 DIRECTOR (analyzes: "What's happening emotionally?")
      ↓
🎥 CINEMATOGRAPHER (translates: "How do we show this?")
      ↓
🖼️ RENDERER (Gemini generates the actual image)
```

### What This Means for UI

**Each scene now has TWO things:**

1. **scene_plan** - Director's analysis (narrative, emotion, camera intent)
2. **visual_prompt** - Cinematographer's detailed instructions (for image rendering)

**Example Scene Response:**
```json
{
  "id": "scene-123",
  "sentence_text": "I felt disconnected.",
  "scene_plan": {
    "narrative_role": "emotional_low_point",
    "emotional_tone": "detached",
    "energy_level": "low",
    "visual_focus": "internal_state",
    "camera_intent": {
      "shot": "close_up",
      "angle": "eye_level",
      "framing": "off_center"
    },
    "props": [
      { "type": "window", "symbolism": "isolation" }
    ],
    "setting": {
      "location": "interior",
      "environment": "quiet_room_near_window",
      "symbolic_elements": ["window", "shadows"]
    }
  },
  "visual_prompt": {
    "characters": [...],
    "composition": {...},
    ...
  },
  "image_url": "data:image/png;base64,...",
  "image_status": "generated"
}
```

---

## 🧙‍♂️ Part 2: Wizard Mode (NEW USER FLOW)

### The Experience

Instead of one big "Generate" button, users now go through steps:

#### **Step 1: Upload Script**
User pastes script, selects style preferences.

#### **Step 2: Review Director's Plans** ⭐ NEW!
- User sees what the AI planned for each scene
- Can edit emotional tone, camera angle, props
- Can approve individual scenes or all at once

#### **Step 3: Generate Visuals**
After approval, cinematographer + image renderer create the final result.

---

## 🎯 Part 3: New API Flow

### Option A: Wizard Mode (Recommended)

#### 1. Create Job with Wizard Mode

```javascript
POST /jobs
{
  "script_text": "Your script...",
  "wizard_mode": true,  // ← NEW! Enables step-by-step
  "generate_images": true,
  "style_config": {
    "art_style": "realistic",
    "lighting": "natural_lighting",
    "character_description": "tech YouTuber, hoodie, friendly"
  }
}

// Response
{
  "id": "job-123",
  "status": "analyzing_script",  // Director working
  ...
}
```

#### 2. Poll Until Ready for Review

```javascript
// Keep checking job status
GET /jobs/job-123

// When ready, status changes to:
{
  "id": "job-123",
  "status": "awaiting_approval",  // ← Paused, waiting for user
  "scene_ids": ["scene-1", "scene-2", ...],
  ...
}
```

#### 3. Get Director's Scene Plans

```javascript
GET /jobs/job-123/director-plans

// Response
{
  "job_id": "job-123",
  "status": "awaiting_approval",
  "scenes": [
    {
      "id": "scene-1",
      "index": 0,
      "sentence": "I felt disconnected.",
      "scene_plan": {
        "narrative_role": "emotional_low_point",
        "emotional_tone": "detached",
        "energy_level": "low",
        "camera_intent": { "shot": "close_up", ... },
        "props": [{ "type": "window", "symbolism": "isolation" }],
        "setting": { "environment": "quiet_room_near_window" }
      }
    },
    // ... more scenes
  ]
}
```

#### 4. (Optional) Edit a Scene Plan

```javascript
PATCH /scenes/scene-1/scene-plan
{
  "scene_plan": {
    "emotional_tone": "hopeful",  // User changed this
    "camera_intent": {
      "shot": "medium_shot"  // User changed this
    }
  }
}
```

#### 5. Approve & Continue

```javascript
POST /jobs/job-123/approve

// Job continues:
// "generating_visuals" → "generating_images" → "completed"
```

#### 6. Get Final Results

```javascript
GET /scenes/job/job-123

// All scenes with visual_prompts and images
```

---

### Option B: Auto Mode (Skip Wizard)

For users who want speed over control:

```javascript
POST /jobs
{
  "script_text": "Your script...",
  "wizard_mode": false,  // ← Skip approval step
  "generate_images": true
}

// Goes straight through:
// pending → analyzing_script → generating_visuals → completed
```

---

## 📊 Part 4: Job Statuses

### New Status Flow

```
pending
   ↓
analyzing_script (Director working)
   ↓
awaiting_approval (Paused - waiting for user) ← NEW!
   ↓
generating_visuals (Cinematographer working)
   ↓
generating_images (Renderer working)
   ↓
completed
```

### What Each Status Means

| Status | What's Happening | What UI Should Show |
|--------|------------------|---------------------|
| `pending` | Job created | "Starting..." |
| `analyzing_script` | Director analyzing narrative | "🎬 Analyzing your script..." |
| `awaiting_approval` | Waiting for user to approve | "✋ Review scene plans" (show review UI) |
| `generating_visuals` | Cinematographer creating prompts | "🎥 Creating visual prompts..." |
| `generating_images` | Gemini generating images | "🖼️ Generating images... X/Y complete" |
| `completed` | Done! | "✅ Complete! View storyboard" |
| `failed` | Error occurred | "❌ Error: {error_message}" |

---

## 💻 Part 5: UI Implementation

### Complete Wizard Flow Component

```jsx
import React, { useState, useEffect } from 'react';

export function StoryboardWizard() {
  const [step, setStep] = useState(1);
  const [jobId, setJobId] = useState(null);
  const [job, setJob] = useState(null);
  
  return (
    <div className="wizard-container">
      {/* Progress Steps */}
      <WizardProgress currentStep={step} />
      
      {/* Step Content */}
      {step === 1 && (
        <ScriptUpload 
          onJobCreated={(id) => {
            setJobId(id);
            setStep(2);
          }} 
        />
      )}
      
      {step === 2 && (
        <DirectorReview 
          jobId={jobId}
          onApprove={() => setStep(3)}
        />
      )}
      
      {step === 3 && (
        <GenerationProgress 
          jobId={jobId}
          onComplete={(completedJob) => {
            setJob(completedJob);
            setStep(4);
          }}
        />
      )}
      
      {step === 4 && (
        <StoryboardViewer job={job} />
      )}
    </div>
  );
}

// Step 1: Upload Script
function ScriptUpload({ onJobCreated }) {
  const [script, setScript] = useState('');
  const [styleConfig, setStyleConfig] = useState({
    art_style: 'realistic',
    lighting: 'natural_lighting',
    character_description: ''
  });
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async () => {
    setLoading(true);
    
    const response = await fetch('http://localhost:8000/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script_text: script,
        wizard_mode: true,  // ← Enable wizard
        generate_images: true,
        style_config: styleConfig
      })
    });
    
    const job = await response.json();
    onJobCreated(job.id);
  };
  
  return (
    <div className="step-upload">
      <h2>Step 1: Upload Your Script</h2>
      
      <textarea
        value={script}
        onChange={(e) => setScript(e.target.value)}
        placeholder="Paste your script here..."
        rows={10}
      />
      
      <StyleSelector 
        value={styleConfig}
        onChange={setStyleConfig}
      />
      
      <button onClick={handleSubmit} disabled={loading || !script}>
        {loading ? 'Analyzing...' : 'Start Analysis'}
      </button>
    </div>
  );
}

// Step 2: Review Director's Plans
function DirectorReview({ jobId, onApprove }) {
  const [scenes, setScenes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [approving, setApproving] = useState(false);
  
  useEffect(() => {
    pollUntilReady();
  }, [jobId]);
  
  const pollUntilReady = async () => {
    const interval = setInterval(async () => {
      const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
      const job = await response.json();
      
      if (job.status === 'awaiting_approval') {
        clearInterval(interval);
        await loadScenePlans();
      }
    }, 2000);
  };
  
  const loadScenePlans = async () => {
    const response = await fetch(`http://localhost:8000/jobs/${jobId}/director-plans`);
    const data = await response.json();
    setScenes(data.scenes);
    setLoading(false);
  };
  
  const handleApprove = async () => {
    setApproving(true);
    await fetch(`http://localhost:8000/jobs/${jobId}/approve`, {
      method: 'POST'
    });
    onApprove();
  };
  
  if (loading) {
    return (
      <div className="loading-state">
        <h2>🎬 Director Analyzing Your Script</h2>
        <p>Analyzing narrative, emotions, and visual direction...</p>
      </div>
    );
  }
  
  return (
    <div className="step-review">
      <h2>Step 2: Review Director's Plans</h2>
      <p>The AI Director has analyzed your script and created a plan for each scene.</p>
      
      <div className="scenes-grid">
        {scenes.map((scene) => (
          <ScenePlanCard 
            key={scene.id}
            scene={scene}
            onEdit={(updated) => updateScenePlan(scene.id, updated)}
          />
        ))}
      </div>
      
      <div className="approve-section">
        <button 
          onClick={handleApprove}
          disabled={approving}
          className="approve-btn"
        >
          {approving ? 'Approving...' : '✓ Approve & Generate Visuals'}
        </button>
      </div>
    </div>
  );
}

// Scene Plan Card
function ScenePlanCard({ scene, onEdit }) {
  const plan = scene.scene_plan;
  
  return (
    <div className="scene-plan-card">
      <div className="card-header">
        <span className="scene-number">Scene {scene.index + 1}</span>
      </div>
      
      <div className="scene-sentence">
        "{scene.sentence}"
      </div>
      
      <div className="plan-details">
        <DetailRow 
          label="Narrative" 
          value={plan.narrative_role}
          badge="primary"
        />
        <DetailRow 
          label="Emotion" 
          value={plan.emotional_tone}
          badge="emotion"
        />
        <DetailRow 
          label="Energy" 
          value={plan.energy_level}
          badge="energy"
        />
        <DetailRow 
          label="Camera" 
          value={`${plan.camera_intent.shot} • ${plan.camera_intent.framing}`}
        />
        
        {plan.props.length > 0 && (
          <div className="detail-row">
            <label>Props:</label>
            <div className="props-list">
              {plan.props.map((prop, idx) => (
                <span key={idx} className="prop-tag">
                  {prop.type}
                  {prop.symbolism && <small>({prop.symbolism})</small>}
                </span>
              ))}
            </div>
          </div>
        )}
        
        <DetailRow 
          label="Setting" 
          value={plan.setting.environment}
        />
      </div>
    </div>
  );
}

function DetailRow({ label, value, badge }) {
  return (
    <div className="detail-row">
      <label>{label}:</label>
      {badge ? (
        <span className={`badge badge-${badge}`}>{value}</span>
      ) : (
        <span>{value}</span>
      )}
    </div>
  );
}

// Step 3: Generation Progress
function GenerationProgress({ jobId, onComplete }) {
  const [status, setStatus] = useState('');
  const [progress, setProgress] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(async () => {
      const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
      const job = await response.json();
      
      setStatus(job.status);
      
      if (job.status === 'generating_images') {
        // Calculate image progress
        const scenesResponse = await fetch(`http://localhost:8000/scenes/job/${jobId}`);
        const scenes = await scenesResponse.json();
        const completed = scenes.filter(s => s.image_status === 'generated').length;
        setProgress((completed / scenes.length) * 100);
      }
      
      if (job.status === 'completed') {
        clearInterval(interval);
        onComplete(job);
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [jobId]);
  
  return (
    <div className="step-progress">
      <h2>Step 3: Generating Your Storyboard</h2>
      
      <div className="status-indicator">
        {status === 'generating_visuals' && (
          <div>🎥 Creating detailed visual prompts...</div>
        )}
        {status === 'generating_images' && (
          <div>🖼️ Generating images ({Math.round(progress)}% complete)</div>
        )}
      </div>
      
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}

// Style Selector Component
function StyleSelector({ value, onChange }) {
  return (
    <div className="style-selector">
      <h3>Visual Style</h3>
      
      <label>
        Art Style:
        <select 
          value={value.art_style}
          onChange={(e) => onChange({ ...value, art_style: e.target.value })}
        >
          <option value="realistic">Realistic</option>
          <option value="anime_style">Anime</option>
          <option value="cartoon">Cartoon</option>
          <option value="minimalist">Minimalist</option>
        </select>
      </label>
      
      <label>
        Lighting:
        <select 
          value={value.lighting}
          onChange={(e) => onChange({ ...value, lighting: e.target.value })}
        >
          <option value="natural_lighting">Natural</option>
          <option value="dramatic_lighting">Dramatic</option>
          <option value="soft_even_studio_lighting">Studio</option>
        </select>
      </label>
      
      <label>
        Character Description:
        <input 
          type="text"
          value={value.character_description}
          onChange={(e) => onChange({ ...value, character_description: e.target.value })}
          placeholder="e.g., tech YouTuber, hoodie, friendly smile"
        />
      </label>
    </div>
  );
}
```

---

## 🎨 Part 6: CSS Styling

```css
/* Wizard Container */
.wizard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

/* Scene Plan Card */
.scene-plan-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
}

.scene-plan-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.scene-number {
  font-weight: 600;
  color: #1a73e8;
}

.scene-sentence {
  font-style: italic;
  color: #5f6368;
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-left: 3px solid #1a73e8;
}

.detail-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  align-items: center;
}

.detail-row label {
  font-weight: 500;
  color: #5f6368;
  min-width: 80px;
}

.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.badge-primary {
  background: #e8f0fe;
  color: #1a73e8;
}

.badge-emotion {
  background: #fce8e6;
  color: #d93025;
}

.badge-energy {
  background: #e6f4ea;
  color: #1e8e3e;
}

.prop-tag {
  display: inline-block;
  padding: 4px 8px;
  background: #f1f3f4;
  border-radius: 4px;
  margin-right: 8px;
  font-size: 13px;
}

.prop-tag small {
  color: #5f6368;
  margin-left: 4px;
}

/* Scenes Grid */
.scenes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin: 20px 0;
}

/* Approve Button */
.approve-btn {
  background: #1a73e8;
  color: white;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  width: 100%;
  max-width: 400px;
}

.approve-btn:hover {
  background: #1557b0;
}

.approve-btn:disabled {
  background: #dadce0;
  cursor: not-allowed;
}

/* Progress Bar */
.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin: 20px 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #1a73e8, #4285f4);
  transition: width 0.3s ease;
}
```

---

## 📋 Part 7: Quick Checklist

### To Implement Wizard Mode:

- [ ] Add wizard progress indicator (4 steps)
- [ ] Create ScriptUpload component
- [ ] Create DirectorReview component with scene plan cards
- [ ] Add polling logic for status changes
- [ ] Create GenerationProgress component
- [ ] Handle all 7 job statuses
- [ ] Add "Approve" button and endpoint call
- [ ] Style scene plan cards (badges for emotion, camera, etc.)
- [ ] Add scene plan editing (optional for v1)

### To Support Custom Styles:

- [ ] Add style selector dropdowns
- [ ] Include `style_config` in job creation
- [ ] Allow users to save favorite styles

---

## 💰 Part 8: Cost Display

```jsx
function CostTracker({ job }) {
  if (!job.cost) return null;
  
  return (
    <div className="cost-tracker">
      <h4>💰 Cost: ${job.cost.total_cost.toFixed(4)}</h4>
      <div className="cost-breakdown">
        <div>Director: ${(job.cost.prompt_generation_cost * 0.3).toFixed(4)}</div>
        <div>Cinematographer: ${(job.cost.prompt_generation_cost * 0.7).toFixed(4)}</div>
        <div>Images: ${job.cost.image_generation_cost.toFixed(4)}</div>
      </div>
      <small>
        {job.cost.num_prompts_generated} scenes • 
        {job.cost.num_images_generated} images
      </small>
    </div>
  );
}
```

---

## 🚦 Part 9: Status Indicators

```jsx
function JobStatusIndicator({ status }) {
  const statusConfig = {
    pending: { icon: '⏳', text: 'Starting...', color: '#757575' },
    analyzing_script: { icon: '🎬', text: 'Director analyzing', color: '#1a73e8' },
    awaiting_approval: { icon: '✋', text: 'Ready for review', color: '#f9ab00' },
    generating_visuals: { icon: '🎥', text: 'Creating visuals', color: '#1a73e8' },
    generating_images: { icon: '🖼️', text: 'Generating images', color: '#1a73e8' },
    completed: { icon: '✅', text: 'Complete!', color: '#1e8e3e' },
    failed: { icon: '❌', text: 'Failed', color: '#d93025' }
  };
  
  const config = statusConfig[status] || statusConfig.pending;
  
  return (
    <div className="status-indicator" style={{ color: config.color }}>
      <span className="status-icon">{config.icon}</span>
      <span className="status-text">{config.text}</span>
    </div>
  );
}
```

---

## ⚡ Part 10: Quick Start

### Simplest Implementation (Auto Mode):

If you want to skip wizard mode initially:

```jsx
// Just create job without wizard_mode
const job = await createJob({
  script_text: script,
  wizard_mode: false,  // Skip review step
  generate_images: true
});

// Poll until completed
// Then show results
```

### Full Wizard (Recommended):

Use the complete `StoryboardWizard` component from Part 5 above.

---

## 📞 Questions?

- **Director Architecture:** See `DIRECTOR_ARCHITECTURE.md`
- **Custom Styles:** See `CUSTOM_STYLE_GUIDE.md`
- **Cost Tracking:** See `COST_TRACKING.md`
- **Wizard Implementation Details:** See `WIZARD_MODE_IMPLEMENTATION.md`

---

## 🎯 Summary

✅ **Director analyzes narrative** - Better variety, symbolic props  
✅ **Wizard mode** - User approves before images  
✅ **Custom styles** - Full control over visuals  
✅ **Cost tracking** - See exactly what you're spending  

All backward compatible - existing code still works!

**Ready to build!** 🚀
