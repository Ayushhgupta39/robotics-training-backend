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

    async def create_job(self, job: JobCreate, user_id: str) -> JobResponse:
        """Create a new job in Supabase with user_id"""
        try:
            result = (
                self.supabase.table("jobs")
                .insert(
                    {
                        "user_id": user_id,
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

    async def get_jobs_by_user(self, user_id: str) -> List[JobResponse]:
        """Get all jobs for a specific user"""
        try:
            result = (
                self.supabase.table("jobs")
                .select("*")
                .eq("user_id", user_id)  # Filter by user_id
                .order("created_at", desc=True)
                .execute()
            )
            return [JobResponse(**job) for job in result.data]
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    async def get_all_jobs(self) -> List[JobResponse]:
        """Get all jobs (admin function - keeping for backwards compatibility)"""
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

    async def get_job_by_id(
        self, job_id: str, user_id: Optional[str] = None
    ) -> Optional[JobResponse]:
        """Get a specific job by ID, optionally filtered by user_id"""
        try:
            query = self.supabase.table("jobs").select("*").eq("id", job_id)

            # If user_id is provided, also filter by user
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if result.data:
                return JobResponse(**result.data[0])
            return None
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")

    async def update_job(
        self, job_id: str, update: JobUpdate, user_id: Optional[str] = None
    ) -> Optional[JobResponse]:
        """Update a job in Supabase, optionally filtered by user_id"""
        try:
            update_data = {k: v for k, v in update.dict().items() if v is not None}

            query = self.supabase.table("jobs").update(update_data).eq("id", job_id)

            # If user_id is provided, also filter by user (for security)
            if user_id:
                query = query.eq("user_id", user_id)

            result = query.execute()

            if result.data:
                return JobResponse(**result.data[0])
            return None
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")


# Global instance
supabase_service = SupabaseService()
