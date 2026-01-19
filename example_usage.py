#!/usr/bin/env python3
"""
Example usage of the YT Visual Generator API

This script demonstrates the complete workflow:
1. Create a job with a script
2. Poll for completion
3. Retrieve scenes
4. Update a scene's prompt
5. Regenerate an image
"""
import requests
import time
import json
from typing import Optional, Dict, List

BASE_URL = "http://localhost:8000"


class VisualGeneratorClient:
    """Simple client for the Visual Generator API"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
    
    def create_job(
        self,
        script_text: str,
        generate_images: bool = True,
        style_preset: str = "bratz_doll_style"
    ) -> Dict:
        """Create a new storyboard generation job"""
        payload = {
            "script_text": script_text,
            "generate_images": generate_images,
            "style_preset": style_preset
        }
        
        response = requests.post(f"{self.base_url}/jobs", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_job(self, job_id: str) -> Dict:
        """Get job status"""
        response = requests.get(f"{self.base_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def wait_for_job(self, job_id: str, timeout: int = 300, poll_interval: int = 2) -> Dict:
        """Wait for job to complete"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            job = self.get_job(job_id)
            status = job['status']
            
            print(f"Job status: {status}")
            
            if status in ['completed', 'failed']:
                return job
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job did not complete within {timeout} seconds")
    
    def get_scenes(self, job_id: str) -> List[Dict]:
        """Get all scenes for a job"""
        response = requests.get(f"{self.base_url}/scenes/job/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def get_scene(self, scene_id: str) -> Dict:
        """Get a specific scene"""
        response = requests.get(f"{self.base_url}/scenes/{scene_id}")
        response.raise_for_status()
        return response.json()
    
    def update_scene(self, scene_id: str, visual_prompt: Dict) -> Dict:
        """Update a scene's visual prompt"""
        payload = {"visual_prompt": visual_prompt}
        response = requests.patch(f"{self.base_url}/scenes/{scene_id}", json=payload)
        response.raise_for_status()
        return response.json()
    
    def regenerate_image(self, scene_id: str) -> Dict:
        """Regenerate image for a scene"""
        response = requests.post(f"{self.base_url}/scenes/{scene_id}/regenerate-image")
        response.raise_for_status()
        return response.json()


def example_basic_workflow():
    """Example: Basic workflow with text script"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Workflow")
    print("=" * 70)
    
    client = VisualGeneratorClient()
    
    # Sample script
    script = """
    Welcome to my channel where we explore the future of technology.
    Today we're diving deep into artificial intelligence and machine learning.
    These technologies are transforming every industry you can imagine.
    Let's explore what this means for our future together.
    """
    
    # Step 1: Create job
    print("\n1. Creating job...")
    job = client.create_job(
        script_text=script.strip(),
        generate_images=False,  # Set to True to generate images
        style_preset="bratz_doll_style"
    )
    job_id = job['id']
    print(f"   Job created: {job_id}")
    
    # Step 2: Wait for completion
    print("\n2. Waiting for job to complete...")
    job = client.wait_for_job(job_id)
    print(f"   Job completed with status: {job['status']}")
    
    # Step 3: Get scenes
    print("\n3. Retrieving scenes...")
    scenes = client.get_scenes(job_id)
    print(f"   Found {len(scenes)} scenes")
    
    # Display scenes
    for scene in scenes:
        print(f"\n   Scene {scene['index']}:")
        print(f"   Text: {scene['sentence_text']}")
        if scene['visual_prompt']:
            prompt = scene['visual_prompt']
            print(f"   Style: {prompt['style']['art_style']}")
            print(f"   Characters: {len(prompt['characters'])}")
            if prompt['characters']:
                print(f"   Main character: {prompt['characters'][0]['description']}")
    
    print("\n✅ Basic workflow complete!")
    return job_id, scenes


def example_edit_and_regenerate(scene_id: str, visual_prompt: Dict):
    """Example: Edit a prompt and regenerate image"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Edit Prompt and Regenerate")
    print("=" * 70)
    
    client = VisualGeneratorClient()
    
    # Modify the prompt
    print("\n1. Updating scene prompt...")
    visual_prompt['style']['lighting'] = 'dramatic_lighting'
    visual_prompt['characters'][0]['expression'] = 'excited'
    
    updated_scene = client.update_scene(scene_id, visual_prompt)
    print(f"   Scene updated: {scene_id}")
    print(f"   New lighting: {updated_scene['visual_prompt']['style']['lighting']}")
    
    # Regenerate image
    print("\n2. Regenerating image...")
    scene = client.regenerate_image(scene_id)
    print(f"   Image regeneration started")
    print(f"   Status: {scene['image_status']}")
    
    print("\n✅ Edit and regenerate complete!")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("YT Visual Generator API - Usage Examples")
    print("=" * 70)
    print("\nMake sure the API server is running at http://localhost:8000")
    print("\nPress Ctrl+C to stop at any time")
    print()
    
    try:
        # Example 1: Basic workflow
        job_id, scenes = example_basic_workflow()
        
        # Example 2: Edit and regenerate (if we have scenes)
        if scenes and len(scenes) > 0:
            first_scene = scenes[0]
            if first_scene.get('visual_prompt'):
                example_edit_and_regenerate(
                    first_scene['id'],
                    first_scene['visual_prompt']
                )
        
        print("\n" + "=" * 70)
        print("All examples completed!")
        print("=" * 70)
        print(f"\nYour job ID: {job_id}")
        print(f"View it at: http://localhost:8000/docs#/jobs/get_job_jobs__job_id__get")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API server")
        print("   Make sure the server is running: python run.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
