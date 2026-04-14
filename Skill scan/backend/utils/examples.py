"""
Example usage of GeminiClient for SkillScan
Quick reference for common operations
"""

from utils.model_client import GeminiClient
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Example 1: Initialize client
def example_init():
    """Example: Initialize Gemini client"""
    print("=" * 70)
    print("EXAMPLE 1: Initialize Client")
    print("=" * 70)
    
    try:
        client = GeminiClient()
        print("✓ Client initialized successfully")
        return client
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return None


# Example 2: Generate MCQ Assessment
def example_generate_mcq(client):
    """Example: Generate MCQ assessment"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Generate MCQ Assessment")
    print("=" * 70)
    
    try:
        assessment = client.generate_assessment(
            skill="Python",
            proficiency=5,
            difficulty="medium",
            assessment_type="mcq"
        )
        
        print(f"✓ Generated MCQ assessment:")
        print(f"  - Questions: {len(assessment['questions'])}")
        print(f"  - Skill: {assessment['metadata']['skill']}")
        print(f"  - Difficulty: {assessment['metadata']['difficulty']}")
        print(f"  - Estimated Time: {assessment['metadata']['estimated_time_minutes']} minutes")
        
        # Print first question
        if assessment['questions']:
            q = assessment['questions'][0]
            print(f"\n  Sample Question:")
            print(f"    Q1: {q['question']}")
            print(f"    Options: {', '.join(q['options'][:2])}...")
            
    except Exception as e:
        print(f"✗ Failed to generate MCQ: {e}")


# Example 3: Generate Coding Challenge
def example_generate_coding(client):
    """Example: Generate coding challenge"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Generate Coding Challenge")
    print("=" * 70)
    
    try:
        assessment = client.generate_assessment(
            skill="Python",
            proficiency=6,
            difficulty="medium",
            assessment_type="coding"
        )
        
        print(f"✓ Generated coding assessment:")
        print(f"  - Problems: {len(assessment['problems'])}")
        print(f"  - Estimated Time: {assessment['metadata']['estimated_time_minutes']} minutes")
        
        if assessment['problems']:
            p = assessment['problems'][0]
            print(f"\n  Sample Problem:")
            print(f"    Title: {p['title']}")
            print(f"    Difficulty: {p['difficulty']}")
            print(f"    Time: {p['estimated_time_minutes']} minutes")
            
    except Exception as e:
        print(f"✗ Failed to generate coding challenge: {e}")


# Example 4: Generate Case Study
def example_generate_case_study(client):
    """Example: Generate case study"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Generate Case Study")
    print("=" * 70)
    
    try:
        assessment = client.generate_assessment(
            skill="SQL Optimization",
            proficiency=5,
            difficulty="medium",
            assessment_type="case_study"
        )
        
        print(f"✓ Generated case study assessment:")
        print(f"  - Case Studies: {len(assessment['case_studies'])}")
        print(f"  - Estimated Time: {assessment['metadata']['estimated_time_minutes']} minutes")
        
        if assessment['case_studies']:
            cs = assessment['case_studies'][0]
            print(f"\n  Sample Case Study:")
            print(f"    Title: {cs['title']}")
            print(f"    Questions: {len(cs['questions'])}")
            print(f"    Difficulty: {cs['difficulty']}")
            
    except Exception as e:
        print(f"✗ Failed to generate case study: {e}")


# Example 5: Score Assessment
def example_score_assessment(client):
    """Example: Score completed assessment"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Score Assessment")
    print("=" * 70)
    
    try:
        # Sample MCQ questions
        questions = [
            {
                "id": 1,
                "question": "What is the output of print(2**3)?",
                "options": ["A) 6", "B) 8", "C) 9", "D) 12"],
                "correct_answer": "B"
            },
            {
                "id": 2,
                "question": "Which keyword is used to define a function?",
                "options": ["A) func", "B) function", "C) def", "D) define"],
                "correct_answer": "C"
            }
        ]
        
        # Sample student responses
        responses = [
            {"question_id": 1, "selected_answer": "B"},
            {"question_id": 2, "selected_answer": "C"}
        ]
        
        score = client.score_assessment(
            assessment_type="mcq",
            questions=questions,
            responses=responses,
            skill="Python"
        )
        
        print(f"✓ Assessment scored:")
        print(f"  - Overall Score: {score['overall_score']}/10")
        print(f"  - Confidence: {score['confidence']}")
        print(f"  - Identified Gaps: {len(score['identified_gaps'])}")
        print(f"  - Strengths: {', '.join(score['strengths'][:2])}")
        print(f"  - Next Difficulty: {score['next_difficulty_recommended']}")
        
    except Exception as e:
        print(f"✗ Failed to score assessment: {e}")


# Example 6: Generate Learning Plan
def example_learning_plan(client):
    """Example: Generate personalized learning plan"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Generate Learning Plan")
    print("=" * 70)
    
    try:
        skill_gaps = [
            {
                "gap": "Advanced SQL optimization",
                "severity": "high",
                "priority_score": 9
            },
            {
                "gap": "Python pandas manipulation",
                "severity": "medium",
                "priority_score": 7
            }
        ]
        
        user_proficiency = {
            "SQL": 6,
            "Python": 5,
            "Excel": 8
        }
        
        learning_plan = client.generate_learning_plan(
            skill_gaps=skill_gaps,
            user_proficiency=user_proficiency,
            user_type="MBA_Analytics"
        )
        
        print(f"✓ Learning plan generated:")
        print(f"  - Gaps to Address: {len(learning_plan['priority_gaps'])}")
        print(f"  - Timeline: {learning_plan['overall_timeline_weeks']} weeks")
        print(f"  - Success Metrics: {len(learning_plan['success_metrics'])}")
        
        if learning_plan['priority_gaps']:
            gap = learning_plan['priority_gaps'][0]
            print(f"\n  Top Priority Gap:")
            print(f"    Gap: {gap['gap']}")
            print(f"    Severity: {gap['severity']}")
            print(f"    Recommendations: {len(gap['recommendations'])}")
            
    except Exception as e:
        print(f"✗ Failed to generate learning plan: {e}")


# Main execution
def main():
    """Run all examples"""
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  GeminiClient Usage Examples".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70)
    
    # Initialize client
    client = example_init()
    if not client:
        print("\n✗ Could not initialize client. Exiting.")
        return
    
    # Run examples
    example_generate_mcq(client)
    example_generate_coding(client)
    example_generate_case_study(client)
    example_score_assessment(client)
    example_learning_plan(client)
    
    print("\n" + "█" * 70)
    print("█" + "  Examples completed!".center(68) + "█")
    print("█" * 70 + "\n")


if __name__ == "__main__":
    main()
