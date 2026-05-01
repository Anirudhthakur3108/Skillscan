#!/usr/bin/env python3
"""Test the dashboard endpoints with a real JWT token."""
import requests
import json
import sys

BASE_URL = "http://localhost:5001"

def register_test_user():
    """Register a test user and return the JWT token."""
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "email": f"testuser_{int(time.time())}@test.com",
            "password": "Test123!",
            "full_name": "Test User"
        }
    )
    if response.status_code == 201:
        data = response.json()
        token = data.get("access_token")
        student = data.get("student", {})
        user_id = student.get("id")
        print(f"✓ Registered user: {user_id}")
        print(f"✓ Email: {student.get('email')}")
        print(f"✓ Token: {token[:50]}...")
        return token, user_id
    else:
        print(f"✗ Registration failed: {response.status_code}")
        print(response.text)
        return None, None

def test_assessments_endpoint(token, user_id):
    """Test the /assessments/student/<id> endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/assessments/student/{user_id}",
        headers=headers
    )
    print(f"\n📋 Assessments Endpoint Test")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response

def test_skills_endpoint(token, user_id):
    """Test the /students/<id>/skills endpoint."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/students/{user_id}/skills",
        headers=headers
    )
    print(f"\n🎯 Skills Endpoint Test")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    return response

if __name__ == "__main__":
    import time
    
    # Test 1: Health check
    print("🏥 Testing health endpoint...")
    try:
        health = requests.get(f"{BASE_URL}/health")
        print(f"✓ Health: {health.status_code} - {health.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        sys.exit(1)
    
    # Test 2: Register user
    print("\n📝 Registering test user...")
    token = None
    user_id = None
    token, user_id = register_test_user()
    if not token or not user_id:
        print(f"✗ Registration failed, token={token}, user_id={user_id}")
        sys.exit(1)
    
    # Test 3: Test assessments endpoint
    print("\n🔍 Testing endpoints...")
    test_assessments_endpoint(token, user_id)
    test_skills_endpoint(token, user_id)
    
    print("\n✓ All tests completed!")
