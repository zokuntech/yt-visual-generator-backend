# API Examples & Usage Guide

## Table of Contents
1. [Basic Usage](#basic-usage)
2. [Complete Workflow](#complete-workflow)
3. [Editing & Regeneration](#editing--regeneration)
4. [Error Handling](#error-handling)

---

## Basic Usage

### 1. Create a Job with Raw Text

**Request:**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Welcome to my channel. Today we explore AI. This technology is revolutionary.",
    "generate_images": true,
    "style_preset": "bratz_doll_style"
  }'
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "created_at": "2026-01-19T10:30:00.000Z",
  "status": "pending",
  "error_message": null,
  "script_text": "Welcome to my channel. Today we explore AI. This technology is revolutionary.",
  "google_doc_url": null,
  "google_doc_id": null,
  "options": {
    "generate_images": true,
    "style_preset": "bratz_doll_style"
  },
  "scene_ids": []
}
```

### 2. Check Job Status

**Request:**
```bash
curl http://localhost:8000/jobs/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response (Processing):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "generating_prompts",
  "scene_ids": []
}
```

**Response (Completed):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "completed",
  "scene_ids": ["scene-1", "scene-2", "scene-3"]
}
```

### 3. Get All Scenes

**Request:**
```bash
curl http://localhost:8000/scenes/job/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Response:**
```json
[
  {
    "id": "scene-1",
    "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
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
          "description": "alternative latina girl, nose ring, bangs, glasses",
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
    "image_url": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "last_error": null
  },
  {
    "id": "scene-2",
    "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "index": 1,
    "sentence_text": "Today we explore AI.",
    "visual_prompt": { ... },
    "image_status": "generated",
    "image_url": "data:image/png;base64,...",
    "last_error": null
  }
]
```

---

## Complete Workflow

### Python Example

```python
import requests
import time

BASE_URL = "http://localhost:8000"

# Step 1: Create job
response = requests.post(f"{BASE_URL}/jobs", json={
    "script_text": """
        Welcome to my channel where we discuss technology.
        Today's topic is artificial intelligence.
        AI is transforming every industry.
        Let's explore what this means for the future.
    """,
    "generate_images": True,
    "style_preset": "bratz_doll_style"
})

job = response.json()
job_id = job['id']
print(f"Job created: {job_id}")

# Step 2: Poll for completion
while True:
    response = requests.get(f"{BASE_URL}/jobs/{job_id}")
    job = response.json()
    status = job['status']
    
    print(f"Status: {status}")
    
    if status in ['completed', 'failed']:
        break
    
    time.sleep(2)

# Step 3: Get scenes
if job['status'] == 'completed':
    response = requests.get(f"{BASE_URL}/scenes/job/{job_id}")
    scenes = response.json()
    
    print(f"\nGenerated {len(scenes)} scenes:")
    for scene in scenes:
        print(f"\nScene {scene['index']}:")
        print(f"  Text: {scene['sentence_text']}")
        print(f"  Has image: {scene['image_status'] == 'generated'}")
        
        if scene['visual_prompt']:
            prompt = scene['visual_prompt']
            print(f"  Style: {prompt['style']['art_style']}")
            if prompt['characters']:
                print(f"  Character: {prompt['characters'][0]['description']}")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

async function createStoryboard() {
  // Create job
  const createResponse = await axios.post(`${BASE_URL}/jobs`, {
    script_text: 'Welcome to my channel. Today we discuss AI. It is amazing.',
    generate_images: true,
    style_preset: 'bratz_doll_style'
  });
  
  const jobId = createResponse.data.id;
  console.log(`Job created: ${jobId}`);
  
  // Poll for completion
  let job;
  do {
    await new Promise(resolve => setTimeout(resolve, 2000));
    const statusResponse = await axios.get(`${BASE_URL}/jobs/${jobId}`);
    job = statusResponse.data;
    console.log(`Status: ${job.status}`);
  } while (!['completed', 'failed'].includes(job.status));
  
  // Get scenes
  if (job.status === 'completed') {
    const scenesResponse = await axios.get(`${BASE_URL}/scenes/job/${jobId}`);
    const scenes = scenesResponse.data;
    
    console.log(`\nGenerated ${scenes.length} scenes`);
    scenes.forEach(scene => {
      console.log(`\nScene ${scene.index}:`);
      console.log(`  Text: ${scene.sentence_text}`);
      console.log(`  Image: ${scene.image_status}`);
    });
  }
}

createStoryboard();
```

---

## Editing & Regeneration

### 1. Get a Specific Scene

**Request:**
```bash
curl http://localhost:8000/scenes/scene-123
```

### 2. Update Visual Prompt

**Request:**
```bash
curl -X PATCH http://localhost:8000/scenes/scene-123 \
  -H "Content-Type: application/json" \
  -d '{
    "visual_prompt": {
      "scene_id": "scene-123",
      "sentence_text": "Welcome to my channel.",
      "style": {
        "art_style": "bratz_doll_style",
        "lighting": "dramatic_lighting",
        "color_palette": "vibrant",
        "background": "studio"
      },
      "characters": [
        {
          "role": "main_subject",
          "description": "energetic content creator, colorful outfit",
          "expression": "excited",
          "pose": "dynamic"
        }
      ],
      "composition": {
        "camera_angle": "close_up",
        "framing": "rule_of_thirds",
        "extras": "no_text_no_logos_no_watermarks"
      }
    }
  }'
