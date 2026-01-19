from typing import Dict, List, Optional
from app.models import Job, Scene


class MemoryStore:
    """In-memory storage for jobs and scenes"""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.scenes: Dict[str, Scene] = {}
    
    # Job operations
    def save_job(self, job: Job) -> Job:
        """Save or update a job"""
        self.jobs[job.id] = job
        return job
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by ID"""
        return self.jobs.get(job_id)
    
    def list_jobs(self) -> List[Job]:
        """List all jobs"""
        return list(self.jobs.values())
    
    # Scene operations
    def save_scene(self, scene: Scene) -> Scene:
        """Save or update a scene"""
        self.scenes[scene.id] = scene
        return scene
    
    def get_scene(self, scene_id: str) -> Optional[Scene]:
        """Retrieve a scene by ID"""
        return self.scenes.get(scene_id)
    
    def get_scenes_by_job(self, job_id: str) -> List[Scene]:
        """Retrieve all scenes for a job"""
        return [
            scene for scene in self.scenes.values()
            if scene.job_id == job_id
        ]
    
    def delete_scene(self, scene_id: str) -> bool:
        """Delete a scene"""
        if scene_id in self.scenes:
            del self.scenes[scene_id]
            return True
        return False


# Global singleton instance
store = MemoryStore()
