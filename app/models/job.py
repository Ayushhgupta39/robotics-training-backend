from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreate(BaseModel):
    name: str
    model_type: Optional[str] = "policy_network"
    dataset_path: Optional[str] = None
    hyperparameters: Optional[dict] = {}


class JobResponse(BaseModel):
    id: str
    name: str
    status: JobStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    modal_call_id: Optional[str] = None
    error_message: Optional[str] = None


class JobUpdate(BaseModel):
    status: Optional[JobStatus] = None
    modal_call_id: Optional[str] = None
    error_message: Optional[str] = None
    training_logs: Optional[str] = None
