# 💰 Cost Tracking - Live Cost Counter for UI

## Overview

Every operation (scene generation, image editing, video animation) now returns **real-time cost information** that you can use to display a live cost counter in the UI.

---

## 🎯 What's Available

### 1. Scene-Level Costs

Every `Scene` object now includes:
- `generation_cost`: Cost to initially generate this scene (director + cinematographer + image)
- `last_operation_cost`: Cost of the most recent operation (regeneration, edit, or video)

### 2. Job-Level Costs

The `GET /jobs/{job_id}` endpoint returns the full job with a `cost` breakdown:

```json
{
  "id": "job_123",
  "status": "completed",
  "cost": {
    "total_cost": 0.0456,
    "prompt_generation_cost": 0.0012,
    "image_generation_cost": 0.0234,
    "video_generation_cost": 0.0210,
    "num_prompts_generated": 10,
    "num_images_generated": 10,
    "num_videos_generated": 3,
    "prompt_tokens_used": 8543,
    "image_tokens_used": 1200
  }
}
```

### 3. Real-Time Cost Endpoint

**NEW:** `GET /jobs/{job_id}/cost` - Get just the cost breakdown (perfect for polling)

```javascript
const response = await fetch(`/jobs/${jobId}/cost`);
const cost = await response.json();
// Returns just the CostBreakdown object
```

---

## 🛠️ UI Implementation Examples

### Example 1: Live Counter During Job Processing

```javascript
function JobCostCounter({ jobId }) {
  const [cost, setCost] = useState({ total_cost: 0 });
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const pollCost = setInterval(async () => {
      const response = await fetch(`/jobs/${jobId}/cost`);
      const data = await response.json();
      setCost(data);
      
      // Check if job is done
      const jobResponse = await fetch(`/jobs/${jobId}`);
      const job = await jobResponse.json();
      if (job.status === 'completed' || job.status === 'failed') {
        setIsProcessing(false);
        clearInterval(pollCost);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollCost);
  }, [jobId]);

  return (
    <div className="cost-counter">
      <span>Total Cost:</span>
      <span className="amount">${cost.total_cost.toFixed(4)}</span>
      {isProcessing && <span className="loading">⏳</span>}
    </div>
  );
}
```

### Example 2: Show Cost After Each Operation

```javascript
// After regenerating an image
const regenerateScene = async (sceneId) => {
  const response = await fetch(`/scenes/${sceneId}/regenerate-image`, {
    method: 'POST'
  });
  const scene = await response.json();
  
  // Show the cost of this operation
  showToast(`Image regenerated! Cost: $${scene.last_operation_cost.toFixed(4)}`);
  
  // Update total job cost
  updateJobCost(scene.job_id);
};

// After editing with instruction
const editScene = async (sceneId, instruction) => {
  const response = await fetch(`/scenes/${sceneId}/regenerate-with-instruction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ instruction })
  });
  const scene = await response.json();
  
  // This includes both cinematographer + image cost
  showToast(`Scene edited! Cost: $${scene.last_operation_cost.toFixed(4)}`);
  updateJobCost(scene.job_id);
};

