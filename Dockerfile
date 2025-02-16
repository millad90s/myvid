# Use official Python base image
FROM python:3.11-slim

# Set environment variables to prevent prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install  dependencies
RUN apt update && apt install -y \
    git ffmpeg \
    curl vim wget curl \
    && rm -rf /var/lib/apt/lists/*

COPY files/fonts/* /usr/share/fonts/truetype/
# Set the working directory
WORKDIR /app

# Copy requirements file if you have one (optional)
COPY requirements.txt .

# Install required Python packages
RUN pip install -r requirements.txt

# Copy all project files into the container
COPY . .

# Set the default command to run your script
CMD ["python", "mytelegram.py"]
