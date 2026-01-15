# Dockerfile
# This file defines how to build the Docker image for our Flask application

# Specify the base image - Python 3.9 on slim variant of Debian
# slim variant is smaller in size compared to full Python image
FROM python:3.9-slim

# Set the working directory inside the container
# All subsequent commands will be executed from this directory
WORKDIR /app

# Install system dependencies required for MySQL connector
# gcc: C compiler needed to build some Python packages
# default-libmysqlclient-dev: MySQL client library headers
# pkg-config: Helper tool for compiling applications
# && rm -rf /var/lib/apt/lists/*: Cleans up apt cache to reduce image size
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt file from host to container
# This is done separately before copying other files
# Docker caches layers, so if requirements don't change, this layer is reused
COPY requirements.txt .

# Install Python dependencies listed in requirements.txt
# --no-cache-dir: Don't cache pip packages (reduces image size)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files from host to container working directory
# This includes app.py, templates folder, and any other files
COPY . .

# Expose port 5000 to allow external access to Flask application
# This is the port Flask development server runs on by default
EXPOSE 5000

# Set environment variable to tell Flask to run in production-like mode
# 0.0.0.0 makes Flask accessible from outside the container
ENV FLASK_RUN_HOST=0.0.0.0

# Define the command to run when container starts
# python app.py will start the Flask application
CMD ["python", "app.py"]