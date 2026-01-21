# Script Input Guide

The API supports **two ways** to provide your script text:
1. ✏️ **Direct Text Input** (paste script directly)
2. 📄 **File Upload** (upload `.doc`, `.docx`, `.txt` file)

Both methods use the same endpoint!

---

## API Endpoint

```
POST /jobs
```

### Request Body

```json
{
  "script_text": "Your script text here...",
  "generate_images": true,
  "style_config": {
    "art_style": "professional_youtube_style",
    "character_description": "content creator",
    "preferred_settings": ["coffee_shop", "park", "home_office"]
  }
}
```

---

## Option 1: Direct Text Input ✏️

Users can paste their script directly into a text area.

### React Example

```jsx
import { useState } from 'react';

const ScriptTextInput = () => {
  const [scriptText, setScriptText] = useState('');
  const [styleConfig, setStyleConfig] = useState({
    art_style: 'professional_youtube_style',
    character_description: 'content creator',
    lighting: 'natural_lighting',
    color_palette: 'warm_neutral',
    background: 'clean_simple',
    camera_angle: 'medium_shot',
    framing: 'centered',
    preferred_settings: []
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!scriptText.trim()) {
      alert('Please enter your script');
      return;
    }

    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script_text: scriptText,
          generate_images: true,
          style_config: styleConfig
        })
      });

      if (response.ok) {
        const job = await response.json();
        setJobId(job.id);
        console.log('Job created:', job.id);
        
        // Start polling for job status
        pollJobStatus(job.id);
      } else {
        alert('Failed to create job');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error creating job');
    } finally {
      setIsProcessing(false);
    }
  };

  const pollJobStatus = async (jobId) => {
    const checkStatus = async () => {
      const response = await fetch(`http://localhost:8000/jobs/${jobId}`);
      const job = await response.json();
      
      console.log('Job status:', job.status);
      
      if (job.status === 'completed') {
        console.log('Job completed!');
        window.location.href = `/results/${jobId}`;
      } else if (job.status === 'failed') {
        alert('Job failed: ' + job.error_message);
      } else {
        // Still processing, check again in 2 seconds
        setTimeout(checkStatus, 2000);
      }
    };
    
    setTimeout(checkStatus, 2000);
  };

  return (
    <div className="script-input">
      <h2>Create Storyboard from Text</h2>
      
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="scriptText">Paste Your Script:</label>
          <textarea
            id="scriptText"
            value={scriptText}
            onChange={(e) => setScriptText(e.target.value)}
            placeholder="Paste your YouTube script here...&#10;&#10;Example:&#10;Hey everyone! Today we're talking about productivity.&#10;I used to struggle with time management.&#10;But then I discovered these three simple techniques."
            rows={15}
            disabled={isProcessing}
            required
          />
          <small>{scriptText.length} characters</small>
        </div>

        {/* Style Configuration (Optional) */}
        <div className="form-group">
          <label htmlFor="artStyle">Art Style:</label>
          <select
            id="artStyle"
            value={styleConfig.art_style}
            onChange={(e) => setStyleConfig({
              ...styleConfig,
              art_style: e.target.value
            })}
            disabled={isProcessing}
          >
            <option value="professional_youtube_style">Professional YouTube</option>
            <option value="bratz/barbie 3d animation">Bratz/Barbie 3D</option>
            <option value="pixar_style_3d">Pixar Style 3D</option>
            <option value="anime">Anime</option>
            <option value="realistic_photo">Realistic Photo</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="character">Character Description:</label>
          <input
            type="text"
            id="character"
            value={styleConfig.character_description}
            onChange={(e) => setStyleConfig({
              ...styleConfig,
              character_description: e.target.value
            })}
            placeholder="e.g., content creator, teacher, fitness instructor"
            disabled={isProcessing}
          />
        </div>

        <button type="submit" disabled={isProcessing || !scriptText.trim()}>
          {isProcessing ? '⏳ Creating Storyboard...' : '✨ Generate Storyboard'}
        </button>
      </form>

      {jobId && (
        <div className="job-status">
          <p>Job ID: {jobId}</p>
          <p>Processing your script... This may take a few minutes.</p>
        </div>
      )}
    </div>
  );
};

export default ScriptTextInput;
```

---

## Option 2: File Upload 📄

Users can upload `.doc`, `.docx`, or `.txt` files. **Your frontend must read the file and send the text content.**

### React Example with File Upload

```jsx
import { useState } from 'react';

