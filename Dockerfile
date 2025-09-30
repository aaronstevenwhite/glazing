# Use official Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY pyproject.toml README.md ./
COPY src/glazing/__version__.py src/glazing/

# Install package dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Copy the rest of the application code
COPY src/ src/
COPY tests/ tests/

# Create data directory for datasets
RUN mkdir -p /data

# Set environment variable for data directory
ENV GLAZING_DATA_DIR=/data

# Initialize datasets during build
RUN glazing init --data-dir /data

# Expose data directory as volume
VOLUME ["/data"]

# Set the entrypoint to the glazing CLI
ENTRYPOINT ["glazing"]

# Default command shows help
CMD ["--help"]
