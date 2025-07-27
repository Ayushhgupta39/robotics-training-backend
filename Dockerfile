# Use a slim Python base image for smaller size
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy only requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir to avoid storing cache in the image
# Using --upgrade to ensure all packages are updated to the specified versions
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port your FastAPI application runs on
EXPOSE 8000

# Command to run your FastAPI application with Uvicorn
# We use 0.0.0.0 to make it accessible from outside the container
# --host 0.0.0.0 and --port 8000 match your main.py if __name__ == "__main__" block
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]