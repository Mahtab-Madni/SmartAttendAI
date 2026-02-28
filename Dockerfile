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
RUN mkdir -p config/data/faces config/data/logs data/faces data/logs

# Verify models exist
RUN test -f models/emotion_model.h5 || echo "Warning: emotion_model.h5 not found" && \
    test -f models/spoof_detection_model.h5 || echo "Warning: spoof_detection_model.h5 not found" && \
    test -f models/shape_predictor_68_face_landmarks.dat || echo "Warning: shape_predictor_68_face_landmarks.dat not found"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application using Python startup wrapper
CMD ["python", "run.py"]
