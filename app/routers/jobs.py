from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.job import JobCreate, JobResponse, JobUpdate
from app.services.supabase_client import supabase_service
from app.services.sqs_client import sqs_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post(
    "/submit-job", response_model=JobResponse, status_code=status.HTTP_201_CREATED
)
async def submit_job(job: JobCreate):
    """
    Submit a new training job
    1. Store in Supabase with status 'pending'
    2. Push job ID to SQS queue
    """
    try:
        # Create job in Supabase
        created_job = await supabase_service.create_job(job)

        # Prepare job data for queue
        job_data = {
            "name": job.name,
            "model_type": job.model_type,
            "dataset_path": job.dataset_path,
            "hyperparameters": job.hyperparameters,
        }

        # Send to SQS queue
        queue_success = await sqs_service.send_job_to_queue(
            job_id=created_job.id, job_data=job_data
        )

        if not queue_success:
            # If queue fails, we could update job status to failed
            await supabase_service.update_job(
                created_job.id,
                JobUpdate(status="failed", error_message="Failed to queue job"),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Job created but failed to queue for processing",
            )

        print(f"Job {created_job.id} created and queued successfully")
        return created_job

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit job: {str(e)}",
        )


@router.get("/", response_model=List[JobResponse])
async def get_all_jobs():
    """Get all jobs for dashboard"""
    try:
        jobs = await supabase_service.get_all_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch jobs: {str(e)}",
        )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    """Get specific job by ID"""
    try:
        job = await supabase_service.get_job_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        return job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch job: {str(e)}",
        )


@router.put("/{job_id}/status", response_model=JobResponse)
async def update_job_status(job_id: str, update: JobUpdate):
    """Update job status (used by Modal or other services)"""
    try:
        updated_job = await supabase_service.update_job(job_id, update)
        if not updated_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
            )
        return updated_job
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update job: {str(e)}",
        )
