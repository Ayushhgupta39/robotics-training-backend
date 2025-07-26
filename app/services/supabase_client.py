from supabase import create_client, Client
import os
from typing import List, Optional
from app.models.job import JobCreate, JobResponse, JobUpdate


class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        if not url or not key:
            raise ValueError("Supabase URL and Service Key must be set")

        self.supabase: Client = create_client(url, key)

    async def create_job(self, job: JobCreate) -> JobResponse:
        """Create a new job in Supabase"""
        try:
            result = (
                self.supabase.table("jobs")
                .insert(
                    {
                        "name": job.name,
                        "status": "pending",
                        "model_type": job.model_type,
                        "dataset_path": job.dataset_path,
                        "hyperparameters": job.hyperparameters,
                    }
                )
                .execute()
            )

            if result.data:
                return JobResponse(**result.data[0])
            else:
                raise Exception("Failed to create job")

        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_all_jobs(self) -> List[JobResponse]:
        """Get all jobs from Supabase"""
        try:
            result = (
                self.supabase.table("jobs")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return [JobResponse(**job) for job in result.data]
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_job_by_id(self, job_id: str) -> Optional[JobResponse]:
        """Get a specific job by ID"""
        try:
            result = self.supabase.table("jobs").select("*").eq("id", job_id).execute()
            if result.data:
                return JobResponse(**result.data[0])
            return None
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    async def update_job(self, job_id: str, update: JobUpdate) -> Optional[JobResponse]:
        """Update a job in Supabase"""
        try:
            update_data = {k: v for k, v in update.dict().items() if v is not None}

            result = (
                self.supabase.table("jobs")
                .update(update_data)
                .eq("id", job_id)
                .execute()
            )

            if result.data:
                return JobResponse(**result.data[0])
            return None
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")


# Global instance
supabase_service = SupabaseService()
