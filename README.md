# YT Visual Generator Backend

A FastAPI backend service that converts YouTube scripts into visual storyboards with AI-generated prompts and images.

## Features

- 📝 **Script Input**: Accepts raw script text
- 🤖 **AI-Powered Prompts**: Uses ChatGPT to generate structured visual prompts
- 🎨 **Image Generation**: Creates images using Google Gemini (Nano Banana)
- 🎭 **Custom Styles**: Full control over art style, lighting, character, and more
- 💰 **Cost Tracking**: Automatic tracking of API costs (OpenAI + Gemini)
- 🔄 **Background Processing**: Asynchronous job processing
- ✏️ **Editable Prompts**: Modify and regenerate specific scenes
- 📊 **RESTful API**: Clean, well-documented endpoints

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_GEMINI_API_KEY=your-gemini-api-key-here
```

### 3. Run the Server

```bash
python -m uvicorn app.main:app --reload
```

Or use the run script:

```bash
python run.py
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Jobs

#### Create Job
```http
POST /jobs
Content-Type: application/json

{
  "script_text": "Your script here...",
  "generate_images": true,
  "style_config": {
    "art_style": "realistic",
    "lighting": "natural_lighting",
    "color_palette": "warm_neutral",
    "background": "clean_simple",
    "character_description": "your persona description",
    "camera_angle": "medium_shot",
    "framing": "centered"
  }
}
```

**Note:** `style_config` is optional. If omitted, uses generic defaults.

#### Get Job Status
```http
GET /jobs/{job_id}
```

#### List All Jobs
```http
GET /jobs
```

### Scenes

#### Get Job Scenes
```http
GET /scenes/job/{job_id}
```

#### Get Single Scene
```http
GET /scenes/{scene_id}
```

#### Update Scene Prompt
```http
PATCH /scenes/{scene_id}
Content-Type: application/json

{
  "visual_prompt": {
    "scene_id": "...",
    "sentence_text": "...",
    "style": { ... },
    "characters": [ ... ],
    "composition": { ... }
  }
}
```

#### Regenerate Scene Image
```http
POST /scenes/{scene_id}/regenerate-image
```

## Workflow

1. **Create a Job**: Submit your script text
2. **Wait for Processing**: Job goes through stages:
   - `pending` → `generating_prompts` → `generating_images` → `completed`
3. **Review Scenes**: Get all generated scenes with prompts and images
4. **Edit if Needed**: Update visual prompts and regenerate images
5. **Use Results**: Integrate storyboard data into your workflow

## Documentation

- **[SETUP.md](SETUP.md)** - Detailed setup instructions
- **[API_EXAMPLES.md](API_EXAMPLES.md)** - Complete API examples
- **[CUSTOM_STYLE_GUIDE.md](CUSTOM_STYLE_GUIDE.md)** - Style customization guide
- **[COST_TRACKING.md](COST_TRACKING.md)** - Cost tracking & optimization
- **[UI_INTEGRATION_GUIDE.md](UI_INTEGRATION_GUIDE.md)** - Frontend integration guide

## Development

### Project Structure

```
app/
├── main.py              # FastAPI application
├── models/              # Pydantic models
│   ├── job.py
│   └── scene.py
├── api/routes/          # API endpoints
│   ├── jobs.py
│   └── scenes.py
├── services/            # Business logic
│   ├── llm_service.py
│   ├── image_service.py
│   └── job_processor.py
└── storage/             # Data persistence
    └── memory_store.py
```

### Running Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## Cost Tracking

Every job automatically tracks costs:

```json
{
  "id": "job-123",
  "status": "completed",
  "cost": {
    "total_cost": 0.00621,
    "prompt_generation_cost": 0.00045,
    "image_generation_cost": 0.00576,
    "num_prompts_generated": 18,
    "num_images_generated": 18
  }
}
```

**Typical Costs:**
- 60-second video (~10 scenes): $0.005
- 3-minute video (~30 scenes): $0.014
- 10-minute video (~100 scenes): $0.047

See [COST_TRACKING.md](COST_TRACKING.md) for details.

## Notes

- **In-Memory Storage**: Data is lost on server restart (suitable for MVP)
- **No Authentication**: Add auth middleware for production
- **Rate Limiting**: Not implemented (add for production)
- **Background Tasks**: Uses FastAPI's built-in background tasks (sufficient for MVP)

## Tech Stack

- **Framework**: FastAPI
- **Models**: Pydantic
- **Server**: Uvicorn
- **LLM**: OpenAI ChatGPT (gpt-4o-mini)
- **Image Gen**: Google Gemini 2.5 Flash

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
