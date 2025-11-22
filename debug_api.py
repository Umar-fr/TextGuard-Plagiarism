#!/usr/bin/env python3
"""Debug script to test API directly"""
import sys
import time
import requests
import subprocess
import os
import signal

# Start server in background
print("Starting server...")
server_process = subprocess.Popen(
    [sys.executable, "plagiarism_server.py"],
    cwd=r"c:\Users\imdop\Documents\textguard-plagiarism",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(8)

# Test the API
print("\nTesting API endpoint...")
try:
    data = {
        'text': 'This is a test of plagiarism detection. ' * 10,
        'user_id': 'test',
        'max_phrases': '5',
        'max_urls': '10',
        'use_semantic': 'false'
    }
    
    print("Sending POST request...")
    response = requests.post(
        'http://127.0.0.1:8000/api/check-text',
        data=data,
        timeout=30
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.json()}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    # Kill server
    print("\nKilling server...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except:
        server_process.kill()
