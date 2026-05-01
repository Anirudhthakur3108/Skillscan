#!/usr/bin/env python3
"""
Full end-to-end flow test: Register -> Add Skill -> Configure -> Generate -> Check Diversity
"""
import requests
import json
from collections import Counter

BASE_URL = "http://localhost:5001"

def test_full_flow():
    print("=" * 80)
    print("FULL END-TO-END ASSESSMENT FLOW TEST")
    print("=" * 80)
    
    # 1. Health Check
    print("\n[1] Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"✓ Backend is running")
        else:
            print(f"✗ Health check failed")
            return
    except Exception as e:
        print(f"✗ Backend not accessible: {e}")
        return
    
    # 2. Register User
    print("\n[2] Register User")
    user_email = f"testuser_{hash('test')%10000}@test.com"
    try:
        register_resp = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": user_email, "password": "password123", "full_name": "Test User"},
            timeout=10
        )
        print(f"Status: {register_resp.status_code}")
        if register_resp.status_code in (200, 201):
            user_data = register_resp.json()
            student_id = user_data.get('student', {}).get('id')
            token = user_data.get('access_token')
            print(f"✓ User registered: {student_id}")
        else:
            print(f"✗ Registration failed: {register_resp.text}")
            return
    except Exception as e:
        print(f"✗ Registration error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Add Skill
    print("\n[3] Add Skill to Student Profile")
    try:
        skill_resp = requests.post(
            f"{BASE_URL}/students/{student_id}/skills/add-manual",
            json={"skill_name": "Python", "proficiency_claimed": 5},
            headers=headers,
            timeout=10
        )
        print(f"Status: {skill_resp.status_code}")
        if skill_resp.status_code in (200, 201):
            skill_data = skill_resp.json()
            # The add-manual endpoint returns the StudentSkill.id, but other
            # endpoints expect the taxonomy id (`skill_id`) from the GET skills
            # response. Fetch the canonical skill list and pick the taxonomy id.
            skills_list_resp = requests.get(
                f"{BASE_URL}/students/{student_id}/skills",
                headers=headers,
                timeout=10
            )
            if skills_list_resp.status_code != 200:
                print(f"✗ Failed to retrieve skills list: {skills_list_resp.text}")
                return
            skills = skills_list_resp.json().get('skills', [])
            # Find the taxonomy id for the newly added skill by name
            skill_entry = next((s for s in skills if s.get('skill_name') == 'Python'), None)
            if not skill_entry:
                print(f"✗ Could not find 'Python' in student's skills list")
                return
            skill_id = skill_entry.get('skill_id')
            print(f"✓ Skill added: {skill_entry.get('skill_name')} (taxonomy ID: {skill_id})")
        else:
            print(f"✗ Skill add failed: {skill_resp.text}")
            return
    except Exception as e:
        print(f"✗ Skill add error: {e}")
        return
    
    # 4. Configure Skill (difficulty + proficiency)
    print("\n[4] Configure Skill Difficulty and Proficiency")
    try:
        config_resp = requests.post(
            f"{BASE_URL}/students/{student_id}/skills/configure",
            json={
                "skills": [
                    {
                        "skill_id": skill_id,
                        "difficulty": 5,
                        "proficiency_claimed": 5
                    }
                ]
            },
            headers=headers,
            timeout=10
        )
        print(f"Status: {config_resp.status_code}")
        if config_resp.status_code == 200:
            print(f"✓ Skill configured (difficulty: 5, proficiency: 5)")
        else:
            print(f"✗ Configuration failed: {config_resp.text}")
            return
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return
    
    # 5. Generate Assessment
    print("\n[5] Generate Assessment (10 Questions Expected)")
    try:
        gen_resp = requests.post(
            f"{BASE_URL}/assessments/generate",
            json={
                "student_id": student_id,
                "skill_id": skill_id,
                "difficulty": 5,
                "proficiency_claimed": 5
            },
            headers=headers,
            timeout=30
        )
        print(f"Status: {gen_resp.status_code}")
        if gen_resp.status_code == 201:
            assessment_data = gen_resp.json()
            assessment_id = assessment_data.get('assessment_id')
            num_questions = assessment_data.get('num_questions')
            source = assessment_data.get('source')
            questions = assessment_data.get('questions', {}).get('mcq', [])
            
            print(f"✓ Assessment generated (ID: {assessment_id})")
            print(f"  - Source: {source}")
            print(f"  - Expected questions: {num_questions}")
            print(f"  - Actual MCQ count: {len(questions)}")
            
            if num_questions != 10:
                print(f"  ⚠ WARNING: Expected 10 questions, got {num_questions}")
            
            # 6. Check Question Diversity
            print("\n[6] Question Diversity Analysis")
            if len(questions) > 0:
                question_texts = [q.get('question', '') for q in questions]
                unique_questions = len(set(question_texts))
                
                print(f"  - Total questions: {len(questions)}")
                print(f"  - Unique questions: {unique_questions}")
                
                if unique_questions == len(questions):
                    print(f"  ✓ All questions are UNIQUE (no duplicates)")
                else:
                    print(f"  ✗ DUPLICATE questions detected!")
                    duplicates = [q for q, count in Counter(question_texts).items() if count > 1]
                    for q in duplicates[:3]:  # Show first 3 duplicates
                        print(f"    - {q[:60]}...")
                
                # Check question IDs uniqueness
                question_ids = [q.get('id', '') for q in questions]
                unique_ids = len(set(question_ids))
                
                if unique_ids == len(questions):
                    print(f"  ✓ All question IDs are UNIQUE")
                else:
                    print(f"  ✗ DUPLICATE question IDs detected")
                
                # Check difficulty variety
                difficulties = [q.get('difficulty', 0) for q in questions]
                unique_difficulties = len(set(difficulties))
                print(f"  - Difficulty levels: {sorted(set(difficulties))}")
                
                # Show first 3 questions
                print(f"\n  First 3 Questions:")
                for i, q in enumerate(questions[:3], 1):
                    print(f"    {i}. {q.get('question', '')[:70]}...")
                    print(f"       Difficulty: {q.get('difficulty', 'N/A')}")
            else:
                print(f"  ✗ No MCQ questions returned")
        else:
            print(f"✗ Generation failed: {gen_resp.text}")
            return
    except Exception as e:
        print(f"✗ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("FULL FLOW TEST COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == '__main__':
    test_full_flow()

