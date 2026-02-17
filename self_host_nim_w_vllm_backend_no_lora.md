
### find the profile 
### Step 1: Start container temporarily to read the manifest

```bash
docker run --rm -it --entrypoint bash \
  nvcr.io/nim/nvidia/llama-3.3-nemotron-super-49b-v1.5:latest \
  -c "cat /opt/nim/etc/default/model_manifest.yaml" > /tmp/nemotron49b-manifest.yaml
```

### Step 2: Find vLLM profiles

```bash
grep -B5 'vllm' /tmp/nimnemotron49b-manifest.yaml | grep -E '(id:|vllm|tp:|precision:|lora:)'

#!/bin/bash
# Find profiles with tp=8 in NIM manifest

grep -B10 'tp: 8' /tmp/nim-manifest.yaml | grep -E '(id:|vllm|tp:|precision:|lora:)' | head -20
```
#!/bin/bash
# Find profiles with tp=8 in NIM manifest

grep -B10 'tp: 8' /tmp/nim-manifest.yaml | grep -E '(id:|vllm|tp:|precision:|lora:)' | head -20



## get into DLCluster with ssh tunnel

#### fetch interactive node with 1 A100 GPU
srun --gres gpu:8--time=08:00:00 --pty /bin/bash -i

##### build ssh tunnel into this running node 
Note: this is a pretty big model, so the ckpt loading will take sometime, do NOT build ssh tunnel before you are sure the server endpoint is up and running 


1. ssh -L 8000:localhost:8000 zcharpy@dlcluster.nvidia.com
2. ssh -vvv -L 8000:luna-prod-1316-au:8000 luna-prod-1316-au -N
            
use squeue -u zcharpy to check the node name

then use 
## run the docker with mount permission issue alternative 
dlcluster-login-02:~> ssh -vvv -L 8000:Node_Name:8000 Node_Name - N 


```bash
docker run -d \
  --gpus all --ipc=host \
  --ulimit memlock=-1 --ulimit stack=67108864 \
  -p 8000:8000 \
  -e NGC_API_KEY=$NGC_API_KEY \
  -e NIM_ENABLE_KV_CACHE_REUSE=1 \
  -e NIM_MODEL_PROFILE=089d3c0d578020772271e4637f690b66a5054b68151361ba80df2aff9717aea8 \
  nvcr.io/nim/nvidia/llama-3.3-nemotron-super-49b-v1.5:latest
```
##
inside of the compute node on DLCluster 

==========================================
Correct curl command format:
==========================================

# Non-streaming:
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "nvidia/llama-3.3-nemotron-super-49b-v1.5", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10}'

# Streaming:
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "nvidia/llama-3.3-nemotron-super-49b-v1.5", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 10, "stream": true}'

# View full API docs:
echo "Open in browser: http://localhost:8000/docs"


## curl command on local PC with ssh tunnel 
curl -X POST http://127.0.0.1:8000/v1/chat/completions -H "accept: application/json" -H "Content-Type: application/json" -d "{\"model\": \"nvidia/llama-3.3-nemotron-super-49b-v1.5\", \"messages\": [{\"role\":\"user\", \"content\":\"Hello! How are you?\"}, {\"role\":\"assistant\", \"content\":\"Hi! I am quite well, how can I help you today?\"}, {\"role\":\"user\", \"content\":\"Can you write me a song?\"}], \"top_p\": 1, \"n\": 1, \"max_tokens\": 15, \"stream\": true, \"frequency_penalty\": 1.0, \"stop\": [\"hello\"]}"




### Metrics endpoint is `/v1/metrics`, not `/metrics`

```bash
# 404
curl localhost:8000/metrics

# Correct
curl localhost:8000/v1/metrics
```

### Cache directory permissions

NIM runs as non-root. Shared/NFS paths often fail with permission errors. Use a local path:

```bash
mkdir -p /tmp/nim-cache && chmod 777 /tmp/nim-cache
# Then mount: -v /tmp/nim-cache:/opt/nim/.cache
```

---

## How to Find vLLM Profile IDs

NIM bundles multiple engine profiles per model. By default it picks TRT-LLM. To use vLLM, you need the profile ID.

### Step 1: Start container temporarily to read the manifest

```bash
docker run --rm -it --entrypoint bash \
  nvcr.io/nim/meta/llama-3.1-8b-instruct:latest \
  -c "cat /opt/nim/etc/default/model_manifest.yaml" > /tmp/nim-manifest.yaml
```

### Step 2: Find vLLM profiles

```bash
grep -B5 'vllm' /tmp/nim-manifest.yaml | grep -E '(id:|vllm|tp:|precision:|lora:)'
```

### Step 3: Pick a profile

Choose based on your needs:

| Criteria | How to pick |
|----------|-------------|
| GPU count | Match `tp:` (tensor parallelism) to your GPU count |
| Precision | `fp8` for speed, `bf16` for quality, `nvfp4` for memory savings |
| LoRA | `lora: true` if you need LoRA adapter support |

