# Scene Editing Guide

## Problem Solved

Previously, editing a scene required:
1. Getting the complex `VisualPrompt` JSON (nested objects with camera, characters, expressions, poses, etc.)
2. Manually editing the JSON
3. Sending the entire structure back

**Now you can just send simple text instructions!** 🎉

## New Endpoint: Regenerate with Instructions

```
POST /scenes/{scene_id}/regenerate-with-instruction
```

### Request Body

```json
{
  "instruction": "make the character smile"
}
```

### Example Instructions

```javascript
// Simple modifications
"make the character smile"
"add a laptop on the desk"
"remove the phone"
"change background to coffee shop"
"make it darker/lighter"
"zoom in on the face"
"add more people in background"
"change to outdoor park setting"
"make character look sad"
"add sunlight through window"
```

## UI Implementation Examples

### Option 1: Simple Text Input

```jsx
const SceneEditor = ({ sceneId }) => {
  const [instruction, setInstruction] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);
  
  const handleRegenerate = async () => {
    if (!instruction.trim()) {
      alert('Please enter an instruction');
      return;
    }
    
    setIsRegenerating(true);
    
    try {
      const response = await fetch(
        `/scenes/${sceneId}/regenerate-with-instruction`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction })
        }
      );
      
      if (response.ok) {
        // Poll for the updated scene
        pollForUpdatedScene(sceneId);
      }
    } catch (error) {
      console.error('Regeneration failed:', error);
    } finally {
      setIsRegenerating(false);
    }
  };
  
  return (
    <div className="scene-editor">
      <h3>Edit This Scene</h3>
      <input
        type="text"
        value={instruction}
        onChange={(e) => setInstruction(e.target.value)}
        placeholder="e.g., make character smile, add laptop, change to park..."
        disabled={isRegenerating}
      />
      <button onClick={handleRegenerate} disabled={isRegenerating}>
        {isRegenerating ? 'Regenerating...' : 'Regenerate Scene'}
      </button>
    </div>
  );
};
```

### Option 2: Quick Action Buttons

