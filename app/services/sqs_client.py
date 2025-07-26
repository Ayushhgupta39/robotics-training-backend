import boto3
import json
import os
from typing import Dict, Any
from botocore.exceptions import ClientError


class SQSService:
    def __init__(self):
        try:
            self.sqs = boto3.client(
                "sqs",
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
            self.queue_url = os.getenv("SQS_QUEUE_URL")
            # Check if queue_url is provided and not the placeholder
            self.is_configured = bool(
                self.queue_url and self.queue_url != "your_sqs_queue_url"
            )
            if not self.is_configured:
                print(
                    "Warning: AWS SQS not fully configured (missing Queue URL or using placeholder). Running in development mode for SQS."
                )
            else:
                print("AWS SQS client initialized and configured.")

        except Exception as e:
            # This catch block handles issues if boto3 can't even initialize,
            # for example, due to invalid region or underlying AWS configuration.
            print(
                f"AWS SQS client initialization failed: {e}. SQS functionality will be simulated."
            )
            self.is_configured = False  # Explicitly set to False if client init fails

    async def send_job_to_queue(self, job_id: str, job_data: Dict[str, Any]) -> bool:
        """Send a job to SQS queue"""
        if not self.is_configured:
            print(f"SQS not configured - simulating queue for job {job_id}")
            print(f"Simulated Job data for SQS: {job_data}")
            return True  # Simulate success for development

        # If configured, proceed with actual SQS send
        try:
            message_body = {
                "job_id": job_id,
                "job_data": job_data,
                "action": "start_training",  # Or whatever action is appropriate for Modal trigger
            }

            response = self.sqs.send_message(
                QueueUrl=self.queue_url,
                MessageBody=json.dumps(message_body),
                MessageAttributes={
                    "job_id": {"StringValue": job_id, "DataType": "String"}
                },
            )

            print(f"Message sent to SQS. MessageId: {response['MessageId']}")
            return True

        except ClientError as e:
            print(f"Error sending message to SQS: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error when sending to SQS: {e}")
            return False


# Global instance
sqs_service = SQSService()
