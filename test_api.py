#!/usr/bin/env python3
import requests
import json
import sys

data = {
    'text': 'This is a test of plagiarism detection. ' * 10,
    'user_id': 'test',
    'max_phrases': '5',
    'max_urls': '10',
    'use_semantic': 'false'
}

print('Sending request to http://127.0.0.1:8000/api/check-text...')
print(f'Payload: {data}')

try:
    response = requests.post('http://127.0.0.1:8000/api/check-text', data=data, timeout=120)
    print(f'\nStatus: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type")}')
    print(f'Response length: {len(response.text)}')
    
    result = response.json()
    print(f'\nResponse keys: {list(result.keys())}')
    print(f'OK: {result.get("ok")}')
    
    if not result.get('ok'):
        print(f'Error: {result.get("error")}')
    else:
        print(f'Plagiarism Score: {result.get("plagiarism_score")}')
        print(f'Matches: {len(result.get("matches", []))}')
        print(f'Response preview: {json.dumps(result, indent=2)[:1000]}')
        
except Exception as e:
    print(f'\nERROR: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
