#!/usr/bin/env python3
"""
Simple API test script
Run this after starting the server to test the endpoints
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()


def test_create_job():
    """Test job creation with sample script"""
    print("Creating a test job...")
    
    sample_script = """
    Welcome to my channel. Today we're going to talk about artificial intelligence.
    AI is transforming the way we work and live. It's an exciting time to be alive.
    Let's dive into the details and see what the future holds.
    """
    
    payload = {
        "script_text": sample_script.strip(),
        "generate_images": False,  # Set to False for quick testing without images
        "style_preset": "bratz_doll_style"
    }
    
    response = requests.post(f"{BASE_URL}/jobs", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        job = response.json()
        print(f"Job created: {job['id']}")
        print(f"Status: {job['status']}")
        return job['id']
    else:
        print(f"Error: {response.text}")
        return None


def test_get_job(job_id):
    """Test getting job status"""
    print(f"\nGetting job status for {job_id}...")
    
    # Poll for completion
    max_attempts = 30
    for attempt in range(max_attempts):
        response = requests.get(f"{BASE_URL}/jobs/{job_id}")
        
        if response.status_code == 200:
            job = response.json()
            status = job['status']
            print(f"Attempt {attempt + 1}: Status = {status}")
            
            if status in ['completed', 'failed']:
                print(f"\nJob {status}!")
                if status == 'failed':
                    print(f"Error: {job.get('error_message')}")
                return job
            
            time.sleep(2)
        else:
            print(f"Error: {response.status_code}")
            return None
    
    print("Timeout waiting for job completion")
    return None


def test_get_scenes(job_id):
    """Test getting scenes for a job"""
    print(f"\nGetting scenes for job {job_id}...")
    
    response = requests.get(f"{BASE_URL}/scenes/job/{job_id}")
    
    if response.status_code == 200:
        scenes = response.json()
        print(f"Found {len(scenes)} scenes")
        
        for scene in scenes:
            print(f"\nScene {scene['index']}:")
            print(f"  Text: {scene['sentence_text'][:60]}...")
            print(f"  Has prompt: {scene['visual_prompt'] is not None}")
            print(f"  Image status: {scene['image_status']}")
        
        return scenes
    else:
        print(f"Error: {response.status_code}")
        return None


def main():
    """Run all tests"""
    print("=" * 60)
    print("YT Visual Generator API Test")
    print("=" * 60)
    print()
    
    # Test health
    test_health()
    
    # Create job
    job_id = test_create_job()
    if not job_id:
        print("Failed to create job. Exiting.")
        return
    
    # Wait and check status
    time.sleep(3)
    job = test_get_job(job_id)
    
    if job:
        # Get scenes
        scenes = test_get_scenes(job_id)
        
        if scenes and len(scenes) > 0:
            print("\n" + "=" * 60)
            print("✅ All tests passed!")
            print(f"Job ID: {job_id}")
            print(f"Scenes generated: {len(scenes)}")
            print("=" * 60)


if __name__ == "__main__":
    main()
