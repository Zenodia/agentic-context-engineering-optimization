
export LOCAL_NIM_CACHE=/mnt/ZenoHD/.cache/nim
#mkdir -p "$LOCAL_NIM_CACHE"
#docker run -it --rm \
#    --gpus all \
#    --shm-size=16GB \
#    -e NGC_API_KEY \
#    -v "$LOCAL_NIM_CACHE:/opt/nim/.cache" \
#    -u $(id -u) \
#    -p 8000:8000 \
#    nvcr.io/nim/nvidia/llama-3.1-nemotron-nano-vl-8b-v1:latest \
#    list-model-profiles


