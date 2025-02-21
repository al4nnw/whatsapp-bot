ARG PYTHON_VERSION=3.12.0
FROM python:${PYTHON_VERSION}-slim as base
# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Add Python path environment variable
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Expose the FastAPI port
EXPOSE 8000
