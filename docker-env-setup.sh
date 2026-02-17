#!/bin/bash
# Docker Environment Setup Script
# Sets both required API keys for the Agent Skills Chatbot

echo "=================================="
echo "Agent Skills Chatbot - Docker Setup"
echo "=================================="
echo ""
echo "This script will help you set the required environment variables."
echo ""
echo "Get your NVIDIA API key at: https://build.nvidia.com/"
echo ""

# Check if keys are already set
if [ -n "$NVIDIA_API_KEY" ]; then
    echo "✅ NVIDIA_API_KEY is already set"
else
    echo "❌ NVIDIA_API_KEY is not set"
    read -p "Enter your NVIDIA API key: " nvidia_key
    export NVIDIA_API_KEY="$nvidia_key"
    echo "✅ NVIDIA_API_KEY exported"
fi

if [ -n "$INFERENCE_API_KEY" ]; then
    echo "✅ INFERENCE_API_KEY is already set"
else
    echo "❌ INFERENCE_API_KEY is not set"
    echo ""
    echo "⚠️  IMPORTANT: INFERENCE_API_KEY is DIFFERENT from NVIDIA_API_KEY"
    echo "    Get it from: https://inference.nvidia.com/ (requires SSO login)"
    echo ""
    read -p "Enter your INFERENCE API key: " inference_key
    export INFERENCE_API_KEY="$inference_key"
    echo "✅ INFERENCE_API_KEY exported"
fi

echo ""
echo "=================================="
echo "Environment variables set successfully!"
echo "=================================="
echo ""
echo "NVIDIA_API_KEY: ${NVIDIA_API_KEY:0:10}..."
echo "INFERENCE_API_KEY: ${INFERENCE_API_KEY:0:10}..."
echo ""
echo "Now you can run:"
echo "  docker-compose up --build"
echo ""
echo "Or run this script with 'source' to persist in your shell:"
echo "  source docker-env-setup.sh"
echo ""

