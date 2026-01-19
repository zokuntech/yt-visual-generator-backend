# UI Integration Guide

**For Frontend Developers**

This guide explains how to integrate your UI with the YT Visual Generator Backend API.

---

## Table of Contents
1. [Overview](#overview)
2. [Backend Capabilities](#backend-capabilities)
3. [API Base URL](#api-base-url)
4. [Authentication](#authentication)
5. [Complete Workflow](#complete-workflow)
6. [API Endpoints](#api-endpoints)
7. [Frontend Implementation Examples](#frontend-implementation-examples)
8. [Error Handling](#error-handling)
9. [Best Practices](#best-practices)

---

## Overview

### What the Backend Does

The backend automates the process of converting YouTube scripts into visual storyboards:

1. **Receives** your script text
2. **Splits** it into individual sentences/scenes
3. **Generates** structured visual prompts using AI (ChatGPT)
4. **Creates** images for each scene using AI (Google Gemini)
5. **Returns** complete storyboard data (text + prompts + images)

### What the UI Should Do

1. **File Handling**: Allow users to upload `.doc` or `.docx` files
2. **Text Extraction**: Parse the document and extract plain text
3. **Job Creation**: Send the extracted text to the backend API
4. **Progress Tracking**: Poll the backend for job status updates
5. **Display Results**: Show the generated scenes, prompts, and images
6. **Editing**: Allow users to edit prompts and regenerate images

---

## Backend Capabilities

### ✅ What the Backend Provides

- **Automatic sentence splitting**
- **AI-powered visual prompt generation** (structured JSON)
- **AI image generation** (optional)
- **Background processing** (non-blocking)
- **Scene editing** (update prompts)
- **Image regeneration** (after editing prompts)
- **Job status tracking**

### ❌ What the Backend Does NOT Do

- **File uploads** - You handle .doc/.docx parsing on the frontend
- **User authentication** - No auth required (add if needed)
- **File storage** - Images are returned as base64 data URIs
- **Rate limiting** - No limits (add if needed for production)

---

## API Base URL

### Development
```
http://localhost:8000
```

### Production
```
https://your-domain.com
```

### API Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Authentication

**Current State**: No authentication required.

For production, you may want to add:
- API keys
- JWT tokens
- OAuth

---

## Complete Workflow

Here's the complete user journey from the UI perspective:

### Step 1: User Uploads Document

```
┌─────────────────────┐
│   User Action       │
│  Upload .doc file   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   UI Processing     │
│ Parse .doc → Text   │
└──────────┬──────────┘
           │
           ▼
```

**UI Responsibilities:**
- Accept `.doc` or `.docx` file upload
- Parse file to extract plain text
- Handle parsing errors gracefully

**Recommended Libraries:**
- JavaScript: `mammoth.js` (for .docx)
- Python: `python-docx` (if backend parsing)

---

### Step 2: Create Job

```
┌─────────────────────┐
│   UI Action         │
│ POST /jobs          │
│ {script_text: ...}  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Backend Response  │
│ Returns Job ID      │
│ Status: "pending"   │
└──────────┬──────────┘
```

**API Call:**
```javascript
POST /jobs
{
  "script_text": "Welcome to my channel. Today we discuss AI...",
  "generate_images": true,
  "style_preset": "bratz_doll_style"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-19T10:30:00Z",
  "status": "pending",
  "script_text": "Welcome to my channel...",
  "options": {
    "generate_images": true,
    "style_preset": "bratz_doll_style"
  },
  "scene_ids": []
}
```

---

### Step 3: Poll Job Status

```
┌─────────────────────┐
│   UI Action         │
│ GET /jobs/{id}      │
│ Every 2-3 seconds   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Check Status        │
│ pending →           │
│ generating_prompts →│
│ generating_images → │
│ completed ✅        │
└─────────────────────┘
```

**Job Status Flow:**
1. `pending` - Job created, waiting to start
2. `generating_prompts` - AI is creating visual prompts
3. `generating_images` - AI is generating images (if enabled)
4. `completed` - All done! ✅
5. `failed` - Something went wrong ❌

**Polling Example:**
```javascript
async function waitForJobCompletion(jobId) {
  while (true) {
    const response = await fetch(`/jobs/${jobId}`);
    const job = await response.json();
    
    // Update UI with current status
    updateProgressBar(job.status);
    
    if (job.status === 'completed') {
      return job;
    }
    
    if (job.status === 'failed') {
      throw new Error(job.error_message);
    }
    
    // Wait 2 seconds before next poll
    await sleep(2000);
  }
}
```

---

### Step 4: Retrieve Scenes

```
┌─────────────────────┐
│   UI Action         │
│ GET /scenes/job/{id}│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Backend Returns   │
│ Array of Scenes     │
│ with prompts +      │
│ images              │
└─────────────────────┘
```

**API Call:**
```javascript
GET /scenes/job/{job_id}
```

**Response:**
```json
[
  {
    "id": "scene-1",
    "job_id": "550e8400-...",
    "index": 0,
    "sentence_text": "Welcome to my channel.",
    "visual_prompt": {
      "scene_id": "scene-1",
      "sentence_text": "Welcome to my channel.",
      "style": {
        "art_style": "bratz_doll_style",
        "lighting": "soft_even_studio_lighting",
        "color_palette": "warm_neutral_with_contrast",
        "background": "contextually_relevant_environment"
      },
      "characters": [
        {
          "role": "main_subject",
          "description": "energetic content creator, friendly smile",
          "expression": "confident_calm",
          "pose": "front_facing"
        }
      ],
      "composition": {
        "camera_angle": "medium_shot",
        "framing": "centered",
        "extras": "no_text_no_logos_no_watermarks"
      }
    },
    "image_status": "generated",
    "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEU...",
    "last_error": null
  },
  // ... more scenes
]
```

---

### Step 5: Display Storyboard (UI Layout)

```
┌────────────────────────────────────────────────────────┐
│                    Storyboard View                      │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │  Scene 1         │  │  Scene 2         │           │
│  │  ┌────────────┐  │  │  ┌────────────┐  │           │
│  │  │   Image    │  │  │  │   Image    │  │           │
│  │  │            │  │  │  │            │  │           │
│  │  └────────────┘  │  │  └────────────┘  │           │
│  │                  │  │                  │           │
│  │ "Welcome to my"  │  │ "Today we talk" │           │
│  │  channel."       │  │  about AI."      │           │
│  │                  │  │                  │           │
│  │ [Edit] [Regen]   │  │ [Edit] [Regen]   │           │
│  └──────────────────┘  └──────────────────┘           │
│                                                         │
└────────────────────────────────────────────────────────┘
```

**What to Display for Each Scene:**
- ✅ Generated image (or placeholder if still generating)
- ✅ Original sentence text
- ✅ Visual prompt details (expandable)
- ✅ Edit button (to modify prompt)
- ✅ Regenerate button (to create new image)
- ✅ Status indicator (pending/generated/failed)

---

### Step 6: Edit Scene (Optional)

```
┌─────────────────────┐
│   User Action       │
│ Edit visual prompt  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   UI Action         │
│ PATCH /scenes/{id}  │
│ {visual_prompt: ...}│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Backend Updates   │
│ Scene prompt saved  │
└─────────────────────┘
```

**Use Case:** User wants to change the visual style or character description.

**API Call:**
```javascript
PATCH /scenes/{scene_id}
{
  "visual_prompt": {
    // Updated prompt with changes
    "scene_id": "scene-1",
    "sentence_text": "Welcome to my channel.",
    "style": {
      "art_style": "bratz_doll_style",
      "lighting": "dramatic_lighting",  // Changed!
      "color_palette": "vibrant",        // Changed!
      "background": "studio"
    },
    // ... rest of prompt
  }
}
```

---

### Step 7: Regenerate Image (Optional)

```
┌─────────────────────┐
│   User Action       │
│ Click "Regenerate"  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   UI Action         │
│ POST /scenes/{id}/  │
│ regenerate-image    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Backend Creates   │
│ New image from      │
│ updated prompt      │
└─────────────────────┘
```

**API Call:**
```javascript
POST /scenes/{scene_id}/regenerate-image
```

**Then Poll Scene Status:**
```javascript
GET /scenes/{scene_id}
// Check image_status: "pending" → "generated"
```

---

## API Endpoints

### Jobs

#### Create Job
```
POST /jobs
Content-Type: application/json

{
  "script_text": "Your script here...",
  "generate_images": true,
  "style_preset": "bratz_doll_style"
}
```

**Fields:**
- `script_text` (string, **required**): The extracted text from the document
- `generate_images` (boolean, optional, default: `true`): Whether to generate images
- `style_preset` (string, optional, default: `"bratz_doll_style"`): Visual style

**Response:** Job object

---

#### Get Job Status
```
GET /jobs/{job_id}
```

**Response:**
```json
{
  "id": "job-id",
  "status": "completed",
  "scene_ids": ["scene-1", "scene-2"]
}
```

---

#### List All Jobs
```
GET /jobs
```

**Response:** Array of Job objects

---

### Scenes

#### Get All Scenes for Job
```
GET /scenes/job/{job_id}
```

**Response:** Array of Scene objects (sorted by index)

---

#### Get Single Scene
```
GET /scenes/{scene_id}
```

**Response:** Scene object

---

#### Update Scene Prompt
```
PATCH /scenes/{scene_id}
Content-Type: application/json

{
  "visual_prompt": {
    // Complete visual prompt object
  }
}
```

**Response:** Updated Scene object

---

#### Regenerate Scene Image
```
POST /scenes/{scene_id}/regenerate-image
```

**Response:** Scene object with `image_status: "pending"`

---

## Frontend Implementation Examples

### React Example

```jsx
import React, { useState } from 'react';
import mammoth from 'mammoth';

function StoryboardGenerator() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [scenes, setScenes] = useState([]);

  // Step 1: Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    
    // Extract text from .docx
    const arrayBuffer = await file.arrayBuffer();
    const result = await mammoth.extractRawText({ arrayBuffer });
    const scriptText = result.value;
    
    // Create job
    createJob(scriptText);
  };

  // Step 2: Create job
  const createJob = async (scriptText) => {
    setStatus('creating');
    
    const response = await fetch('http://localhost:8000/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script_text: scriptText,
        generate_images: true,
        style_preset: 'bratz_doll_style'
      })
    });
    
    const job = await response.json();
    setJobId(job.id);
    
    // Start polling
    pollJobStatus(job.id);
  };

  // Step 3: Poll job status
  const pollJobStatus = async (jobId) => {
    const interval = setInterval(async () => {
      const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
      const job = await response.json();
      
      setStatus(job.status);
      
      if (job.status === 'completed') {
        clearInterval(interval);
        fetchScenes(jobId);
      }
      
      if (job.status === 'failed') {
        clearInterval(interval);
        alert('Job failed: ' + job.error_message);
      }
    }, 2000);
  };

  // Step 4: Fetch scenes
  const fetchScenes = async (jobId) => {
    const response = await fetch(`http://localhost:8000/scenes/job/${jobId}`);
    const scenesData = await response.json();
    setScenes(scenesData);
  };

  // Step 5: Regenerate image
  const regenerateImage = async (sceneId) => {
    await fetch(`http://localhost:8000/scenes/${sceneId}/regenerate-image`, {
      method: 'POST'
    });
    
    // Poll for updated scene
    setTimeout(() => fetchScenes(jobId), 3000);
  };

  return (
    <div>
      <h1>YouTube Storyboard Generator</h1>
      
      {/* File Upload */}
      <input 
        type="file" 
        accept=".doc,.docx" 
        onChange={handleFileUpload}
      />
      
      {/* Status */}
      {status !== 'idle' && (
        <div>Status: {status}</div>
      )}
      
      {/* Scenes Grid */}
      <div className="scenes-grid">
        {scenes.map(scene => (
          <div key={scene.id} className="scene-card">
            <img 
              src={scene.image_url} 
              alt={scene.sentence_text}
            />
            <p>{scene.sentence_text}</p>
            <button onClick={() => regenerateImage(scene.id)}>
              Regenerate
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default StoryboardGenerator;
```

---

### Vanilla JavaScript Example

```javascript
// Handle file upload
document.getElementById('fileInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  
  // Use mammoth to extract text
  const arrayBuffer = await file.arrayBuffer();
  const result = await mammoth.extractRawText({ arrayBuffer });
  const scriptText = result.value;
  
  // Create job
  const response = await fetch('http://localhost:8000/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_text: scriptText,
      generate_images: true
    })
  });
  
  const job = await response.json();
  
  // Poll for completion
  pollJob(job.id);
});

async function pollJob(jobId) {
  const interval = setInterval(async () => {
    const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
    const job = await response.json();
    
    document.getElementById('status').textContent = job.status;
    
    if (job.status === 'completed') {
      clearInterval(interval);
      loadScenes(jobId);
    }
  }, 2000);
}

async function loadScenes(jobId) {
  const response = await fetch(`http://localhost:8000/scenes/job/${jobId}`);
  const scenes = await response.json();
  
  // Display scenes
  const container = document.getElementById('scenes');
  scenes.forEach(scene => {
    const div = document.createElement('div');
    div.innerHTML = `
      <img src="${scene.image_url}" />
      <p>${scene.sentence_text}</p>
    `;
    container.appendChild(div);
  });
}
```

---

## Error Handling

### Common Errors

#### 1. Job Creation Failed
```json
{
  "detail": "Field required"
}
```
**Fix:** Ensure `script_text` is provided

---

#### 2. Job Failed During Processing
```json
{
  "status": "failed",
  "error_message": "OpenAI API key is invalid"
}
```
**Fix:** Contact backend team about API keys

---

#### 3. Scene Not Found
```json
{
  "detail": "Scene not found"
}
```
**Fix:** Verify scene ID is correct

---

### Error Handling Example

```javascript
try {
  const response = await fetch('http://localhost:8000/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ script_text: text })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Job creation failed');
  }
  
  const job = await response.json();
  // ... proceed
  
} catch (error) {
  console.error('Error:', error);
  alert('Failed to create job: ' + error.message);
}
```

---

## Best Practices

### 1. File Parsing

✅ **Do:**
- Use `mammoth.js` for .docx files
- Handle parsing errors gracefully
- Show loading state during parsing
- Validate text is not empty

❌ **Don't:**
- Send files larger than 5MB without warning
- Assume parsing will always succeed

---

### 2. Polling

✅ **Do:**
- Poll every 2-3 seconds
- Stop polling when job completes/fails
- Show progress indicator
- Set a maximum timeout (e.g., 5 minutes)

❌ **Don't:**
- Poll more than once per second (be respectful)
- Poll forever (add timeout)

---

### 3. Image Display

✅ **Do:**
- Show loading placeholder while image generates
- Handle base64 data URIs correctly
- Add error state for failed images
- Lazy load images if many scenes

❌ **Don't:**
- Try to cache images (they're base64 in memory)
- Assume all images will succeed

---

### 4. User Experience

✅ **Do:**
- Show clear status messages ("Generating prompts...", "Creating images...")
- Allow canceling (stop polling)
- Save job IDs for later retrieval
- Show estimated time remaining

❌ **Don't:**
- Leave users wondering what's happening
- Block UI during processing

---

## Quick Reference

### Required Libraries (Frontend)

```bash
npm install mammoth  # For .docx parsing
```

### Environment Variables (Frontend)

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### Typical Response Times

- **Job Creation**: < 1 second
- **Prompt Generation**: 2-10 seconds (depends on script length)
- **Image Generation**: 5-30 seconds per scene
- **Total**: ~30 seconds for 3-sentence script with images

---

## Testing

### Test Data

Use this sample script for testing:

```
Welcome to my channel where we explore technology. 
Today we're discussing artificial intelligence. 
This is an exciting topic that affects everyone.
```

### Test Without Images (Faster)

```json
{
  "script_text": "Test script here.",
  "generate_images": false
}
```

---

## Support

- **API Documentation**: http://localhost:8000/docs
- **Backend Team**: Contact backend developers
- **Issues**: Check console logs and backend terminal

---

## Summary Checklist

Frontend Integration Checklist:

- [ ] File upload UI component
- [ ] Document parsing (mammoth.js)
- [ ] Create job API call
- [ ] Job status polling logic
- [ ] Progress indicators
- [ ] Fetch scenes API call
- [ ] Display scenes grid
- [ ] Edit scene UI
- [ ] Regenerate image functionality
- [ ] Error handling
- [ ] Loading states
- [ ] Responsive design

---

**You're ready to integrate!** 🚀

If you have questions, check the API docs at `/docs` or contact the backend team.
