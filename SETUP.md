# Setup Guide

## Prerequisites

- Python 3.11 or higher
- OpenAI API key
- Google Gemini API key
- (Optional) Google Cloud credentials for Google Docs support

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
cd /Users/hectorsilvarobles/Documents/projects/yt/yt-visual-generator-backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env
```

Add the following content to `.env`:

```env
# OpenAI API (for ChatGPT prompt generation)
OPENAI_API_KEY=sk-your-actual-openai-key-here

# Google Gemini API (for image generation)
GOOGLE_GEMINI_API_KEY=your-actual-gemini-key-here
```

### 5. Get API Keys

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy it to your `.env` file

#### Google Gemini API Key
1. Go to https://ai.google.dev/
2. Get API key from Google AI Studio
3. Copy it to your `.env` file

### 6. Run the Server

```bash
# Option 1: Using the run script (recommended)
python run.py

# Option 2: Direct uvicorn
python -m uvicorn app.main:app --reload

# Option 3: As module
python app/main.py
```

### 7. Test the API

Open a new terminal and run:

```bash
# Activate venv first
source venv/bin/activate

# Run test script
python test_api.py
```

### 8. Access Documentation

Open your browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Quick Test

Test with curl:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "script_text": "Hello world. This is a test. AI is amazing.",
    "generate_images": false,
    "style_preset": "bratz_doll_style"
  }'
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the project root:

```bash
cd /Users/hectorsilvarobles/Documents/projects/yt/yt-visual-generator-backend
python run.py
```

### API Key Errors

Make sure your `.env` file is in the project root and contains valid keys:

```bash
ls -la .env
cat .env  # Check content
```

### Port Already in Use

If port 8000 is busy:

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn app.main:app --port 8001
```

## What's Next?

1. Test the basic workflow with your scripts
2. Try different style presets
3. Edit visual prompts and regenerate images
4. Integrate with your frontend

## Project Structure

```
.
├── app/
│   ├── main.py                 # FastAPI app
│   ├── models/                 # Data models
│   ├── api/routes/             # API endpoints
│   ├── services/               # Business logic
│   └── storage/                # Data storage
├── requirements.txt            # Python dependencies
├── run.py                      # Dev server runner
├── test_api.py                 # API test script
├── .env                        # Environment variables (you create this)
├── README.md                   # Documentation
└── context.md                  # Project context
```

## Development Tips

### Hot Reload

The server runs with `--reload` by default, so code changes are reflected immediately.

### Debugging

Add print statements or use Python debugger:

```python
import pdb; pdb.set_trace()
```

### Viewing Logs

Server logs appear in the terminal where you ran `python run.py`.

### Testing Without Images

Set `generate_images: false` in your requests to test faster (skips image generation):

```json
{
  "script_text": "Your script...",
  "generate_images": false
}
```

## Production Considerations

Before deploying to production:

1. **Storage**: Replace in-memory store with a database (PostgreSQL, MongoDB)
2. **Auth**: Add authentication middleware
3. **Rate Limiting**: Implement rate limiting
4. **CORS**: Configure specific allowed origins
5. **Env Vars**: Use proper secrets management
6. **Logging**: Add structured logging
7. **Monitoring**: Add health checks and metrics
8. **Queue**: Use Celery/Redis for long-running jobs

## Support

- Check README.md for API documentation
- Review context.md for project goals
- Open an issue for bugs or questions
