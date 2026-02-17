#!/usr/bin/env python3
"""
Quick test to check NVIDIA API response format
This helps debug the "No image data in response" error
"""

import os
import requests
import json

def test_api_response():
    api_key = os.getenv("NVIDIA_API_KEY")
    
    if not api_key:
        print("❌ NVIDIA_API_KEY not set")
        print("Set it with: export NVIDIA_API_KEY='your-key'")
        return
    
    print("Testing NVIDIA Flux.1 Schnell API...")
    print("="*70)
    
    # Test with Schnell model (fast, 4 steps)
    invoke_url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    
    payload = {
        "prompt": "a simple coffee shop interior",
        "width": 1024,
        "height": 1024,
        "seed": 0,
        "steps": 4
    }
    
    print(f"\n📡 Request to: {invoke_url}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    print("\n⏳ Sending request...\n")
    
    try:
        response = requests.post(invoke_url, headers=headers, json=payload)
        response.raise_for_status()
        response_body = response.json()
        
        print("✅ Response received!")
        print("="*70)
        print("\n📋 Response structure:")
        print(f"   Top-level keys: {list(response_body.keys())}")
        print(f"\n📄 Full response:")
        print(json.dumps(response_body, indent=2)[:1000])  # First 1000 chars
        
        # Try to find image data
        print("\n🔍 Looking for image data...")
        
        if "image" in response_body:
            print("   ✅ Found 'image' field")
            print(f"   Type: {type(response_body['image'])}")
            if isinstance(response_body['image'], str):
                print(f"   Length: {len(response_body['image'])} chars")
        
        if "data" in response_body:
            print("   ✅ Found 'data' field")
            print(f"   Type: {type(response_body['data'])}")
            if isinstance(response_body['data'], list) and len(response_body['data']) > 0:
                print(f"   First item keys: {list(response_body['data'][0].keys())}")
        
        if "artifacts" in response_body:
            print("   ✅ Found 'artifacts' field")
            print(f"   Type: {type(response_body['artifacts'])}")
            if isinstance(response_body['artifacts'], list) and len(response_body['artifacts']) > 0:
                print(f"   First item keys: {list(response_body['artifacts'][0].keys())}")
        
        if "images" in response_body:
            print("   ✅ Found 'images' field")
            print(f"   Type: {type(response_body['images'])}")
        
        print("\n" + "="*70)
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Status code: {e.response.status_code}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_api_response()

