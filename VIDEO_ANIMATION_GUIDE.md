# 🎬 Video Animation with Veo 3.1

## Overview

You can now animate any generated scene image into an **8-second video** using Google's Veo 3.1! This feature converts still images into dynamic videos with motion and (optionally) sound.

## Quick Start

### 1. Animate a Scene

After generating a scene image, click your "Animate" button to start video generation:

```typescript
// Example: Animate a scene
async function animateScene(sceneId: string) {
  const response = await fetch(`${API_URL}/scenes/${sceneId}/animate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      aspect_ratio: "16:9",  // or "9:16" for portrait
      custom_prompt: null    // optional: override scene text
    })
  });
  
  const scene = await response.json();
  console.log('Video generation started:', scene.video_operation_name);
  console.log('Status:', scene.video_status);  // "pending"
}
```

### 2. Poll for Video Status

Video generation takes **11 seconds to 6 minutes**. Poll every 5-10 seconds:

```typescript
async function checkVideoStatus(sceneId: string) {
  const response = await fetch(`${API_URL}/scenes/${sceneId}/video-status`);
  const scene = await response.json();
  
  switch (scene.video_status) {
    case 'pending':
    case 'processing':
      console.log('Still generating video...');
      // Continue polling
      setTimeout(() => checkVideoStatus(sceneId), 5000);
      break;
      
    case 'generated':
      console.log('Video ready!', scene.video_url);
      // Display video
      displayVideo(scene.video_url);
      break;
      
    case 'failed':
      console.error('Video generation failed:', scene.last_error);
      break;
  }
}
```

### 3. Display the Video

The video is returned as a data URI (same format as images):

```typescript
function displayVideo(videoUrl: string) {
  const videoElement = document.createElement('video');
  videoElement.src = videoUrl;
  videoElement.controls = true;
  videoElement.autoplay = true;
  videoElement.loop = true;
  
  // Add to DOM
  document.getElementById('video-container').appendChild(videoElement);
}
```

## API Reference

### POST /scenes/{scene_id}/animate

Start video generation for a scene.

**Request Body:**
```json
{
  "aspect_ratio": "16:9",      // or "9:16" for portrait
  "custom_prompt": "optional"  // override scene text (optional)
}
```

**Response:**
```json
{
  "id": "scene-123",
  "sentence_text": "A person smiling at the camera",
  "image_url": "data:image/png;base64,...",
  "video_status": "pending",
  "video_operation_name": "operations/...",
  "video_url": null
}
```

**Requirements:**
- Scene must have `image_status = "generated"`
- Scene must have a valid `image_url`

**Error Responses:**
- `400`: Scene has no image - generate image first
- `404`: Scene not found
- `503`: Video service not available

---

### GET /scenes/{scene_id}/video-status

Check video generation progress.

**Response:**
```json
{
  "id": "scene-123",
  "video_status": "processing",  // or "generated", "failed"
  "video_url": "data:video/mp4;base64,...",  // when generated
  "last_error": null
}
```

**Video Status Values:**
- `not_requested`: No video requested yet
- `pending`: Video generation just started
- `processing`: Video is being generated
- `generated`: ✅ Video ready! Check `video_url`
- `failed`: ❌ Generation failed, check `last_error`

## UI Implementation Example

### React Component

```tsx
import React, { useState, useEffect } from 'react';

interface Scene {
  id: string;
  image_url: string;
  video_status: string;
  video_url?: string;
  last_error?: string;
}

