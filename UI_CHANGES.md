# 🎨 UI Integration Updates - Custom Styles & Cost Tracking

## What Changed

We added 2 major features to the API:

1. **Custom Style Configuration** - Full control over visual style
2. **Automatic Cost Tracking** - See API costs in real-time

Both are **backward compatible** - your existing code still works!

---

## 1. Custom Style Configuration

### Before (Still Works)

```javascript
const response = await fetch('http://localhost:8000/jobs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    script_text: "Your script...",
    generate_images: true
    // ← Uses default generic style
  })
});
```

### New (Recommended)

```javascript
const response = await fetch('http://localhost:8000/jobs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    script_text: "Your script...",
    generate_images: true,
    style_config: {
      art_style: "realistic",                    // User's choice
      lighting: "natural_lighting",              // User's choice
      color_palette: "warm_neutral",             // User's choice
      background: "modern_office",               // User's choice
      character_description: "tech YouTuber...", // User types this
      camera_angle: "medium_shot",               // User's choice
      framing: "centered"                        // User's choice
    }
  })
});
```

### What to Build in UI

Add style selection dropdowns/inputs:

```jsx
function StyleSelector({ value, onChange }) {
  return (
    <div className="style-selector">
      {/* Art Style */}
      <label>
        Art Style:
        <select 
          value={value.art_style}
          onChange={(e) => onChange({ ...value, art_style: e.target.value })}
        >
          <option value="realistic">Realistic</option>
          <option value="anime_style">Anime</option>
          <option value="cartoon">Cartoon</option>
          <option value="oil_painting">Oil Painting</option>
          <option value="minimalist">Minimalist</option>
        </select>
      </label>

      {/* Lighting */}
      <label>
        Lighting:
        <select 
          value={value.lighting}
          onChange={(e) => onChange({ ...value, lighting: e.target.value })}
        >
          <option value="natural_lighting">Natural Light</option>
          <option value="dramatic_lighting">Dramatic</option>
          <option value="soft_even_studio_lighting">Studio</option>
          <option value="golden_hour">Golden Hour</option>
        </select>
      </label>

      {/* Color Palette */}
      <label>
        Colors:
        <select 
          value={value.color_palette}
          onChange={(e) => onChange({ ...value, color_palette: e.target.value })}
        >
          <option value="warm_neutral">Warm & Neutral</option>
          <option value="vibrant">Vibrant</option>
          <option value="muted">Muted</option>
          <option value="monochrome">Black & White</option>
        </select>
      </label>

      {/* Background */}
      <label>
        Background:
        <select 
          value={value.background}
          onChange={(e) => onChange({ ...value, background: e.target.value })}
        >
          <option value="clean_simple">Clean & Simple</option>
          <option value="blurred">Blurred</option>
          <option value="office">Office</option>
          <option value="outdoor">Outdoor</option>
          <option value="studio">Studio</option>
        </select>
      </label>

      {/* Character Description */}
      <label>
        Your Character:
        <input
          type="text"
          value={value.character_description}
          onChange={(e) => onChange({ ...value, character_description: e.target.value })}
          placeholder="e.g., tech YouTuber, hoodie, glasses, friendly"
        />
      </label>

      {/* Camera Angle */}
      <label>
        Camera Angle:
        <select 
          value={value.camera_angle}
          onChange={(e) => onChange({ ...value, camera_angle: e.target.value })}
        >
          <option value="medium_shot">Medium Shot</option>
          <option value="close_up">Close Up</option>
          <option value="wide_shot">Wide Shot</option>
        </select>
      </label>

      {/* Framing */}
      <label>
        Framing:
        <select 
          value={value.framing}
          onChange={(e) => onChange({ ...value, framing: e.target.value })}
        >
          <option value="centered">Centered</option>
          <option value="rule_of_thirds">Rule of Thirds</option>
          <option value="dynamic">Dynamic</option>
        </select>
      </label>
    </div>
  );
}
```

### Complete Example

