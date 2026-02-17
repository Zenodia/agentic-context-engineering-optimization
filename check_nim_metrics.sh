#!/bin/bash
# Script to check NIM container status and access metrics

NIM_PORT=8000
HOST="localhost"

echo "🔍 Checking NIM container status..."
echo ""

# Check if container is running
CONTAINER=$(docker ps --filter "publish=$NIM_PORT" --format "{{.Names}}" | head -1)

# If no running container, check for stopped containers
if [ -z "$CONTAINER" ]; then
    STOPPED_CONTAINER=$(docker ps -a --filter "name=nim" --filter "name=llama" --format "{{.Names}}\t{{.Status}}" | head -1)
    if [ -n "$STOPPED_CONTAINER" ]; then
        echo "⚠️  Found stopped NIM container:"
        echo "   $STOPPED_CONTAINER"
        echo ""
        echo "📋 Recent logs (last 10 lines):"
        CONTAINER_NAME=$(echo "$STOPPED_CONTAINER" | cut -f1)
        docker logs "$CONTAINER_NAME" 2>&1 | tail -10 | sed 's/^/   /'
        echo ""
        echo "💡 To restart the container, run:"
        echo "   ./local_nim_vllm_profile.sh"
        echo ""
        echo "   Or to see full logs:"
        echo "   docker logs $CONTAINER_NAME"
        exit 1
    else
        echo "❌ No NIM container found running on port $NIM_PORT"
        echo ""
        echo "💡 To start the container, run:"
        echo "   ./local_nim_vllm_profile.sh"
        echo ""
        exit 1
    fi
fi

echo "✅ NIM container is running: $CONTAINER"
echo ""

# Check if port is accessible
if ! nc -z $HOST $NIM_PORT 2>/dev/null; then
    echo "⚠️  Port $NIM_PORT is not accessible"
    echo "   Container might still be starting up..."
    exit 1
fi

echo "📊 Available endpoints:"
echo ""

# Test /v1/models endpoint (health check)
echo "1. Health check (/v1/models):"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://$HOST:$NIM_PORT/v1/models 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Status: OK"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY" | head -5
else
    echo "   ❌ Status: $HTTP_CODE"
    echo "$BODY" | head -3
fi
echo ""

# Test /metrics endpoint (Prometheus format)
echo "2. Metrics endpoint (/metrics):"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://$HOST:$NIM_PORT/metrics 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Status: OK"
    echo "$BODY" | head -20
    echo "   ... (showing first 20 lines, use 'curl http://$HOST:$NIM_PORT/metrics' for full output)"
else
    echo "   ❌ Status: $HTTP_CODE"
    echo "$BODY" | head -3
fi
echo ""

# Test /v1/metrics (if it exists)
echo "3. Alternative metrics endpoint (/v1/metrics):"
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://$HOST:$NIM_PORT/v1/metrics 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')
if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Status: OK"
    echo "$BODY" | head -20
else
    echo "   ❌ Status: $HTTP_CODE (endpoint may not exist)"
    if [ -n "$BODY" ]; then
        echo "$BODY" | head -3
    fi
fi
echo ""

echo "💡 Tip: The correct metrics endpoint is usually:"
echo "   curl http://$HOST:$NIM_PORT/metrics"
echo ""
echo "   For JSON format (if supported):"
echo "   curl http://$HOST:$NIM_PORT/v1/models"