```

**Response:**
```json
{
  "id": "scene-123",
  "visual_prompt": {
    "style": {
      "lighting": "dramatic_lighting",
      "color_palette": "vibrant"
    }
  },
  "image_status": "generated",
  "image_url": "data:image/png;base64,..."
}
```

### 3. Regenerate Image

**Request:**
```bash
curl -X POST http://localhost:8000/scenes/scene-123/regenerate-image
```

**Response:**
```json
{
  "id": "scene-123",
  "image_status": "pending",
  "last_error": null
}
```

**Check Status:**
```bash
curl http://localhost:8000/scenes/scene-123
```

---

## Error Handling

### Invalid Request (Missing Script)

**Request:**
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "generate_images": true
  }'
```

**Response (422 Validation Error):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "script_text"],
      "msg": "Field required"
    }
  ]
}
```

### Job Not Found

**Request:**
```bash
curl http://localhost:8000/jobs/invalid-id
```

**Response (404 Not Found):**
```json
{
  "detail": "Job not found"
}
```

### Job Failed

**Response:**
```json
{
  "id": "job-123",
  "status": "failed",
  "error_message": "Failed to retrieve Google Doc: Invalid document ID",
  "scene_ids": []
}
```

---

## Advanced Usage

### Without Image Generation (Faster)

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Your script here...",
    "generate_images": false,
    "style_preset": "bratz_doll_style"
  }'
```

This will only generate visual prompts (no images), which is much faster.

### Different Style Presets

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Your script here...",
    "generate_images": true,
    "style_preset": "anime_style"
  }'
```

### List All Jobs

```bash
curl http://localhost:8000/jobs
```

**Response:**
```json
[
  {
    "id": "job-1",
    "status": "completed",
    "created_at": "2026-01-19T10:00:00Z"
  },
  {
    "id": "job-2",
    "status": "generating_images",
    "created_at": "2026-01-19T10:30:00Z"
  }
]
```

---

## Testing with Postman

### Import Collection

Create a Postman collection with these endpoints:

1. **Create Job**
   - Method: POST
   - URL: `{{base_url}}/jobs`
   - Body: JSON with `script_text`

2. **Get Job**
   - Method: GET
   - URL: `{{base_url}}/jobs/{{job_id}}`

3. **Get Scenes**
   - Method: GET
   - URL: `{{base_url}}/scenes/job/{{job_id}}`

4. **Update Scene**
   - Method: PATCH
   - URL: `{{base_url}}/scenes/{{scene_id}}`
   - Body: JSON with `visual_prompt`

5. **Regenerate Image**
   - Method: POST
   - URL: `{{base_url}}/scenes/{{scene_id}}/regenerate-image`

Set environment variable:
- `base_url`: `http://localhost:8000`

---

## Rate Limiting Considerations

Currently, there's **no rate limiting**. For production:

1. Add rate limiting middleware
2. Implement API keys
3. Set quotas per user
4. Add retry logic in clients

---

## Best Practices

1. **Poll Responsibly**: Wait 2-3 seconds between status checks
2. **Handle Errors**: Always check response status codes
3. **Validate Input**: Ensure scripts are reasonable length
4. **Save Job IDs**: Store job IDs for later retrieval
5. **Monitor Status**: Check for 'failed' status and handle errors
6. **Use Webhooks**: (Future) Instead of polling, use webhooks

---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for:
- Interactive API testing
- Complete schema documentation
- Try-it-out functionality
- Response examples

---

**Need Help?** Check README.md or SETUP.md for more information.