const ScriptFileUpload = () => {
  const [scriptText, setScriptText] = useState('');
  const [fileName, setFileName] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState(null);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileName(file.name);

    try {
      let text = '';
      
      if (file.type === 'text/plain') {
        // Plain text file
        text = await file.text();
      } else if (
        file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        file.name.endsWith('.docx')
      ) {
        // .docx file - you'll need a library like 'mammoth'
        // npm install mammoth
        const mammoth = require('mammoth');
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        text = result.value;
      } else if (
        file.type === 'application/msword' ||
        file.name.endsWith('.doc')
      ) {
        // .doc file (older format)
        // For .doc files, you might need to use a backend service
        // or a library that can parse binary .doc format
        alert('Please convert .doc to .docx or use text input');
        return;
      } else {
        alert('Unsupported file type. Please use .txt, .docx, or paste text directly.');
        return;
      }

      setScriptText(text);
      console.log('Extracted text:', text.substring(0, 100) + '...');
      
    } catch (error) {
      console.error('Error reading file:', error);
      alert('Error reading file. Please try again or paste text directly.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!scriptText.trim()) {
      alert('No script content found');
      return;
    }

    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          script_text: scriptText,
          generate_images: true,
          style_config: {
            art_style: 'professional_youtube_style',
            character_description: 'content creator'
          }
        })
      });

      if (response.ok) {
        const job = await response.json();
        setJobId(job.id);
        // Poll for status...
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Error creating job');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="file-upload">
      <h2>Upload Script File</h2>
      
      <div className="upload-area">
        <input
          type="file"
          accept=".txt,.docx,.doc"
          onChange={handleFileUpload}
          disabled={isProcessing}
        />
        {fileName && <p>File: {fileName}</p>}
      </div>

      {scriptText && (
        <>
          <div className="preview">
            <h3>Preview:</h3>
            <pre>{scriptText.substring(0, 500)}...</pre>
            <p>{scriptText.length} characters extracted</p>
          </div>

          <button onClick={handleSubmit} disabled={isProcessing}>
            {isProcessing ? '⏳ Processing...' : '✨ Generate Storyboard'}
          </button>
        </>
      )}
    </div>
  );
};

export default ScriptFileUpload;
```

### Installing mammoth for .docx parsing

```bash
npm install mammoth
```

---

## Option 3: Combined Interface (Best UX)

Provide both options in one component:

```jsx
import { useState } from 'react';

const ScriptInput = () => {
  const [inputMode, setInputMode] = useState('text'); // 'text' or 'file'
  const [scriptText, setScriptText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      let text = '';
      
      if (file.name.endsWith('.txt')) {
        text = await file.text();
      } else if (file.name.endsWith('.docx')) {
        // Use mammoth to extract text from .docx
        const mammoth = require('mammoth');
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        text = result.value;
      } else {
        alert('Please use .txt or .docx files');
        return;
      }

      setScriptText(text);
      setInputMode('text'); // Switch to text view to show preview
      
    } catch (error) {
      console.error('Error reading file:', error);
      alert('Error reading file');
    }
  };

  const handleSubmit = async () => {
    if (!scriptText.trim()) {
      alert('Please enter or upload a script');
      return;
    }

    setIsProcessing(true);

    try {
      const response = await fetch('http://localhost:8000/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_text: scriptText,
          generate_images: true
        })
      });

      if (response.ok) {
        const job = await response.json();
        console.log('Job created:', job.id);
        // Navigate to results or start polling...
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="script-input-container">
      <h2>Create Your Storyboard</h2>
      
      {/* Mode Selector */}
      <div className="mode-selector">
        <button
          className={inputMode === 'text' ? 'active' : ''}
          onClick={() => setInputMode('text')}
        >
          ✏️ Type Script
        </button>
        <button
          className={inputMode === 'file' ? 'active' : ''}
          onClick={() => setInputMode('file')}
        >
          📄 Upload File
        </button>
      </div>

      {/* Input Area */}
      {inputMode === 'text' ? (
        <div className="text-input-area">
          <textarea
            value={scriptText}
            onChange={(e) => setScriptText(e.target.value)}
            placeholder="Paste your YouTube script here...&#10;&#10;Each sentence will become a scene in your storyboard."
            rows={20}
            disabled={isProcessing}
          />
          <p className="char-count">{scriptText.length} characters</p>
        </div>
      ) : (
        <div className="file-input-area">
          <div className="upload-box">
            <input
              type="file"
              accept=".txt,.docx"
              onChange={handleFileUpload}
              disabled={isProcessing}
              id="fileInput"
            />
            <label htmlFor="fileInput">
              <div className="upload-icon">📁</div>
              <p>Click to upload or drag & drop</p>
              <small>Supports .txt and .docx files</small>
            </label>
          </div>
        </div>
      )}

      {/* Submit Button */}
      {scriptText && (
        <button
          className="submit-btn"
          onClick={handleSubmit}
          disabled={isProcessing || !scriptText.trim()}
        >
          {isProcessing ? (
            <>⏳ Generating Storyboard...</>
          ) : (
            <>✨ Create Storyboard ({scriptText.split('.').length} sentences)</>
          )}
        </button>
      )}
    </div>
  );
};

