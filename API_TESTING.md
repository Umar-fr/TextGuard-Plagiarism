# TextGuard API Testing Guide

This file contains examples for testing all TextGuard endpoints using curl, Python, and JavaScript.

## Prerequisites

Make sure the server is running:
```bash
python plagiarism_server.py
# or
uvicorn plagiarism_server:app --host 0.0.0.0 --port 8000
```

## 🧪 Testing Endpoints

### 1. Health Check

**CURL:**
```bash
curl http://localhost:8000/health
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/health')
print(response.json())
```

**JavaScript/Fetch:**
```javascript
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(data => console.log(data));
```

---

### 2. Check Text for Plagiarism

**CURL:**
```bash
curl -X POST "http://localhost:8000/api/check-text" \
  -F "text=Your text here to check for plagiarism" \
  -F "user_id=user123" \
  -F "max_phrases=10" \
  -F "max_urls=30" \
  -F "use_semantic=true"
```

**Python:**
```python
import requests

data = {
    'text': 'Your text here to check for plagiarism',
    'user_id': 'user123',
    'max_phrases': 10,
    'max_urls': 30,
    'use_semantic': True
}

response = requests.post('http://localhost:8000/api/check-text', data=data)
result = response.json()

print(f"Plagiarism Score: {result['plagiarism_percentage']}%")
print(f"Is Plagiarized: {result['is_plagiarized']}")
print(f"Matches Found: {len(result['matches'])}")

for match in result['matches']:
    print(f"  - {match['url']}: {match['plagiarism_percent']}%")
```

**JavaScript/Fetch:**
```javascript
const formData = new FormData();
formData.append('text', 'Your text here to check for plagiarism');
formData.append('user_id', 'user123');
formData.append('max_phrases', 10);
formData.append('max_urls', 30);
formData.append('use_semantic', true);

fetch('http://localhost:8000/api/check-text', {
  method: 'POST',
  body: formData
})
.then(r => r.json())
.then(data => {
  console.log(`Plagiarism Score: ${data.plagiarism_percentage}%`);
  console.log(`Is Plagiarized: ${data.is_plagiarized}`);
  console.log(`Matches: ${data.matches.length}`);
  data.matches.forEach(m => {
    console.log(`  - ${m.url}: ${m.plagiarism_percent}%`);
  });
});
```

---

### 3. Check File for Plagiarism

**CURL:**
```bash
# Check PDF
curl -X POST "http://localhost:8000/api/check-file" \
  -F "file=@document.pdf" \
  -F "user_id=user123" \
  -F "max_phrases=10" \
  -F "max_urls=30"

# Check DOCX
curl -X POST "http://localhost:8000/api/check-file" \
  -F "file=@document.docx" \
  -F "user_id=user123"

# Check TXT
curl -X POST "http://localhost:8000/api/check-file" \
  -F "file=@document.txt" \
  -F "user_id=user123"

# Check CSV
curl -X POST "http://localhost:8000/api/check-file" \
  -F "file=@data.csv" \
  -F "user_id=user123"
```

**Python:**
```python
import requests

# Check a PDF file
with open('document.pdf', 'rb') as f:
    files = {
        'file': ('document.pdf', f, 'application/pdf'),
    }
    data = {
        'user_id': 'user123',
        'max_phrases': 10,
        'max_urls': 30
    }
    response = requests.post('http://localhost:8000/api/check-file', 
                            files=files, data=data)
    result = response.json()
    
    print(f"Plagiarism Score: {result['plagiarism_percentage']}%")
    print(f"Sources Examined: {result['sources_examined']}")
```

**JavaScript/Fetch:**
```javascript
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];

const formData = new FormData();
formData.append('file', file);
formData.append('user_id', 'user123');
formData.append('max_phrases', 10);
formData.append('max_urls', 30);

fetch('http://localhost:8000/api/check-file', {
  method: 'POST',
  body: formData
})
.then(r => r.json())
.then(data => {
  console.log(`File: ${data.filename}`);
  console.log(`Plagiarism Score: ${data.plagiarism_percentage}%`);
  console.log(`Is Plagiarized: ${data.is_plagiarized}`);
});
```

---

### 4. Remove Plagiarism (Paraphrase)

**CURL:**
```bash
# Light paraphrasing
curl -X POST "http://localhost:8000/api/remove-plagiarism" \
  -F "text=Your text here that needs paraphrasing" \
  -F "intensity=0.3"

# Medium paraphrasing
curl -X POST "http://localhost:8000/api/remove-plagiarism" \
  -F "text=Your text here that needs paraphrasing" \
  -F "intensity=0.7"

# Heavy paraphrasing
curl -X POST "http://localhost:8000/api/remove-plagiarism" \
  -F "text=Your text here that needs paraphrasing" \
  -F "intensity=1.0"
```

