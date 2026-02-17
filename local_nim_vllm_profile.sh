#!/bin/bash
set -e  # Exit on error

# Check if API key is set (try both NGC_API_KEY and NVIDIA_API_KEY)
if [ -z "$NGC_API_KEY" ] && [ -z "$NVIDIA_API_KEY" ]; then
    echo "❌ Error: API key not set!"
    echo "   Please set either NGC_API_KEY or NVIDIA_API_KEY environment variable"
    echo "   Example: export NGC_API_KEY='your-key-here'"
    exit 1
fi

# Use NGC_API_KEY if set, otherwise fall back to NVIDIA_API_KEY
API_KEY="${NGC_API_KEY:-$NVIDIA_API_KEY}"

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if NVIDIA container runtime is available
if ! docker info 2>&1 | grep -q nvidia && ! command -v nvidia-container-runtime &> /dev/null; then
    echo "⚠️  Warning: NVIDIA container runtime may not be configured"
    echo "   The --gpus flag may not work. Continuing anyway..."
fi

# Ensure cache directory exists and is accessible
CACHE_DIR="$(pwd)/.cachem/nim-cache"
mkdir -p "$CACHE_DIR/local_cache"

# Fix permissions - make sure the cache directory is writable by anyone
echo "🔧 Setting up cache directory permissions..."
# Set permissions to be writable by all (777) so container can write regardless of user
chmod -R 777 "$CACHE_DIR" 2>/dev/null || true
# Also ensure parent directory is accessible
chmod 777 "$(pwd)/.cachem" 2>/dev/null || true
# Use a container to ensure proper ownership (UID 1000 is typical for containers)
docker run --rm -v "$(pwd)/.cachem:/cache" alpine sh -c "chown -R 1000:1000 /cache/nim-cache && chmod -R 777 /cache/nim-cache" 2>/dev/null || true

echo "🚀 Starting NIM container..."
echo "   Cache directory: $CACHE_DIR"
echo "   Port: 8000"

# Check if running in interactive terminal and build docker command accordingly
DOCKER_ARGS=()
if [ -t 0 ] && [ -t 1 ]; then
    DOCKER_ARGS+=(-it)
else
    echo "⚠️  Running in non-interactive mode (no -it flag)"
fi

# Run the container with proper error handling
docker run "${DOCKER_ARGS[@]}" --rm \
  --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 8000:8000 \
  -v "$CACHE_DIR:/opt/nim/.cache" \
  -e NGC_API_KEY="$API_KEY" \
  -e NIM_ENABLE_KV_CACHE_REUSE=1 \
  -e NIM_MODEL_PROFILE=4c0d8954feb1eaaa7c2df1771a37a2d9304060953d086cb01b80afd9f1e75ecc \
  nvcr.io/nim/meta/llama-3.1-8b-instruct:latest