```jsx
function CreateJobForm() {
  const [scriptText, setScriptText] = useState('');
  const [styleConfig, setStyleConfig] = useState({
    art_style: 'realistic',
    lighting: 'natural_lighting',
    color_palette: 'warm_neutral',
    background: 'clean_simple',
    character_description: '',
    camera_angle: 'medium_shot',
    framing: 'centered'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_text: scriptText,
          generate_images: true,
          style_config: styleConfig
        })
      });
      
      const job = await response.json();
      console.log('Job created:', job.id);
      
      // Poll for completion
      pollJobStatus(job.id);
      
    } catch (error) {
      console.error('Error creating job:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea
        value={scriptText}
        onChange={(e) => setScriptText(e.target.value)}
        placeholder="Paste your script here..."
      />
      
      <StyleSelector 
        value={styleConfig}
        onChange={setStyleConfig}
      />
      
      <button onClick={handleSubmit} disabled={loading}>
        {loading ? 'Creating...' : 'Generate Storyboard'}
      </button>
    </div>
  );
}
```

---

## 2. Cost Tracking

### Response Now Includes Cost

Every job response now has a `cost` field:

```javascript
{
  "id": "job-123",
  "status": "completed",
  "script_text": "...",
  "cost": {
    "total_cost": 0.00621,              // Total in USD
    "prompt_generation_cost": 0.00045,   // OpenAI cost
    "image_generation_cost": 0.00576,    // Gemini cost
    "prompt_tokens_used": 3542,          // GPT tokens
    "image_tokens_used": 23220,          // Gemini tokens (approx)
    "num_prompts_generated": 18,         // Scenes
    "num_images_generated": 18           // Images
  },
  "scene_ids": [...],
  ...
}
```

### Display Cost in UI

```jsx
function JobCostDisplay({ job }) {
  if (!job.cost) return null;
  
  return (
    <div className="cost-display">
      <h3>💰 Cost: ${job.cost.total_cost.toFixed(4)}</h3>
      
      <div className="cost-breakdown">
        <div>
          <span>Prompts:</span>
          <span>${job.cost.prompt_generation_cost.toFixed(4)}</span>
        </div>
        <div>
          <span>Images:</span>
          <span>${job.cost.image_generation_cost.toFixed(4)}</span>
        </div>
      </div>
      
      <div className="usage-info">
        <small>
          {job.cost.num_prompts_generated} scenes • 
          {job.cost.num_images_generated} images
        </small>
      </div>
    </div>
  );
}
```

### Track Total Spending