**Python:**
```python
import requests

text = "Your text here that needs paraphrasing"

data = {
    'text': text,
    'intensity': 0.7  # 0.1 = light, 1.0 = heavy
}

response = requests.post('http://localhost:8000/api/remove-plagiarism', data=data)
result = response.json()

if result['ok']:
    print("Original:")
    print(result['original_text'])
    print("\nParaphrased:")
    print(result['paraphrased_text'])
    print(f"\nToken Overlap: {result['changes_applied']['token_overlap']}%")
else:
    print(f"Error: {result['error']}")
```

**JavaScript/Fetch:**
```javascript
const formData = new FormData();
formData.append('text', 'Your text here that needs paraphrasing');
formData.append('intensity', 0.7);

fetch('http://localhost:8000/api/remove-plagiarism', {
  method: 'POST',
  body: formData
})
.then(r => r.json())
.then(data => {
  if (data.ok) {
    console.log('Original:', data.original_text);
    console.log('Paraphrased:', data.paraphrased_text);
    console.log('Token Overlap:', data.changes_applied.token_overlap + '%');
  } else {
    console.error('Error:', data.error);
  }
});
```

---

### 5. Get Statistics

**CURL:**
```bash
curl http://localhost:8000/api/stats
```

**Python:**
```python
import requests

response = requests.get('http://localhost:8000/api/stats')
stats = response.json()

print(f"Cached Pages: {stats['cached_pages']}")
print(f"Total Submissions: {stats['total_submissions']}")
print(f"Cache Size: {stats['cache_size_mb']} MB")
print(f"Semantic Model Loaded: {stats['semantic_model_loaded']}")
print(f"LSH Enabled: {stats['lsh_enabled']}")
```

**JavaScript/Fetch:**
```javascript
fetch('http://localhost:8000/api/stats')
  .then(r => r.json())
  .then(stats => {
    console.log(`Cached Pages: ${stats.cached_pages}`);
    console.log(`Total Submissions: ${stats.total_submissions}`);
    console.log(`Cache Size: ${stats.cache_size_mb} MB`);
    console.log(`Models Loaded: ${stats.semantic_model_loaded}`);
  });
```

---

## 🧪 Full Test Suite (Python)

```python
import requests
import json
import time

BASE_URL = 'http://localhost:8000'

def test_health():
    print("Testing health endpoint...")
    response = requests.get(f'{BASE_URL}/health')
    assert response.status_code == 200
    print("✅ Health check passed")

def test_check_text():
    print("\nTesting text plagiarism check...")
    data = {
        'text': 'Machine learning is a subset of artificial intelligence',
        'user_id': 'test_user',
        'max_phrases': 5,
        'max_urls': 10
    }
    response = requests.post(f'{BASE_URL}/api/check-text', data=data)
    assert response.status_code == 200
    result = response.json()
    assert result['ok'] == True
    assert 'plagiarism_percentage' in result
    print(f"✅ Text check passed - Score: {result['plagiarism_percentage']}%")

def test_stats():
    print("\nTesting statistics endpoint...")
    response = requests.get(f'{BASE_URL}/api/stats')
    assert response.status_code == 200
    stats = response.json()
    assert stats['ok'] == True
    print(f"✅ Stats check passed - Cached Pages: {stats['cached_pages']}")

def test_remove_plagiarism():
    print("\nTesting plagiarism removal...")
    data = {
        'text': 'Artificial intelligence is transforming the world',
        'intensity': 0.7
    }
    response = requests.post(f'{BASE_URL}/api/remove-plagiarism', data=data)
    assert response.status_code == 200
    result = response.json()
    assert result['ok'] == True
    print(f"✅ Paraphrasing passed - Token overlap: {result['changes_applied']['token_overlap']}%")

def run_all_tests():
    print("="*50)
    print("TextGuard API Test Suite")
    print("="*50)
    
    try:
        test_health()
        test_check_text()
        test_stats()
        test_remove_plagiarism()
        
        print("\n" + "="*50)
        print("✅ All tests passed!")
        print("="*50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_all_tests()
```

---

## 📊 Response Status Codes

| Code | Meaning |
|------|---------|
| 200  | Success |
| 400  | Bad Request (missing/invalid parameters) |
| 413  | Payload Too Large (text > 1MB) |
| 500  | Internal Server Error |

---

## 💡 Tips

- **Timeout**: Web searches can take 30-60 seconds on first run
- **Caching**: Results are cached - subsequent checks are faster
- **Batch Processing**: Send multiple requests but not simultaneously
- **Large Files**: PDFs > 5MB may take longer to process
- **Semantic Analysis**: Disable if slow: `use_semantic=false`

---

**Happy Testing! 🚀**