export default ScriptInput;
```

### CSS Example

```css
.script-input-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}

.mode-selector {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.mode-selector button {
  flex: 1;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.mode-selector button.active {
  border-color: #4CAF50;
  background: #f1f8f4;
  font-weight: bold;
}

.text-input-area textarea {
  width: 100%;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-family: 'Arial', sans-serif;
  font-size: 1rem;
  resize: vertical;
}

.upload-box {
  border: 3px dashed #e0e0e0;
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-box:hover {
  border-color: #4CAF50;
  background: #f1f8f4;
}

.upload-box input[type="file"] {
  display: none;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.submit-btn {
  width: 100%;
  padding: 1rem 2rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: bold;
  cursor: pointer;
  margin-top: 1rem;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  background: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3);
}

.submit-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.char-count {
  text-align: right;
  color: #666;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}
```

---

## Python Client Example

```python
import requests

# Option 1: Direct text
def create_job_from_text(script_text: str):
    response = requests.post(
        'http://localhost:8000/jobs',
        json={
            'script_text': script_text,
            'generate_images': True,
            'style_config': {
                'art_style': 'professional_youtube_style',
                'character_description': 'content creator'
            }
        }
    )
    
    job = response.json()
    print(f"Job created: {job['id']}")
    return job['id']

# Option 2: From file
def create_job_from_file(file_path: str):
    with open(file_path, 'r', encoding='utf-8') as f:
        script_text = f.read()
    
    return create_job_from_text(script_text)

# Usage
job_id = create_job_from_text("""
Hey everyone! Today we're talking about productivity.
I used to struggle with time management.
But then I discovered these three techniques.
""")

# Or from file
job_id = create_job_from_file('my_script.txt')
```

---

## cURL Examples

### Direct Text

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Hey everyone! Today we are talking about AI. It is fascinating how far we have come.",
    "generate_images": true,
    "style_config": {
      "art_style": "professional_youtube_style",
      "character_description": "tech content creator"
    }
  }'
```

### From File

```bash
# Read file content and send it
SCRIPT_TEXT=$(cat my_script.txt)

curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d "{
    \"script_text\": \"$SCRIPT_TEXT\",
    \"generate_images\": true
  }"
```

---

## Key Points

1. ✅ **Backend already supports both methods** - just send `script_text`
2. 📄 **File parsing happens in the frontend** - extract text from `.doc`/`.docx` before sending
3. ✏️ **Direct text is simpler** - no parsing needed
4. 🎨 **Style config is optional** - defaults are provided
5. 🔄 **Same endpoint for both** - `POST /jobs` with `script_text`

---

## File Parsing Libraries

### For JavaScript/React:
- **mammoth** - Parse `.docx` files
  ```bash
  npm install mammoth
  ```

- **docx-preview** - Preview and extract .docx
  ```bash
  npm install docx-preview
  ```

### For Python (if you need backend parsing):
- **python-docx** - Parse `.docx` files
  ```bash
  pip install python-docx
  ```

- **textract** - Extract text from various formats
  ```bash
  pip install textract
  ```

---

## Response Format

Both methods return the same response:

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2026-01-20T01:00:00",
  "status": "pending",
  "script_text": "Your script...",
  "options": {
    "generate_images": true,
    "style_config": {
      "art_style": "professional_youtube_style",
      "character_description": "content creator"
    }
  },
  "scene_ids": [],
  "cost": {
    "total_cost": 0.0
  }
}
```

Then poll the job status:

```
GET /jobs/{job_id}
```

Until `status` becomes `"completed"` or `"failed"`.

---

🎉 **Both options work with the same backend!** Choose what's best for your users.
