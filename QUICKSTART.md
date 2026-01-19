# Quick Start Guide

Get your YT Visual Generator API running in 5 minutes!

## Prerequisites

- Python 3.11+
- OpenAI API key
- Google Gemini API key

## Installation (5 Steps)

### 1. Create Virtual Environment

```bash
cd /Users/hectorsilvarobles/Documents/projects/yt/yt-visual-generator-backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables

Create `.env` file:

```bash
cat > .env << 'EOF'
OPENAI_API_KEY=your-openai-key-here
GOOGLE_GEMINI_API_KEY=your-gemini-key-here
EOF
```

**Replace with your actual keys!**

### 4. Start the Server

```bash
python run.py
```

You should see:
```
✅ Environment variables configured
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test It!

Open a new terminal:

```bash
cd /Users/hectorsilvarobles/Documents/projects/yt/yt-visual-generator-backend
source venv/bin/activate
python test_api.py
```

## Your First Request

### Using curl

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Welcome to my channel. Today we explore AI. This is amazing.",
    "generate_images": false,
    "style_preset": "bratz_doll_style"
  }'
```

### Using Python

```python
import requests

response = requests.post('http://localhost:8000/jobs', json={
    'script_text': 'Welcome to my channel. Today we explore AI. This is amazing.',
    'generate_images': False,
    'style_preset': 'bratz_doll_style'
})

job = response.json()
print(f"Job ID: {job['id']}")
print(f"Status: {job['status']}")
```

## View API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Common Issues

### "OPENAI_API_KEY environment variable is required"

**Fix:** Make sure your `.env` file exists and has valid keys:

```bash
cat .env  # Check content
```

### "Port 8000 already in use"

**Fix:** Kill the process or use a different port:

```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

### Import errors

**Fix:** Make sure you're in the project root and venv is activated:

```bash
cd /Users/hectorsilvarobles/Documents/projects/yt/yt-visual-generator-backend
source venv/bin/activate
python run.py
```

## What's Next?

1. ✅ **Read API_EXAMPLES.md** - See detailed usage examples
2. ✅ **Run example_usage.py** - See Python client examples
3. ✅ **Check PROJECT_SUMMARY.md** - Understand the architecture
4. ✅ **Read SETUP.md** - Detailed setup instructions

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/jobs` | POST | Create new job |
| `/jobs/{id}` | GET | Get job status |
| `/scenes/job/{id}` | GET | Get all scenes |
| `/scenes/{id}` | PATCH | Update scene |
| `/scenes/{id}/regenerate-image` | POST | Regenerate image |

## Example Workflow

```bash
# 1. Create job
JOB_ID=$(curl -s -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"script_text":"Hello world. AI is cool.","generate_images":false}' \
  | jq -r '.id')

echo "Job ID: $JOB_ID"

# 2. Wait a few seconds
sleep 5

# 3. Check status
curl http://localhost:8000/jobs/$JOB_ID | jq '.status'

# 4. Get scenes
curl http://localhost:8000/scenes/job/$JOB_ID | jq '.[].sentence_text'
```

## Tips

- Set `generate_images: false` for faster testing
- Use the interactive docs at `/docs` to explore
- Check logs in the terminal where you ran `python run.py`
- Jobs are processed in the background
- Data is lost when server restarts (in-memory storage)

## Get Help

- **API Docs**: http://localhost:8000/docs
- **README**: Full documentation
- **SETUP**: Detailed setup guide
- **API_EXAMPLES**: Usage examples

---

**You're all set!** 🚀

Start automating your YouTube storyboard generation!
