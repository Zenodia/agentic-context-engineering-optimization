import requests
import re

def get_cache_hit_rate(queries: list[str] = None):
    """
    Fetch vLLM metrics and calculate cache hit rate.
    Equivalent to the curl + awk command.
    """
    url = "http://localhost:8000/v1/metrics"
    
    try:
        # Make GET request (equivalent to curl -s)
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse metrics to find queries and hits
        query_count = None
        hits = None
        
        for line in response.text.split('\n'):
            # Match vllm:prefix_cache_queries_total with optional Prometheus labels and extract the value
            # Format: vllm:prefix_cache_queries_total{labels} value or vllm:prefix_cache_queries_total value
            match_queries = re.match(r'^vllm:prefix_cache_queries_total(?:\{[^}]+\})?\s+([\d.]+)', line)
            if match_queries:
                query_count = float(match_queries.group(1))
            
            # Match vllm:prefix_cache_hits_total with optional Prometheus labels and extract the value
            match_hits = re.match(r'^vllm:prefix_cache_hits_total(?:\{[^}]+\})?\s+([\d.]+)', line)
            if match_hits:
                hits = float(match_hits.group(1))
        
        # Calculate and print cache hit rate
        if query_count is not None and hits is not None and query_count > 0:
            hit_rate = (hits / query_count) * 100
            print(f"Cache hit rate: {hit_rate:.1f}% ({hits:.0f}/{query_count:.0f})")
        else:
            print(f"No cache queries found or queries is 0 (queries: {query_count}, hits: {hits})")
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching metrics: {e}")
    except Exception as e:
        print(f"Error processing metrics: {e}")

if __name__ == "__main__":
    get_cache_hit_rate(["hello"])

