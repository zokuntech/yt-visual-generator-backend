# Aspect Ratio Guide

The API now supports **custom aspect ratios** for generated images. You can specify the aspect ratio when creating a job, and all images will be generated in that ratio.

---

## Supported Aspect Ratios

Gemini supports the following aspect ratios:

| Aspect Ratio | Best For | Dimensions Example |
|--------------|----------|-------------------|
| **16:9** (default) | YouTube videos, wide screens | 1920×1080 |
| **9:16** | TikTok, Instagram Stories, Reels | 1080×1920 |
| **1:1** | Instagram posts, square format | 1080×1080 |
| **4:3** | Classic TV, presentations | 1024×768 |
| **3:4** | Portrait photos, Pinterest | 768×1024 |

---

## How to Specify Aspect Ratio

### API Request

Include `aspect_ratio` in the `style_config`:

```json
{
  "script_text": "Your script here...",
  "generate_images": true,
  "style_config": {
    "aspect_ratio": "16:9",
    "art_style": "professional_youtube_style",
    "character_description": "content creator"
  }
}
```

### React Example

```jsx
const StoryboardCreator = () => {
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const [scriptText, setScriptText] = useState('');

  const handleSubmit = async () => {
    const response = await fetch('http://localhost:8000/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        script_text: scriptText,
        generate_images: true,
        style_config: {
          aspect_ratio: aspectRatio,
          art_style: 'professional_youtube_style',
          character_description: 'content creator'
        }
      })
    });

    const job = await response.json();
    console.log('Job created:', job.id);
  };

  return (
    <div>
      <h2>Create Storyboard</h2>
      
      <div className="aspect-ratio-selector">
        <label htmlFor="aspectRatio">Aspect Ratio:</label>
        <select
          id="aspectRatio"
          value={aspectRatio}
          onChange={(e) => setAspectRatio(e.target.value)}
        >
          <option value="16:9">16:9 - YouTube (Landscape)</option>
          <option value="9:16">9:16 - TikTok/Stories (Portrait)</option>
          <option value="1:1">1:1 - Instagram (Square)</option>
          <option value="4:3">4:3 - Classic (Landscape)</option>
          <option value="3:4">3:4 - Portrait</option>
        </select>
      </div>

      <textarea
        value={scriptText}
        onChange={(e) => setScriptText(e.target.value)}
        placeholder="Enter your script..."
        rows={10}
      />

      <button onClick={handleSubmit}>
        Generate Storyboard
      </button>
    </div>
  );
};
```

---

## Use Cases by Platform

### YouTube Videos (16:9)
```json
{
  "style_config": {
    "aspect_ratio": "16:9"
  }
}
```
- Standard YouTube video format
- Best for desktop viewing
- Wide cinematic look

### TikTok / Instagram Reels / Stories (9:16)
```json
{
  "style_config": {
    "aspect_ratio": "9:16"
  }
}
```
- Vertical mobile format
- Full-screen on phones
- Perfect for short-form content

### Instagram Feed Posts (1:1)
```json
{
  "style_config": {
    "aspect_ratio": "1:1"
  }
}
```
- Square format
- Clean, centered composition
- Works well in grid layouts

### Classic / Presentations (4:3)
```json
{
  "style_config": {
    "aspect_ratio": "4:3"
  }
}
```
- Traditional TV format
- Good for presentations
- More vertical space than 16:9

### Portrait Photography (3:4)
```json
{
  "style_config": {
    "aspect_ratio": "3:4"
  }
}
```
- Portrait orientation
- Good for character focus
- Pinterest-friendly

---

## Python Example

```python
import requests

def create_storyboard(script_text: str, aspect_ratio: str = "16:9"):
    """
    Create a storyboard with custom aspect ratio
    
    Args:
        script_text: Your script text
        aspect_ratio: One of "16:9", "9:16", "1:1", "4:3", "3:4"
    """
    response = requests.post(
        'http://localhost:8000/jobs',
        json={
            'script_text': script_text,
            'generate_images': True,
            'style_config': {
                'aspect_ratio': aspect_ratio,
                'art_style': 'professional_youtube_style',
                'character_description': 'content creator'
            }
        }
    )
    
    job = response.json()
    print(f"Job created: {job['id']}")
    print(f"Aspect ratio: {aspect_ratio}")
    return job['id']

# Usage examples
# YouTube
create_storyboard("Hey everyone! Today's video is about AI.", aspect_ratio="16:9")

# TikTok/Stories
create_storyboard("Quick tip about productivity!", aspect_ratio="9:16")

# Instagram
create_storyboard("Check out this cool technique.", aspect_ratio="1:1")
```

---

## cURL Examples

### YouTube Format (16:9)
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Hey everyone! Welcome back to my channel.",
    "generate_images": true,
    "style_config": {
      "aspect_ratio": "16:9",
      "art_style": "professional_youtube_style"
    }
  }'
```

### TikTok Format (9:16)
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Quick productivity hack!",
    "generate_images": true,
    "style_config": {
      "aspect_ratio": "9:16",
      "art_style": "professional_youtube_style"
    }
  }'
```

