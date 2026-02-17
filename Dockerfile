# Base Python image - Using 3.10 for best compatibility with dependencies
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for image processing and builds
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for better layer caching
COPY requirements_gradio.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_gradio.txt

# Copy application code
COPY . .

# Expose Gradio default port
EXPOSE 7860

# Create directories for generated files (optional, can be done via volumes)
RUN mkdir -p /app/generated_images /app/plans

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/ || exit 1

# Run the Gradio application
CMD ["python", "gradio_agent_chatbot.py"]
