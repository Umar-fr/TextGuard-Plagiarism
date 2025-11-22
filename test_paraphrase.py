#!/usr/bin/env python3
"""Test the improved paraphrasing system"""

import requests
import json

# Test text from user
test_text = """A class is a user-defined data type. It consists of data members and member functions, which can be accessed and used by creating an instance of that class. It represents the set of properties or methods that are common to all objects of one type. A class is like a blueprint for an object.  

For Example: Consider the Class of Cars. There may be many cars with different names and brands but all of them will share some common properties like all of them will have 4 wheels, Speed Limit, Mileage range, etc. So here, Car is the class, and wheels, speed limits, mileage are their properties.

2. Object: 

It is a basic unit of Object-Oriented Programming and represents the real-life entities. An Object is an instance of a Class. When a class is defined, no memory is allocated but when it is instantiated (i.e. an object is created) memory is allocated. An object has an identity, state, and behavior. Each object contains data and code to manipulate the data. Objects can interact without having to know details of each other's data or code, it is sufficient to know the type of message accepted and type of response returned by the objects. 

For example "Dog" is a real-life Object, which has some characteristics like color, Breed, Bark, Sleep, and Eats."""

print("=" * 80)
print("IMPROVED PARAPHRASING TEST")
print("=" * 80)
print()

for intensity in [0.3, 0.5, 0.7, 0.9]:
    print(f"\n{'=' * 80}")
    print(f"Testing with Intensity: {intensity}")
    print(f"{'=' * 80}")
    
    data = {
        'text': test_text,
        'intensity': intensity
    }
    
    try:
        response = requests.post('http://127.0.0.1:8000/api/remove-plagiarism', data=data)
        result = response.json()
        
        if result.get('ok'):
            changes = result.get('changes_applied', {})
            paraphrased = result.get('paraphrased_text', '')
            
            print(f"\n✅ Status: Success")
            print(f"📊 Sentences Processed: {changes.get('sentences_processed', 'N/A')}")
            print(f"🔄 Text Variation: {changes.get('token_overlap', 'N/A')}%")
            print(f"🎯 Method: {changes.get('method', 'N/A')}")
            
            print(f"\n{'─' * 80}")
            print("ORIGINAL TEXT (First 300 chars):")
            print(f"{'─' * 80}")
            print(test_text[:300] + "...")
            
            print(f"\n{'─' * 80}")
            print(f"PARAPHRASED TEXT (First 300 chars):")
            print(f"{'─' * 80}")
            print(paraphrased[:300] + "...")
            
            print(f"\n{'─' * 80}")
            print("FULL PARAPHRASED OUTPUT:")
            print(f"{'─' * 80}")
            print(paraphrased)
            
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Request failed: {e}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