For example, for **1 GPU, fp8 precision, no LoRA**:
```
NIM_MODEL_PROFILE=4c0d8954feb1eaaa7c2df1771a37a2d9304060953d086cb01b80afd9f1e75ecc
```

### Profiles for `llama-3.1-8b-instruct` (NIM v1.15.5)

| Profile ID | TP | Precision | LoRA |
|---|---|---|---|
| `058d...ddc` | 1 | fp8 | yes |
| `4c0d...ecc` | 1 | fp8 | no |
| `1d53...aaa` | 1 | bf16 | no |
| `fd5b...552` | 1 | bf16 | yes |
| `1dbd...211` | 1 | nvfp4 | yes |
| `f2cf...c60` | 1 | nvfp4 | no |
| `d67e...e84` | 2 | bf16 | no |
| `e4e8...0a9` | 2 | bf16 | yes |
| `6c4b...daf` | 4 | bf16 | no |
| `f849...ffc` | 4 | bf16 | yes |

> Profile IDs are model-specific. Other NIM images will have different IDs. Always check the manifest.

---

## Retrieving Metrics

### Query prefix cache metrics

```bash
# All metrics
curl -s localhost:8000/v1/metrics

# Prefix cache metrics only
curl -s localhost:8000/v1/metrics | grep prefix_cache

# Key metrics:
#   vllm:prefix_cache_queries_total  - total tokens checked against cache
#   vllm:prefix_cache_hits_total     - tokens served from cache
#   Hit rate = hits / queries
```

### Compute hit rate

```bash
curl -s localhost:8000/v1/metrics | awk '
  /^vllm:prefix_cache_queries_total/ { queries = $2 }
  /^vllm:prefix_cache_hits_total/    { hits = $2 }
  END { if (queries > 0) printf "Cache hit rate: %.1f%% (%d/%d)\n", hits/queries*100, hits, queries }
'
```

### Other useful metrics from vLLM backend

```bash
# GPU cache utilization
curl -s localhost:8000/v1/metrics | grep gpu_cache_usage_perc

# Request queue depth
curl -s localhost:8000/v1/metrics | grep num_requests

# Time to first token
curl -s localhost:8000/v1/metrics | grep time_to_first_token
```

---

## Test Results (H200 NVL, llama-3.1-8b-instruct, NIM v1.15.5, vLLM backend)

Test setup: ~2000-token system prompt, `max_tokens=1`, non-streaming. Same benchmark script, same node, containers restarted between tests.

### Cache OFF vs Cache ON

| Request | Cache OFF | Cache ON (cold start) | Cache ON (warm cache) |
|---------|-----------|----------------------|----------------------|
| Q1 (first with prefix) | 20.6 ms | 21.6 ms | 10.3 ms |
| Q2 (same prefix) | 20.9 ms | 12.3 ms | 10.3 ms |
| Q3 (same prefix) | 20.2 ms | 10.1 ms | 10.4 ms |
| Q4 (same prefix) | 20.1 ms | 10.2 ms | 10.0 ms |
| Q5 (same prefix) | 20.0 ms | 10.0 ms | 9.9 ms |
| **Avg Q2-Q5** | **20.3 ms** | **10.7 ms** | **10.1 ms** |
| **Speedup** | **1.0x** | **2.0x** | **2.0x** |

- **Cache OFF**: Every request takes ~20 ms, no benefit from repeated prefixes.
- **Cache ON (cold start)**: Q1 pays full cost (~21 ms), Q2+ are ~10 ms as the cached prefix is reused. **2x TTFT improvement**.
- **Cache ON (warm cache)**: If the prefix was cached from previous requests, even Q1 is fast (~10 ms).

### Cache metrics (only available with vLLM backend)

| Scenario | Queries | Hits | Hit Rate |
|----------|---------|------|----------|
| Cold start (first 5+2 warmup requests) | 3,652 | 2,832 | **77.5%** |
| Warm cache (next 5+2 requests) | 3,649 | 3,552 | **97.3%** |
| Cache OFF | 0 | 0 | N/A (no metrics exported) |

The first batch has a lower hit rate because Q1's prefix is a compulsory miss. The second batch hits ~97% because the prefix blocks were already cached from the first batch.

---

## All KV Cache Env Vars

| Env Var | Values | Default | Description |
|---------|--------|---------|-------------|
| `NIM_ENABLE_KV_CACHE_REUSE` | `1` / `0` | `0` | Enable prefix caching |
| `NIM_ENABLE_KV_CACHE_HOST_OFFLOAD` | `1` / `0` | unset | Offload cache to host memory (TRT-LLM only) |
| `NIM_KV_CACHE_HOST_MEM_FRACTION` | float | `0.1` | Host memory fraction for offload buffer |
| `NIM_MODEL_PROFILE` | string | auto | Force a specific engine profile |

## References

- [NIM KV Cache Reuse](https://docs.nvidia.com/nim/large-language-models/latest/kv-cache-reuse.html)
- [NIM Configuration](https://docs.nvidia.com/nim/large-language-models/latest/configuration.html)
- [NIM Observability](https://docs.nvidia.com/nim/large-language-models/latest/observability.html)