function SceneCard({ scene }: { scene: Scene }) {
  const [currentScene, setCurrentScene] = useState<Scene>(scene);
  const [isAnimating, setIsAnimating] = useState(false);

  // Start animation
  const handleAnimate = async () => {
    setIsAnimating(true);
    
    const response = await fetch(`/api/scenes/${scene.id}/animate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        aspect_ratio: "16:9"
      })
    });
    
    const updated = await response.json();
    setCurrentScene(updated);
    
    // Start polling
    pollVideoStatus();
  };

  // Poll for video status
  const pollVideoStatus = async () => {
    const response = await fetch(`/api/scenes/${scene.id}/video-status`);
    const updated = await response.json();
    setCurrentScene(updated);
    
    // Continue polling if still processing
    if (updated.video_status === 'pending' || updated.video_status === 'processing') {
      setTimeout(pollVideoStatus, 5000);  // Poll every 5 seconds
    } else {
      setIsAnimating(false);
    }
  };

  return (
    <div className="scene-card">
      {/* Show image */}
      <img src={currentScene.image_url} alt="Scene" />
      
      {/* Show video if generated */}
      {currentScene.video_status === 'generated' && currentScene.video_url && (
        <video src={currentScene.video_url} controls autoPlay loop />
      )}
      
      {/* Animate button */}
      {currentScene.video_status === 'not_requested' && (
        <button onClick={handleAnimate} disabled={isAnimating}>
          🎬 Animate Scene
        </button>
      )}
      
      {/* Status indicator */}
      {(currentScene.video_status === 'pending' || currentScene.video_status === 'processing') && (
        <div className="status">
          ⏳ Generating video... (11s - 6min)
        </div>
      )}
      
      {/* Error display */}
      {currentScene.video_status === 'failed' && (
        <div className="error">
          ❌ Video failed: {currentScene.last_error}
          <button onClick={handleAnimate}>Retry</button>
        </div>
      )}
    </div>
  );
}
```

## Features & Options

### Aspect Ratios

- **`16:9` (Landscape)**: Default, perfect for YouTube
- **`9:16` (Portrait)**: For TikTok, Instagram Reels, YouTube Shorts

```typescript
// For portrait videos
await fetch(`/api/scenes/${sceneId}/animate`, {
  method: 'POST',
  body: JSON.stringify({
    aspect_ratio: "9:16"  // Portrait
  })
});
```

### Custom Prompts

Override the scene text with a custom prompt for video generation:

```typescript
await fetch(`/api/scenes/${sceneId}/animate`, {
  method: 'POST',
  body: JSON.stringify({
    aspect_ratio: "16:9",
    custom_prompt: "A person slowly turning their head and smiling at the camera"
  })
});
```

### Video Specifications

- **Duration**: 8 seconds
- **Resolution**: 720p (can be upgraded to 1080p or 4k)
- **Frame Rate**: 24fps
- **Format**: MP4
- **Audio**: Natively generated (if applicable to the scene)
- **Watermark**: SynthID watermark included
- **Storage**: Videos stored for 2 days on server

## Cost Information

Video generation cost is automatically tracked:

- **Veo 3.1 Fast**: ~$0.12 per 8-second video
- **Veo 3.1 Regular**: ~$0.20 per 8-second video (higher quality)

Cost is added to the job's total cost breakdown.

## Polling Best Practices

### Recommended Polling Strategy

```typescript
class VideoPoller {
  private maxAttempts = 72;  // 6 minutes ÷ 5 seconds
  private pollInterval = 5000;  // 5 seconds
  private attempts = 0;

  async poll(sceneId: string): Promise<Scene> {
    while (this.attempts < this.maxAttempts) {
      const response = await fetch(`/api/scenes/${sceneId}/video-status`);
      const scene = await response.json();
      
      if (scene.video_status === 'generated' || scene.video_status === 'failed') {
        return scene;  // Done!
      }
      
      this.attempts++;
      await new Promise(resolve => setTimeout(resolve, this.pollInterval));
    }
    
    throw new Error('Video generation timed out');
  }
}
```

### User Experience Tips

1. **Show Progress**: Display "Generating video... (11s - 6min)" during processing
2. **Allow Cancellation**: Let users navigate away and come back later
3. **Persist State**: Store video_operation_name in case user refreshes
4. **Download Option**: Offer button to download the video file
5. **Fallback to Image**: Always keep the image visible as fallback

## Error Handling

```typescript
async function animateSceneWithErrorHandling(sceneId: string) {
  try {
    const response = await fetch(`/api/scenes/${sceneId}/animate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ aspect_ratio: "16:9" })
    });
    
    if (!response.ok) {
      const error = await response.json();
      
      if (response.status === 400) {
        alert('Please generate an image first before animating!');
      } else if (response.status === 503) {
        alert('Video service temporarily unavailable. Try again later.');
      } else {
        alert(`Error: ${error.detail}`);
      }
      return;
    }
    
    const scene = await response.json();
    // Start polling...
    
  } catch (error) {
    console.error('Network error:', error);
    alert('Failed to start video generation. Check your connection.');
  }
}
```

## Common Issues

### Issue: "Scene has no generated image"

**Solution**: The scene must have `image_status = "generated"` and a valid `image_url` before you can animate it. Generate the image first using the job creation workflow.

### Issue: Video generation stuck in "pending" forever

**Solution**: Check the `video_operation_name` is present. If polling for 6+ minutes with no change, the operation may have failed. Try regenerating or check server logs.

### Issue: Video URL is too large for browser

**Solution**: Videos are returned as data URIs which can be large (several MB). For production, consider:
1. Storing videos on cloud storage (S3, GCS)
2. Returning download URLs instead of data URIs
3. Implementing server-side video serving

## Advanced: Batch Animation

Animate multiple scenes at once:

```typescript
async function animateAllScenes(sceneIds: string[]) {
  // Start all animations
  const operations = await Promise.all(
    sceneIds.map(id => 
      fetch(`/api/scenes/${id}/animate`, {
        method: 'POST',
        body: JSON.stringify({ aspect_ratio: "16:9" })
      })
    )
  );
  
  // Poll all in parallel
  const poller = setInterval(async () => {
    const statuses = await Promise.all(
      sceneIds.map(id => 
        fetch(`/api/scenes/${id}/video-status`).then(r => r.json())
      )
    );
    
    const allDone = statuses.every(s => 
      s.video_status === 'generated' || s.video_status === 'failed'
    );
    
    if (allDone) {
      clearInterval(poller);
      console.log('All videos done!', statuses);
    }
  }, 5000);
}
```

## Model Information

### Veo 3.1 Fast (Default)
- **Speed**: Optimized for quick generation
- **Quality**: High quality, slightly lower than regular Veo 3.1
- **Cost**: ~$0.12 per video
- **Best for**: Rapid iteration, A/B testing, social media content

### Veo 3.1 (Premium)
- **Speed**: Slower, more thorough
- **Quality**: Highest quality
- **Cost**: ~$0.20 per video
- **Best for**: Final production, professional content

## Next Steps

- ✅ Implement the "Animate" button in your UI
- ✅ Add polling logic for video status
- ✅ Display videos when ready
- ✅ Handle errors gracefully
- ✅ Test with different aspect ratios

Need help? Check the [Veo 3.1 Documentation](https://ai.google.dev/gemini-api/docs/video).