// After animating to video
const animateScene = async (sceneId) => {
  const response = await fetch(`/scenes/${sceneId}/animate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ aspect_ratio: '16:9' })
  });
  const scene = await response.json();
  
  // Show estimated cost immediately
  showToast(`Video generation started! Estimated: $${scene.last_operation_cost.toFixed(4)}`);
  
  // Poll for completion, then update total
  pollVideoStatus(sceneId);
};
```

### Example 3: Detailed Cost Breakdown Display

```javascript
function CostBreakdown({ jobId }) {
  const [cost, setCost] = useState(null);

  useEffect(() => {
    fetch(`/jobs/${jobId}/cost`)
      .then(r => r.json())
      .then(setCost);
  }, [jobId]);

  if (!cost) return <div>Loading...</div>;

  return (
    <div className="cost-breakdown">
      <h3>Cost Breakdown</h3>
      <table>
        <tbody>
          <tr>
            <td>Scene Planning (GPT):</td>
            <td>${cost.prompt_generation_cost.toFixed(6)}</td>
            <td>({cost.num_prompts_generated} scenes)</td>
          </tr>
          <tr>
            <td>Image Generation (Gemini):</td>
            <td>${cost.image_generation_cost.toFixed(6)}</td>
            <td>({cost.num_images_generated} images)</td>
          </tr>
          <tr>
            <td>Video Animation (Veo):</td>
            <td>${cost.video_generation_cost.toFixed(6)}</td>
            <td>({cost.num_videos_generated} videos)</td>
          </tr>
          <tr className="total">
            <td><strong>Total:</strong></td>
            <td><strong>${cost.total_cost.toFixed(6)}</strong></td>
            <td></td>
          </tr>
        </tbody>
      </table>
      <div className="tokens-used">
        <small>Tokens Used: {cost.prompt_tokens_used.toLocaleString()}</small>
      </div>
    </div>
  );
}
```

---

## 📊 Cost Tracking Flow

### Initial Job Creation
1. User submits script → `POST /jobs`
2. Backend processes scenes in background
3. Each scene gets `generation_cost` set (director + cinematographer + image)
4. Job's `cost.total_cost` updates in real-time

### Image Regeneration
1. User clicks "Regenerate" → `POST /scenes/{id}/regenerate-image`
2. Response includes `scene.last_operation_cost` (just image cost)
3. Job's `cost.image_generation_cost` increases

### Scene Editing with Instruction
1. User types "make her smile" → `POST /scenes/{id}/regenerate-with-instruction`
2. Response includes `scene.last_operation_cost` (cinematographer + image cost)
3. Job's costs update accordingly

### Video Animation
1. User clicks "Animate" → `POST /scenes/{id}/animate`
2. Response includes `scene.last_operation_cost` (estimated video cost: ~$0.09)
3. Poll `GET /scenes/{id}/video-status` until done
4. When `video_status = "generated"`, job's `cost.video_generation_cost` increases

---

## 🎨 UI Design Suggestions

### Floating Cost Counter
```jsx
<div className="floating-cost-counter">
  💰 ${totalCost.toFixed(4)}
</div>
```

### Per-Scene Cost Display
```jsx
<div className="scene-card">
  <img src={scene.image_url} />
  <div className="scene-cost">
    <small>Generation: ${scene.generation_cost.toFixed(6)}</small>
    {scene.last_operation_cost > 0 && (
      <small>Last edit: ${scene.last_operation_cost.toFixed(6)}</small>
    )}
  </div>
</div>
```

### Budget Warning
```jsx
{cost.total_cost > 1.00 && (
  <div className="budget-warning">
    ⚠️ Cost exceeds $1.00! Consider reducing edits.
  </div>
)}
```

---

## 💡 Typical Costs

| Operation | Cost | Notes |
|-----------|------|-------|
| Scene generation | ~$0.00015 | Director + Cinematographer (GPT-4o-mini) |
| Image generation | ~$0.002 | Gemini image generation |
| Image regeneration | ~$0.002 | Just image, no prompt update |
| Scene edit (text) | ~$0.00215 | Cinematographer + new image |
| Video animation | ~$0.09 | Veo 3.1 Fast, 6 seconds |

**Example:** A 10-scene video (all animated) = ~$0.02 (scenes) + $0.02 (images) + $0.90 (videos) = **~$0.94 total**

---

## 🚀 Quick Start

```javascript
// Simple cost tracker component
import { useState, useEffect } from 'react';

export function CostTracker({ jobId }) {
  const [cost, setCost] = useState(0);

  useEffect(() => {
    const interval = setInterval(async () => {
      const res = await fetch(`/jobs/${jobId}/cost`);
      const data = await res.json();
      setCost(data.total_cost);
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId]);

  return <div>Cost: ${cost.toFixed(4)}</div>;
}
```

That's it! 🎉