```jsx
const QuickEditButtons = ({ sceneId }) => {
  const quickActions = [
    { label: "😊 Make Smile", instruction: "make the character smile" },
    { label: "💻 Add Laptop", instruction: "add a laptop on the desk" },
    { label: "🌳 Change to Park", instruction: "change setting to outdoor park" },
    { label: "🔍 Zoom In", instruction: "zoom in on the character's face" },
    { label: "☀️ More Light", instruction: "add more natural lighting" },
  ];
  
  const handleQuickAction = async (instruction) => {
    await fetch(`/scenes/${sceneId}/regenerate-with-instruction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction })
    });
    
    // Poll for updates...
  };
  
  return (
    <div className="quick-actions">
      <h4>Quick Edits</h4>
      {quickActions.map((action, idx) => (
        <button
          key={idx}
          onClick={() => handleQuickAction(action.instruction)}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
};
```

### Option 3: Categorized Dropdown

```jsx
const CategorizedEditor = ({ sceneId }) => {
  const [category, setCategory] = useState('');
  const [specificAction, setSpecificAction] = useState('');
  
  const categories = {
    expression: [
      { label: "Smiling", instruction: "make character smile" },
      { label: "Sad", instruction: "make character look sad" },
      { label: "Surprised", instruction: "make character look surprised" },
      { label: "Thoughtful", instruction: "make character look thoughtful" },
    ],
    props: [
      { label: "Add Laptop", instruction: "add a laptop" },
      { label: "Add Phone", instruction: "add a phone" },
      { label: "Add Coffee", instruction: "add a coffee cup" },
      { label: "Add Book", instruction: "add a book" },
    ],
    setting: [
      { label: "Coffee Shop", instruction: "change setting to coffee shop" },
      { label: "Park", instruction: "change setting to park" },
      { label: "Office", instruction: "change setting to office" },
      { label: "Home", instruction: "change setting to cozy home" },
    ],
    camera: [
      { label: "Zoom In", instruction: "zoom in closer on face" },
      { label: "Zoom Out", instruction: "zoom out to show more environment" },
      { label: "Profile View", instruction: "change to profile view" },
    ],
    lighting: [
      { label: "More Light", instruction: "add more natural lighting" },
      { label: "Darker", instruction: "make it darker and moodier" },
      { label: "Sunset", instruction: "add warm sunset lighting" },
    ]
  };
  
  const handleRegenerate = async () => {
    if (!specificAction) return;
    
    await fetch(`/scenes/${sceneId}/regenerate-with-instruction`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction: specificAction.instruction })
    });
    
    // Poll for updates...
  };
  
  return (
    <div className="categorized-editor">
      <select onChange={(e) => {
        setCategory(e.target.value);
        setSpecificAction('');
      }}>
        <option value="">Select Category</option>
        <option value="expression">😊 Expression</option>
        <option value="props">🎯 Props</option>
        <option value="setting">🏠 Setting</option>
        <option value="camera">📷 Camera</option>
        <option value="lighting">💡 Lighting</option>
      </select>
      
      {category && (
        <select onChange={(e) => setSpecificAction(categories[category][e.target.value])}>
          <option value="">Select Action</option>
          {categories[category].map((action, idx) => (
            <option key={idx} value={idx}>{action.label}</option>
          ))}
        </select>
      )}
      
      <button onClick={handleRegenerate} disabled={!specificAction}>
        Apply Change
      </button>
    </div>
  );
};
```

## Polling for Updated Scene

After calling regenerate, you need to poll for the updated scene:

```javascript
const pollForUpdatedScene = async (sceneId) => {
  const maxAttempts = 30; // 30 seconds max
  let attempts = 0;
  
  const poll = async () => {
    attempts++;
    
    const scene = await fetch(`/scenes/${sceneId}`).then(r => r.json());
    
    if (scene.image_status === 'generated') {
      // Success! Update UI with new image
      updateSceneInUI(scene);
      return;
    }
    
    if (scene.image_status === 'failed') {
      // Failed
      alert(`Regeneration failed: ${scene.last_error}`);
      return;
    }
    
    if (attempts < maxAttempts) {
      // Still processing, try again in 1 second
      setTimeout(poll, 1000);
    } else {
      // Timeout
      alert('Regeneration timed out');
    }
  };
  
  // Start polling after a short delay
  setTimeout(poll, 1000);
};
```

## Complete Example

```javascript
const SceneCard = ({ scene }) => {
  const [instruction, setInstruction] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [currentImage, setCurrentImage] = useState(scene.image_url);
  
  const handleRegenerate = async () => {
    if (!instruction.trim()) return;
    
    setIsRegenerating(true);
    
    try {
      // Send instruction
      const response = await fetch(
        `/scenes/${scene.id}/regenerate-with-instruction`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ instruction: instruction.trim() })
        }
      );
      
      if (response.ok) {
        // Poll for result
        pollForUpdate();
      }
    } catch (error) {
      console.error('Failed:', error);
      setIsRegenerating(false);
    }
  };
  
  const pollForUpdate = async () => {
    const maxAttempts = 30;
    let attempts = 0;
    
    const check = async () => {
      attempts++;
      const updated = await fetch(`/scenes/${scene.id}`).then(r => r.json());
      
      if (updated.image_status === 'generated' && updated.image_url !== currentImage) {
        // New image!
        setCurrentImage(updated.image_url);
        setIsRegenerating(false);
        setIsEditing(false);
        setInstruction('');
      } else if (updated.image_status === 'failed') {
        alert('Failed: ' + updated.last_error);
        setIsRegenerating(false);
      } else if (attempts < maxAttempts) {
        setTimeout(check, 1000);
      } else {
        alert('Timeout');
        setIsRegenerating(false);
      }
    };
    
    setTimeout(check, 1000);
  };
  
  return (
    <div className="scene-card">
      <img src={currentImage} alt={scene.sentence_text} />
      <p>{scene.sentence_text}</p>
      
      {!isEditing ? (
        <button onClick={() => setIsEditing(true)}>
          ✏️ Edit Scene
        </button>
      ) : (
        <div className="edit-panel">
          <input
            type="text"
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="e.g., make character smile"
            disabled={isRegenerating}
          />
          <button onClick={handleRegenerate} disabled={isRegenerating || !instruction}>
            {isRegenerating ? '⏳ Regenerating...' : '✨ Apply'}
          </button>
          <button onClick={() => setIsEditing(false)} disabled={isRegenerating}>
            Cancel
          </button>
        </div>
      )}
    </div>
  );
};
```

## Instruction Examples by Category

### Expressions
- "make character smile warmly"
- "make character look worried"
- "make character look determined"
- "add a slight smile"

### Props/Objects
- "add a laptop on the desk"
- "add coffee cup in hand"
- "add phone on table"
- "add book character is reading"
- "remove the phone"

### Setting/Background
- "change to coffee shop"
- "change to outdoor park"
- "change to modern office"
- "add window in background"
- "make it an empty room"

### Camera
- "zoom in on face"
- "zoom out to show full body"
- "change to profile view"
- "change to overhead angle"

### Lighting
- "add more natural light"
- "make it darker and moodier"
- "add sunset lighting"
- "add window light from left"

### Multiple Changes
- "make character smile and add a laptop"
- "change to park and zoom out"
- "add coffee shop background with warm lighting"

## API Response

The endpoint returns immediately with the scene object (status will be `pending`):

```json
{
  "id": "scene-123",
  "image_status": "pending",
  "sentence_text": "...",
  "visual_prompt": { ... }
}
```

You need to **poll** the scene endpoint to get the updated image:

```
GET /scenes/{scene_id}
```

When complete:
```json
{
  "id": "scene-123",
  "image_status": "generated",
  "image_url": "data:image/png;base64,...",  // NEW IMAGE!
  "sentence_text": "...",
  "visual_prompt": { ... }  // UPDATED PROMPT!
}
```

## Old Endpoint Still Available

The complex JSON editing is still available if you need fine-grained control:

```
PATCH /scenes/{scene_id}
POST /scenes/{scene_id}/regenerate-image
```

But the new instruction-based endpoint is much easier! 🎉

---

**Questions?** Test the new endpoint and let us know how it works!
