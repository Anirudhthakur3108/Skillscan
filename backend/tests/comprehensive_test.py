#!/usr/bin/env python3
"""Comprehensive endpoint validation test."""
import requests
import json
import sys
import time
from collections import Counter

BASE_URL = "http://localhost:5001"

def test_health():
    """Test health endpoint."""
    print("?? Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        status = response.status_code
        data = response.json()
        print(f"   ? Status: {status}")
        print(f"   ? Response: {data}")
        return status == 200
    except Exception as e:
        print(f"   ? Error: {e}")
        return False

def test_register():
    """Register a test user and return token."""
    print("\n?? Testing register endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "email": f"testuser_{int(time.time() * 1000)}@test.com",
                "password": "Test123!",
                "full_name": "Test User"
            }
        )
        status = response.status_code
        data = response.json()
        print(f"   ? Status: {status}")
        if status == 201:
            token = data.get("access_token")
            user_id = data.get("student", {}).get("id")
            print(f"   ? User ID: {user_id}")
            print(f"   ? Token acquired: {token[:50]}...")
            return True, token, user_id
        else:
            print(f"   ? Response: {data}")
            return False, None, None
    except Exception as e:
        print(f"   ? Error: {e}")
        return False, None, None

def test_generate_assessment(token, user_id):
    """Test generate assessment endpoint."""
    print("\n?? Testing generate assessment endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "skill": "Python",
            "level": "intermediate",
            "num_questions": 10
        }
        response = requests.post(
            f"{BASE_URL}/assessments/generate",
            json=payload,
            headers=headers
        )
        status = response.status_code
        data = response.json()
        print(f"   Status: {status}")
        
        if status == 200:
            # Check num_questions
            num_questions = data.get("num_questions")
            print(f"   ? num_questions: {num_questions}")
            
            # Check MCQ questions
            questions = data.get("questions", [])
            print(f"   ? Questions count: {len(questions)}")
            
            if len(questions) > 0:
                print(f"\n   ?? Question Structure Check:")
                # Check first question structure
                q = questions[0]
                print(f"      - ID exists: {'id' in q}")
                print(f"      - Text exists: {'text' in q}")
                print(f"      - Options exist: {'options' in q}")
                
                # Check unique IDs
                ids = [q.get('id') for q in questions]
                unique_ids = len(set(ids))
                print(f"\n   ?? ID Uniqueness Check:")
                print(f"      - Total questions: {len(questions)}")
                print(f"      - Unique IDs: {unique_ids}")
                print(f"      - All unique: {unique_ids == len(questions)}")
                
                # Check duplicate question texts
                texts = [q.get('text') for q in questions]
                text_counts = Counter(texts)
                duplicates = [t for t, c in text_counts.items() if c > 1]
                print(f"\n   ?? Question Text Uniqueness Check:")
                print(f"      - Total questions: {len(questions)}")
                print(f"      - Unique texts: {len(text_counts)}")
                print(f"      - All unique: {len(duplicates) == 0}")
                if duplicates:
                    print(f"      - Duplicates found: {duplicates}")
                
                return True, num_questions == 10, len(questions) == 10, unique_ids == len(questions), len(duplicates) == 0
            else:
                print(f"   ? No questions returned")
                return False, False, False, False, False
        else:
            print(f"   ? Response: {data}")
            return False, False, False, False, False
    except Exception as e:
        print(f"   ? Error: {e}")
        return False, False, False, False, False

def test_skills(token, user_id):
    """Test skills endpoint."""
    print("\n?? Testing skills endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/students/{user_id}/skills",
            headers=headers
        )
        status = response.status_code
        data = response.json()
        print(f"   Status: {status}")
        print(f"   Response: {data}")
        return status == 200
    except Exception as e:
        print(f"   ? Error: {e}")
        return False

def test_assessments(token, user_id):
    """Test assessments endpoint."""
    print("\n?? Testing assessments endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/assessments/student/{user_id}",
            headers=headers
        )
        status = response.status_code
        data = response.json()
        print(f"   Status: {status}")
        print(f"   Response: {data}")
        return status == 200
    except Exception as e:
        print(f"   ? Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("COMPREHENSIVE ENDPOINT VALIDATION TEST")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Health
    results['health'] = test_health()
    
    # Test 2: Register
    reg_pass, token, user_id = test_register()
    results['register'] = reg_pass
    
    if reg_pass and token:
        # Test 3: Generate Assessment
        gen_pass, num_q_pass, arr_pass, unique_id_pass, unique_text_pass = test_generate_assessment(token, user_id)
        results['generate_assessment'] = gen_pass
        results['num_questions_10'] = num_q_pass
        results['mcq_array_exists'] = arr_pass
        results['unique_ids'] = unique_id_pass
        results['unique_texts'] = unique_text_pass
        
        # Test 4: Skills
        results['skills'] = test_skills(token, user_id)
        
        # Test 5: Assessments
        results['assessments'] = test_assessments(token, user_id)
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "? PASS" if passed else "? FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    print("=" * 60)
    print(f"Overall: {'? ALL TESTS PASSED' if all_passed else '? SOME TESTS FAILED'}")
    print("=" * 60)
    
    sys.exit(0 if all_passed else 1)