### Square Format (1:1)
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Here is an interesting fact.",
    "generate_images": true,
    "style_config": {
      "aspect_ratio": "1:1",
      "art_style": "professional_youtube_style"
    }
  }'
```

---

## UI Component Example

Complete React component with visual preview:

```jsx
import { useState } from 'react';
import './AspectRatioSelector.css';

const AspectRatioSelector = ({ value, onChange }) => {
  const ratios = [
    {
      value: '16:9',
      label: 'YouTube',
      icon: '🖥️',
      description: 'Wide screen, landscape',
      preview: 'landscape-wide'
    },
    {
      value: '9:16',
      label: 'TikTok/Stories',
      icon: '📱',
      description: 'Vertical, mobile',
      preview: 'portrait-tall'
    },
    {
      value: '1:1',
      label: 'Instagram',
      icon: '📷',
      description: 'Square format',
      preview: 'square'
    },
    {
      value: '4:3',
      label: 'Classic',
      icon: '📺',
      description: 'Traditional TV',
      preview: 'landscape'
    },
    {
      value: '3:4',
      label: 'Portrait',
      icon: '🖼️',
      description: 'Portrait photo',
      preview: 'portrait'
    }
  ];

  return (
    <div className="aspect-ratio-selector">
      <h3>Image Aspect Ratio</h3>
      
      <div className="ratio-grid">
        {ratios.map((ratio) => (
          <button
            key={ratio.value}
            className={`ratio-option ${value === ratio.value ? 'active' : ''}`}
            onClick={() => onChange(ratio.value)}
          >
            <div className="ratio-icon">{ratio.icon}</div>
            <div className="ratio-label">{ratio.label}</div>
            <div className="ratio-value">{ratio.value}</div>
            <div className="ratio-description">{ratio.description}</div>
            <div className={`ratio-preview ${ratio.preview}`}></div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default AspectRatioSelector;
```

### CSS for Visual Preview

```css
.aspect-ratio-selector {
  margin: 2rem 0;
}

.ratio-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.ratio-option {
  padding: 1.5rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  background: white;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s;
}

.ratio-option:hover {
  border-color: #4CAF50;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.ratio-option.active {
  border-color: #4CAF50;
  background: #f1f8f4;
  font-weight: bold;
}

.ratio-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.ratio-label {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.ratio-value {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.ratio-description {
  font-size: 0.8rem;
  color: #999;
  margin-bottom: 1rem;
}

.ratio-preview {
  margin: 0 auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 4px;
}

/* Visual previews */
.ratio-preview.landscape-wide {
  width: 80px;
  height: 45px; /* 16:9 ratio */
}

.ratio-preview.portrait-tall {
  width: 40px;
  height: 71px; /* 9:16 ratio */
  margin: 0 auto;
}

.ratio-preview.square {
  width: 60px;
  height: 60px; /* 1:1 ratio */
}

.ratio-preview.landscape {
  width: 60px;
  height: 45px; /* 4:3 ratio */
}

.ratio-preview.portrait {
  width: 45px;
  height: 60px; /* 3:4 ratio */
  margin: 0 auto;
}
```

---

## Default Behavior

If you **don't specify** an aspect ratio:
- Default is **16:9** (YouTube format)
- Backwards compatible with existing jobs
- All images in a job use the same aspect ratio

---

## Important Notes

1. ✅ **All images in a job use the same aspect ratio** - specified at job creation
2. 🔄 **Cannot change aspect ratio mid-job** - create a new job if you need different ratios
3. 📐 **Exact dimensions may vary** - Gemini determines optimal resolution
4. 🎨 **Aspect ratio is part of style_config** - saved with the job
5. 🖼️ **Images are returned as base64 data URIs** - decode for actual dimensions

---

## Example: Multi-Platform Workflow

Create storyboards for different platforms from the same script:

```javascript
const script = "Hey everyone! Today's video is about productivity.";

// YouTube version
const youtubeJob = await createJob(script, { aspect_ratio: "16:9" });

// TikTok version
const tiktokJob = await createJob(script, { aspect_ratio: "9:16" });

// Instagram version
const instagramJob = await createJob(script, { aspect_ratio: "1:1" });

async function createJob(script, styleConfig) {
  const response = await fetch('/jobs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      script_text: script,
      generate_images: true,
      style_config: {
        ...styleConfig,
        art_style: 'professional_youtube_style'
      }
    })
  });
  
  return response.json();
}
```

---

## Checking Aspect Ratio in Response

The aspect ratio is saved in the job:

```json
{
  "id": "job-123",
  "status": "completed",
  "options": {
    "style_config": {
      "aspect_ratio": "16:9",
      "art_style": "professional_youtube_style",
      ...
    }
  },
  "scene_ids": ["scene-1", "scene-2", ...]
}
```

Each scene also has the aspect ratio in its visual prompt:

```json
{
  "id": "scene-1",
  "visual_prompt": {
    "style": {
      "aspect_ratio": "16:9",
      ...
    },
    ...
  },
  "image_url": "data:image/png;base64,..."
}
```

---

🎉 **Your images will now be generated in the correct aspect ratio!**

Perfect for creating content optimized for any platform.
