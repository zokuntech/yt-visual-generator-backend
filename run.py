#!/usr/bin/env python3
"""
Development server runner for YT Visual Generator API
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_vars():
    """Check if required environment variables are set"""
    required = ["OPENAI_API_KEY", "GOOGLE_GEMINI_API_KEY"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set them in your .env file")
        return False
    
    print("✅ Environment variables configured")
    return True


def main():
    """Run the development server"""
    print("🚀 Starting YT Visual Generator API...")
    print()
    
    if not check_env_vars():
        sys.exit(1)
    
    print("\n📚 API Documentation will be available at:")
    print("   http://localhost:8000/docs")
    print()
    
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
