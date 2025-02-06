# Use official Python base image
FROM python:3.9-slim

# Set environment variables to prevent prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install FFmpeg and dependencies
RUN apt update && apt install -y \
    ffmpeg \
    git \
    curl vim wget curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements file if you have one (optional)
# COPY requirements.txt .

# Install required Python packages
RUN pip install --no-cache-dir \
    faster-whisper ffmpeg-python

# Copy all project files into the container
COPY . .

# Set the default command to run your script
CMD ["python", "main.py"]
