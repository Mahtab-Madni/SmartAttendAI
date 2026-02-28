# Use official Python runtime as base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV OPENCV_VIDEOIO_DEBUG=0
ENV QT_QPA_PLATFORM=offscreen
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for OpenCV, dlib, and face-recognition
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    pkg-config \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libxrender1 \
    libgomp1 \
    libglib2.0-0 \
    libopenblas-dev \
    liblapack-dev \
    gfortran \
    libglvnd0 \
    libglvnd-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p config/data/faces config/data/logs data/faces data/logs models

# Note: ML models (emotion_model.h5, spoof_detection_model.h5, shape_predictor_68_face_landmarks.dat)
# are not included in the Docker image as they are too large for git (>100MB per file).
# The system gracefully handles missing models using fallback detection methods.
# See MODELS.md for instructions on downloading optional models locally.

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application using Python startup wrapper
CMD ["python", "run.py"]
