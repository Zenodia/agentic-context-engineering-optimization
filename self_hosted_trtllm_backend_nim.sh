

export NIM_PER_REQ_METRICS_ENABLE=1
export LOCAL_NIM_CACHE=.cache/nim

mkdir -p "$LOCAL_NIM_CACHE"
docker run -it --rm \
    --gpus all \
    --shm-size=16GB \
    -e NGC_API_KEY \
    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
    -e NIM_PER_REQ_METRICS_ENABLE=1 \
    -u $(id -u) \
    -p 8000:8000 \
    nvcr.io/nim/nvidia/llama-3.1-nemotron-nano-8b-v1:latest