```jsx
function Dashboard() {
  const [jobs, setJobs] = useState([]);
  
  useEffect(() => {
    // Fetch all jobs
    fetch('http://localhost:8000/jobs')
      .then(r => r.json())
      .then(data => setJobs(data));
  }, []);
  
  // Calculate totals
  const totalCost = jobs.reduce((sum, job) => sum + (job.cost?.total_cost || 0), 0);
  const totalVideos = jobs.length;
  const totalScenes = jobs.reduce((sum, job) => sum + (job.cost?.num_prompts_generated || 0), 0);
  
  return (
    <div className="dashboard">
      <h2>📊 Usage Stats</h2>
      <div className="stats">
        <div>Total Videos: {totalVideos}</div>
        <div>Total Scenes: {totalScenes}</div>
        <div>Total Cost: ${totalCost.toFixed(2)}</div>
        <div>Avg per Video: ${(totalCost / totalVideos).toFixed(4)}</div>
      </div>
      
      <div className="job-list">
        {jobs.map(job => (
          <div key={job.id} className="job-card">
            <h4>Job {job.id.slice(0, 8)}</h4>
            <JobCostDisplay job={job} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 3. Typical Costs

Show these to users for transparency:

```jsx
function CostEstimator({ scriptLength }) {
  // Rough estimate: ~150 words = ~10 scenes
  const estimatedScenes = Math.ceil(scriptLength / 150);
  const estimatedCost = estimatedScenes * 0.0005; // ~$0.0005 per scene
  
  return (
    <div className="cost-estimate">
      <p>📊 Estimated cost: ${estimatedCost.toFixed(4)}</p>
      <small>~{estimatedScenes} scenes</small>
    </div>
  );
}
```

**Typical costs to show users:**
- 60-second video: ~$0.005
- 3-minute video: ~$0.014
- 10-minute video: ~$0.047

---

## 4. Updated API Flow

### Complete Workflow with New Features

```jsx
async function generateStoryboard(scriptText, styleConfig) {
  // 1. Create job with custom style
  const createResponse = await fetch('http://localhost:8000/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_text: scriptText,
      generate_images: true,
      style_config: styleConfig  // ← Custom style
    })
  });
  
  const job = await createResponse.json();
  console.log('Job created:', job.id);
  console.log('Style:', job.options.style_config);
  
  // 2. Poll for completion
  let completed = false;
  while (!completed) {
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const statusResponse = await fetch(`http://localhost:8000/jobs/${job.id}`);
    const updatedJob = await statusResponse.json();
    
    console.log('Status:', updatedJob.status);
    console.log('Current cost:', updatedJob.cost?.total_cost); // ← Live cost updates
    
    if (updatedJob.status === 'completed') {
      completed = true;
      console.log('Final cost:', updatedJob.cost); // ← Final cost breakdown
    } else if (updatedJob.status === 'failed') {
      throw new Error(updatedJob.error_message);
    }
  }
  
  // 3. Fetch scenes
  const scenesResponse = await fetch(`http://localhost:8000/scenes/job/${job.id}`);
  const scenes = await scenesResponse.json();
  
  return { job, scenes };
}
```

---

## 5. Migration Guide

### If You're Already Using the API

**Option 1: Keep Current Code (No Changes Needed)**
```javascript
// This still works exactly as before
fetch('/jobs', {
  method: 'POST',
  body: JSON.stringify({
    script_text: "...",
    generate_images: true
  })
});
// Uses default generic style
```

**Option 2: Add Style Selection (Recommended)**
```javascript
// Add this to enable custom styles
fetch('/jobs', {
  method: 'POST',
  body: JSON.stringify({
    script_text: "...",
    generate_images: true,
    style_config: userSelectedStyle  // ← Just add this
  })
});
```

### Cost Field is Automatic

Just read it from the response:
```javascript
const job = await response.json();
console.log('Cost:', job.cost.total_cost);
// That's it!
```

---

## 6. Testing

### Test Custom Styles

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Test script.",
    "generate_images": true,
    "style_config": {
      "art_style": "anime_style",
      "character_description": "test character"
    }
  }'
```

### Check Response Format

```bash
curl http://localhost:8000/jobs/{job_id}
```

Look for:
- `options.style_config` - Your custom style
- `cost` - Cost breakdown

---

## 7. Quick Reference

### New Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `style_config` | Object | No | Custom style configuration |
| `style_config.art_style` | String | No | Art style (e.g., "realistic") |
| `style_config.lighting` | String | No | Lighting (e.g., "natural_lighting") |
| `style_config.color_palette` | String | No | Colors (e.g., "warm_neutral") |
| `style_config.background` | String | No | Background (e.g., "office") |
| `style_config.character_description` | String | No | Character description |
| `style_config.camera_angle` | String | No | Camera (e.g., "medium_shot") |
| `style_config.framing` | String | No | Framing (e.g., "centered") |

### New Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `cost` | Object | Cost breakdown |
| `cost.total_cost` | Number | Total USD |
| `cost.prompt_generation_cost` | Number | OpenAI USD |
| `cost.image_generation_cost` | Number | Gemini USD |
| `cost.prompt_tokens_used` | Number | GPT tokens |
| `cost.image_tokens_used` | Number | Gemini tokens |
| `cost.num_prompts_generated` | Number | Scene count |
| `cost.num_images_generated` | Number | Image count |

---

## 8. Need Help?

- **Full style options:** See `CUSTOM_STYLE_GUIDE.md`
- **Cost details:** See `COST_TRACKING.md`
- **API examples:** See `API_EXAMPLES.md`
- **Full integration:** See `UI_INTEGRATION_GUIDE.md`

---

## Summary

✅ **Custom styles** - Users can choose their visual style  
✅ **Cost tracking** - See API costs automatically  
✅ **Backward compatible** - Existing code still works  
✅ **Optional** - Only use if you want these features  

**No breaking changes!** 🎉
