import time
import requests
import json
import sys
import os
from openai import OpenAI

# Define your model endpoint URL
API_URL = "http://0.0.0.0:8000/v1/chat/completions"
HEALTH_URL = "http://0.0.0.0:8000/v1/models"

# NVIDIA hosted API configuration
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

def wait_for_server(timeout=600):
    """Wait for the server to be ready"""
    print("Waiting for NIM server to be ready...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(HEALTH_URL, timeout=5)
            if response.status_code == 200:
                print("✓ Server is ready!")
                print(f"  Took {int(time.time() - start_time)} seconds to start\n")
                return True
        except (requests.ConnectionError, requests.Timeout):
            pass
        
        time.sleep(5)
        elapsed = int(time.time() - start_time)
        print(f"  Still waiting... ({elapsed}s elapsed)")
    
    print(f"✗ Server did not become ready within {timeout}s timeout")
    return False

# Function to send a request to the LOCAL API and return the response time
def send_request(model, messages, max_tokens=15):
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "top_p": 1,
        "frequency_penalty": 1.0
    }

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json"
    }

    start_time = time.time()
    response = requests.post(API_URL, headers=headers, data=json.dumps(data))
    end_time = time.time()

    output = response.json()
    print(f"Output: {output['choices'][0]['message']['content']}")
    print(f"Generation time: {end_time - start_time:.4f} seconds")
    return end_time - start_time

# Function to send a request to NVIDIA hosted API
def send_request_nvidia(model, messages, max_tokens=15):
    if not NVIDIA_API_KEY:
        print("Error: NVIDIA_API_KEY environment variable not set")
        sys.exit(1)
    
    client = OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY
    )
    
    start_time = time.time()
    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=1.00,
        top_p=0.01,
        max_tokens=max_tokens,
        stream=False  # Non-streaming for timing comparison
    )
    end_time = time.time()
    
    output = completion.choices[0].message.content
    print(f"Output: {output}")
    print(f"Generation time: {end_time - start_time:.4f} seconds")
    return end_time - start_time

# Test function demonstrating caching with a long prompt
def test_prefix_caching(use_nvidia_hosted=False):
    model = "nvidia/llama-3.1-nemotron-nano-vl-8b-v1"
    
    if use_nvidia_hosted:
        print("=" * 60)
        print("Testing NVIDIA Hosted API (https://integrate.api.nvidia.com)")
        print("=" * 60)
        request_func = send_request_nvidia
    else:
        print("=" * 60)
        print("Testing Local NIM Server (http://0.0.0.0:8000)")
        print("=" * 60)
        request_func = send_request

    # Long document to simulate complex input
    LONG_PROMPT = """# Table of People\n""" + \
    "| ID  | Name          | Age | Occupation    | Country       |\n" + \
    "|-----|---------------|-----|---------------|---------------|\n" + \
    "| 1   | John Doe      | 29  | Engineer      | USA           |\n" + \
    "| 2   | Jane Smith    | 34  | Doctor        | Canada        |\n" * 50  # Replicating rows to make the table long

    # First query (no caching)
    messages_1 = [{"role": "user", "content": LONG_PROMPT + "Question: What is the age of John Doe?"}]
    print("\nFirst query (no caching):")
    time_1 = request_func(model, messages_1)

    # Second query (prefix caching enabled)
    messages_2 = [{"role": "user", "content": LONG_PROMPT + "Question: What is the occupation of Jane Smith?"}]
    print("\nSecond query (with prefix caching):")
    time_2 = request_func(model, messages_2)
    
    # Summary
    improvement = ((time_1 - time_2) / time_1) * 100 if time_1 > 0 else 0
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  First query:  {time_1:.4f}s")
    print(f"  Second query: {time_2:.4f}s")
    print(f"  Speedup:      {improvement:.2f}%")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Test KV cache reuse with local or NVIDIA hosted models')
    parser.add_argument('--mode', choices=['local', 'nvidia', 'both'], default='local',
                        help='Test mode: local (NIM server), nvidia (hosted API), or both')
    args = parser.parse_args()
    
    if args.mode in ['local', 'both']:
        # Wait for server to be ready before testing
        if not wait_for_server():
            print("\nError: NIM server is not responding. Make sure it's running:")
            print("  bash local_llm_nim.sh")
            if args.mode == 'local':
                sys.exit(1)
            else:
                print("\nSkipping local test, will test NVIDIA hosted only...\n")
        else:
            test_prefix_caching(use_nvidia_hosted=False)
    
    if args.mode in ['nvidia', 'both']:
        if args.mode == 'both':
            print("\n" + "="*60 + "\n")
        test_prefix_caching(use_nvidia_hosted=True)