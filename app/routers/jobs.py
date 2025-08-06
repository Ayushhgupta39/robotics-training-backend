from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.job import JobCreate, JobResponse, JobUpdate
from app.services.supabase_client import supabase_service
from app.services.sqs_client import sqs_service
from app.dependencies.auth import get_current_user_id, get_optional_user_id

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post(
    "/submit-job", response_model=JobResponse, status_code=status.HTTP_201_CREATED
)
async def submit_job(
    job: JobCreate, current_user_id: str = Depends(get_current_user_id)
):
    """
    Submit a new training job (requires authentication)
    1. Store in Supabase with status 'pending' and user_id
    2. Push job ID to SQS queue
    """
    try:
        # Create job in Supabase with user_id
        created_job = await supabase_service.create_job(job, current_user_id)

        # Prepare job data for queue
        job_data = {
            "name": job.name,
            "model_type": job.model_type,
            "dataset_path": job.dataset_path,
            "hyperparameters": job.hyperparameters,
            "user_id": current_user_id,
        }

        # Send to SQS queue
        queue_success = await sqs_service.send_job_to_queue(
            job_id=created_job.id, job_data=job_data
        )

        if not queue_success:
            # If queue fails, update job status to failed
            await supabase_service.update_job(
                created_job.id,
                JobUpdate(status="failed", error_message="Failed to queue job"),
                current_user_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Job created but failed to queue for processing",
            )

        print(
            f"Job {created_job.id} created and queued successfully for user {current_user_id}"
        )
        return created_job

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}",
        )


@router.get("/", response_model=List[JobResponse])
async def get_user_jobs(current_user_id: str = Depends(get_current_user_id)):
    """Get all jobs for the authenticated user"""
    try:
        jobs = await supabase_service.get_jobs_by_user(current_user_id)
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch jobs: {str(e)}",
        )


@router.get("/all", response_model=List[JobResponse])
async def get_all_jobs():
    """
    Get all jobs (admin endpoint - no authentication for now)
    This can be used by Modal or other services to process jobs
    """
    try:
        jobs = await supabase_service.get_all_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch jobs: {str(e)}",
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, current_user_id: str = Depends(get_current_user_id)):
    """Get specific job by ID (only if it belongs to the user)"""
    try:
        job = await supabase_service.get_job_by_id(job_id, current_user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found or access denied",
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch job: {str(e)}",
        )
