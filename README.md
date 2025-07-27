# Robotics Training Backend

FastAPI-based backend service for managing robotics policy network training jobs. This service handles job submission, queue management, and integrates with Modal for serverless training execution.

## Architecture

- **FastAPI**: REST API server
- **Supabase**: Database for job persistence
- **AWS SQS**: Job queue management
- **Clerk**: Authentication service
- **Modal**: Serverless training execution

## Project Structure
```
app/
├── main.py                 # FastAPI application entry point
├── dependencies/
│   └── auth.py            # Authentication dependencies
├── models/
│   └── job.py             # Pydantic models for job data
├── routers/
│   └── jobs.py            # Job-related API endpoints
└── services/
    ├── clerk_auth.py      # Clerk authentication service
    ├── sqs_client.py      # AWS SQS client wrapper
    └── supabase_client.py # Supabase database client
```

## Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Environment variables**:
```bash
export SUPABASE_URL=your_supabase_url
export SUPABASE_KEY=your_supabase_key
export CLERK_SECRET_KEY=your_clerk_secret
export AWS_ACCESS_KEY_ID=your_aws_key
export AWS_SECRET_ACCESS_KEY=your_aws_secret
export AWS_REGION=us-east-1
export SQS_QUEUE_URL=your_sqs_queue_url
```

3. **Run locally**:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

- `POST /jobs/` - Submit a new training job
- `GET /jobs/` - List all jobs for authenticated user
- `GET /jobs/{job_id}` - Get specific job details
- `PUT /jobs/{job_id}/status` - Update job status (internal use)

## Deployment

The backend is designed to be deployed on AWS ECS. The service automatically:

- Polls SQS for new training jobs
- Triggers Modal training functions
- Updates job status in Supabase
- Handles authentication via Clerk

## Key Features

- **Job Queue Management**: Reliable job processing with SQS
- **Authentication**: Secure user authentication with Clerk
- **Database Integration**: Persistent job storage with Supabase
- **Modal Integration**: Serverless GPU training execution
- **Status Tracking**: Real-time job status updates