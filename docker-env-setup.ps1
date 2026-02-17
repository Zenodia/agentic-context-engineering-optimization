# Docker Environment Setup Script (PowerShell)
# Sets both required API keys for the Agent Skills Chatbot

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Agent Skills Chatbot - Docker Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will help you set the required environment variables."
Write-Host ""
Write-Host "Get your NVIDIA API key at: https://build.nvidia.com/"
Write-Host ""

# Check if keys are already set
if ($env:NVIDIA_API_KEY) {
    Write-Host "✅ NVIDIA_API_KEY is already set" -ForegroundColor Green
} else {
    Write-Host "❌ NVIDIA_API_KEY is not set" -ForegroundColor Red
    $nvidia_key = Read-Host "Enter your NVIDIA API key"
    $env:NVIDIA_API_KEY = $nvidia_key
    Write-Host "✅ NVIDIA_API_KEY exported" -ForegroundColor Green
}

if ($env:INFERENCE_API_KEY) {
    Write-Host "✅ INFERENCE_API_KEY is already set" -ForegroundColor Green
} else {
    Write-Host "❌ INFERENCE_API_KEY is not set" -ForegroundColor Red
    Write-Host ""
    Write-Host "⚠️  IMPORTANT: INFERENCE_API_KEY is DIFFERENT from NVIDIA_API_KEY" -ForegroundColor Yellow
    Write-Host "    Get it from: https://inference.nvidia.com/ (requires SSO login)" -ForegroundColor Yellow
    Write-Host ""
    $inference_key = Read-Host "Enter your INFERENCE API key"
    $env:INFERENCE_API_KEY = $inference_key
    Write-Host "✅ INFERENCE_API_KEY exported" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Environment variables set successfully!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "NVIDIA_API_KEY: $($env:NVIDIA_API_KEY.Substring(0, [Math]::Min(10, $env:NVIDIA_API_KEY.Length)))..."
Write-Host "INFERENCE_API_KEY: $($env:INFERENCE_API_KEY.Substring(0, [Math]::Min(10, $env:INFERENCE_API_KEY.Length)))..."
Write-Host ""
Write-Host "Now you can run:" -ForegroundColor Yellow
Write-Host "  docker-compose up --build" -ForegroundColor Yellow
Write-Host ""
Write-Host "Note: These environment variables are set for the current PowerShell session only."
Write-Host "To persist them, add to your PowerShell profile or set as system environment variables."
Write-Host ""

