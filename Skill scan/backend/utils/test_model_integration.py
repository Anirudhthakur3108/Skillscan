"""
Comprehensive test suite for GeminiClient integration
Tests all assessment types, difficulties, and features
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.model_client import GeminiClient


class TestRunner:
    """Test runner with reporting capabilities."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
        self.client = None
    
    def initialize_client(self):
        """Initialize Gemini client."""
        print("\n" + "="*70)
        print("INITIALIZING GEMINI CLIENT")
        print("="*70)
        try:
            self.client = GeminiClient()
            self.log_result("✅ Client Initialization", True, "Gemini API client initialized successfully")
            return True
        except Exception as e:
            self.log_result("❌ Client Initialization", False, str(e))
            return False
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        self.tests.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "details": details
        })
    
    def print_separator(self, title: str):
        """Print section separator."""
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70)
    
    def print_summary(self):
        """Print test summary."""
        self.print_separator("TEST SUMMARY")
        print(f"\nTotal Tests: {self.passed + self.failed}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Pass Rate: {(self.passed / (self.passed + self.failed) * 100):.1f}%")
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
        else:
            print(f"\n⚠️  {self.failed} test(s) failed")
    
    # ========================================================================
    # MCQ Assessment Tests
    # ========================================================================
    
    def test_mcq_easy(self):
        """Test MCQ generation at easy difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="Python",
                proficiency=3,
                difficulty="easy",
                assessment_type="mcq"
            )
            
            # Validate structure
            assert "questions" in assessment, "Missing questions"
            assert "metadata" in assessment, "Missing metadata"
            assert len(assessment["questions"]) == 5, "Should have 5 questions"
            
            # Print sample
            q = assessment["questions"][0]
            sample = f"Q1: {q['question'][:60]}... | Difficulty: {q['difficulty']}"
            
            self.log_result(
                "MCQ Generation (Easy)",
                True,
                f"{len(assessment['questions'])} questions generated. {sample}"
            )
        except Exception as e:
            self.log_result("MCQ Generation (Easy)", False, str(e))
    
    def test_mcq_medium(self):
        """Test MCQ generation at medium difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="React",
                proficiency=6,
                difficulty="medium",
                assessment_type="mcq"
            )
            
            assert "questions" in assessment
            assert len(assessment["questions"]) == 5
            
            q = assessment["questions"][0]
            sample = f"Q1: {q['question'][:60]}... | Difficulty: {q['difficulty']}"
            
            self.log_result(
                "MCQ Generation (Medium)",
                True,
                f"{len(assessment['questions'])} questions generated. {sample}"
            )
        except Exception as e:
            self.log_result("MCQ Generation (Medium)", False, str(e))
    
    def test_mcq_hard(self):
        """Test MCQ generation at hard difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="Advanced Python",
                proficiency=8,
                difficulty="hard",
                assessment_type="mcq"
            )
            
            assert "questions" in assessment
            assert len(assessment["questions"]) == 5
            
            q = assessment["questions"][0]
            sample = f"Q1: {q['question'][:60]}... | Difficulty: {q['difficulty']}"
            
            self.log_result(
                "MCQ Generation (Hard)",
                True,
                f"{len(assessment['questions'])} questions generated. {sample}"
            )
        except Exception as e:
            self.log_result("MCQ Generation (Hard)", False, str(e))
    
    # ========================================================================
    # Coding Challenge Tests
    # ========================================================================
    
    def test_coding_easy(self):
        """Test coding challenge generation at easy difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="Python",
                proficiency=4,
                difficulty="easy",
                assessment_type="coding"
            )
            
            assert "problems" in assessment
            assert len(assessment["problems"]) >= 1
            
            p = assessment["problems"][0]
            sample = f"P1: {p['title'][:50]}... | Difficulty: {p['difficulty']}"
            
            self.log_result(
                "Coding Challenge (Easy)",
                True,
                f"{len(assessment['problems'])} problems generated. {sample}"
            )
        except Exception as e:
            self.log_result("Coding Challenge (Easy)", False, str(e))
    
    def test_coding_medium(self):
        """Test coding challenge generation at medium difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="JavaScript",
                proficiency=6,
                difficulty="medium",
                assessment_type="coding"
            )
            
            assert "problems" in assessment
            assert len(assessment["problems"]) >= 1
            
            p = assessment["problems"][0]
            sample = f"P1: {p['title'][:50]}... | Difficulty: {p['difficulty']}"
            
            self.log_result(
                "Coding Challenge (Medium)",
                True,
                f"{len(assessment['problems'])} problems generated. {sample}"
            )
        except Exception as e:
            self.log_result("Coding Challenge (Medium)", False, str(e))
    
    def test_coding_hard(self):
        """Test coding challenge generation at hard difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="Data Structures",
                proficiency=8,
                difficulty="hard",
                assessment_type="coding"
            )
            
            assert "problems" in assessment
            assert len(assessment["problems"]) >= 1
            
            p = assessment["problems"][0]
            sample = f"P1: {p['title'][:50]}... | Difficulty: {p['difficulty']}"
            
            self.log_result(
                "Coding Challenge (Hard)",
                True,
                f"{len(assessment['problems'])} problems generated. {sample}"
            )
        except Exception as e:
            self.log_result("Coding Challenge (Hard)", False, str(e))
    
    # ========================================================================
    # Case Study Tests
    # ========================================================================
    
    def test_case_study_easy(self):
        """Test case study generation at easy difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="SQL Optimization",
                proficiency=4,
                difficulty="easy",
                assessment_type="case_study"
            )
            
            assert "case_studies" in assessment
            assert len(assessment["case_studies"]) >= 1
            
            cs = assessment["case_studies"][0]
            sample = f"CS1: {cs['title'][:50]}... | Difficulty: {cs['difficulty']}"
            
            self.log_result(
                "Case Study (Easy)",
                True,
                f"{len(assessment['case_studies'])} case study(ies) generated. {sample}"
            )
        except Exception as e:
            self.log_result("Case Study (Easy)", False, str(e))
    
    def test_case_study_medium(self):
        """Test case study generation at medium difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="Database Design",
                proficiency=6,
                difficulty="medium",
                assessment_type="case_study"
            )
            
            assert "case_studies" in assessment
            assert len(assessment["case_studies"]) >= 1
            
            cs = assessment["case_studies"][0]
            sample = f"CS1: {cs['title'][:50]}... | Difficulty: {cs['difficulty']}"
            
            self.log_result(
                "Case Study (Medium)",
                True,
                f"{len(assessment['case_studies'])} case study(ies) generated. {sample}"
            )
        except Exception as e:
            self.log_result("Case Study (Medium)", False, str(e))
    
    def test_case_study_hard(self):
        """Test case study generation at hard difficulty."""
        try:
            assessment = self.client.generate_assessment(
                skill="System Architecture",
                proficiency=9,
                difficulty="hard",
                assessment_type="case_study"
            )
            
            assert "case_studies" in assessment
            assert len(assessment["case_studies"]) >= 1
            
            cs = assessment["case_studies"][0]
            sample = f"CS1: {cs['title'][:50]}... | Difficulty: {cs['difficulty']}"
            
            self.log_result(
                "Case Study (Hard)",
                True,
                f"{len(assessment['case_studies'])} case study(ies) generated. {sample}"
            )
        except Exception as e:
            self.log_result("Case Study (Hard)", False, str(e))
    
    # ========================================================================
    # Assessment Scoring Tests
    # ========================================================================
    
    def test_scoring_mcq(self):
        """Test MCQ assessment scoring."""
        try:
            # Sample MCQ questions and responses
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
            
            responses = [
                {"question_id": 1, "selected_answer": "B"},
                {"question_id": 2, "selected_answer": "C"}
            ]
            
            scoring = self.client.score_assessment(
                assessment_type="mcq",
                questions=questions,
                responses=responses,
                skill="Python"
            )
            
            assert "overall_score" in scoring
            assert 1 <= scoring["overall_score"] <= 10
            assert "identified_gaps" in scoring
            assert "confidence" in scoring
            
            self.log_result(
                "MCQ Assessment Scoring",
                True,
                f"Score: {scoring['overall_score']}/10 | Confidence: {scoring.get('confidence', 'N/A')}"
            )
        except Exception as e:
            self.log_result("MCQ Assessment Scoring", False, str(e))
    
    def test_scoring_coding(self):
        """Test coding challenge scoring."""
        try:
            questions = [
                {
                    "id": 1,
                    "title": "Simple Calculator",
                    "description": "Write a function to add two numbers"
                }
            ]
            
            responses = [
                {
                    "question_id": 1,
                    "code": "def add(a, b):\n    return a + b"
                }
            ]
            
            scoring = self.client.score_assessment(
                assessment_type="coding",
                questions=questions,
                responses=responses,
                skill="Python"
            )
            
            assert "overall_score" in scoring
            assert 1 <= scoring["overall_score"] <= 10
            
            self.log_result(
                "Coding Challenge Scoring",
                True,
                f"Score: {scoring['overall_score']}/10"
            )
        except Exception as e:
            self.log_result("Coding Challenge Scoring", False, str(e))
    
    def test_scoring_case_study(self):
        """Test case study scoring."""
        try:
            questions = [
                {
                    "id": 1,
                    "question": "What approach would you take to optimize this query?"
                }
            ]
            
            responses = [
                {
                    "question_id": 1,
                    "answer": "I would add appropriate indexes and analyze the query execution plan"
                }
            ]
            
            scoring = self.client.score_assessment(
                assessment_type="case_study",
                questions=questions,
                responses=responses,
                skill="SQL"
            )
            
            assert "overall_score" in scoring
            assert 1 <= scoring["overall_score"] <= 10
            
            self.log_result(
                "Case Study Scoring",
                True,
                f"Score: {scoring['overall_score']}/10"
            )
        except Exception as e:
            self.log_result("Case Study Scoring", False, str(e))
    
    # ========================================================================
    # Learning Plan Generation Tests
    # ========================================================================
    
    def test_learning_plan_mba(self):
        """Test learning plan generation for MBA student."""
        try:
            skill_gaps = [
                {
                    "gap": "Advanced SQL optimization",
                    "severity": "high",
                    "priority_score": 9
                },
                {
                    "gap": "Python data manipulation",
                    "severity": "medium",
                    "priority_score": 7
                }
            ]
            
            user_proficiency = {
                "SQL": 6,
                "Python": 5,
                "Excel": 8
            }
            
            learning_plan = self.client.generate_learning_plan(
                skill_gaps=skill_gaps,
                user_proficiency=user_proficiency,
                user_type="MBA_Analytics"
            )
            
            assert "priority_gaps" in learning_plan
            assert "overall_timeline_weeks" in learning_plan
            assert len(learning_plan["priority_gaps"]) > 0
            
            timeline = learning_plan.get("overall_timeline_weeks", "N/A")
            gaps_count = len(learning_plan["priority_gaps"])
            
            self.log_result(
                "Learning Plan Generation (MBA)",
                True,
                f"{gaps_count} gaps covered | Timeline: {timeline} weeks"
            )
        except Exception as e:
            self.log_result("Learning Plan Generation (MBA)", False, str(e))
    
    def test_learning_plan_bca(self):
        """Test learning plan generation for BCA student."""
        try:
            skill_gaps = [
                {
                    "gap": "Data Structures & Algorithms",
                    "severity": "high",
                    "priority_score": 10
                },
                {
                    "gap": "Web Development Fundamentals",
                    "severity": "medium",
                    "priority_score": 8
                }
            ]
            
            user_proficiency = {
                "Python": 7,
                "C++": 5,
                "Web Development": 4
            }
            
            learning_plan = self.client.generate_learning_plan(
                skill_gaps=skill_gaps,
                user_proficiency=user_proficiency,
                user_type="BCA"
            )
            
            assert "priority_gaps" in learning_plan
            assert "overall_timeline_weeks" in learning_plan
            
            timeline = learning_plan.get("overall_timeline_weeks", "N/A")
            gaps_count = len(learning_plan["priority_gaps"])
            
            self.log_result(
                "Learning Plan Generation (BCA)",
                True,
                f"{gaps_count} gaps covered | Timeline: {timeline} weeks"
            )
        except Exception as e:
            self.log_result("Learning Plan Generation (BCA)", False, str(e))
    
    # ========================================================================
    # Main Test Execution
    # ========================================================================
    
    def run_all_tests(self):
        """Run all tests."""
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  SKILLSCAN GEMINI CLIENT - COMPREHENSIVE TEST SUITE".center(68) + "█")
        print("█" + f"  Test Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70)
        
        # Initialize client
        if not self.initialize_client():
            print("\n❌ Failed to initialize Gemini client. Cannot proceed with tests.")
            return
        
        # MCQ Tests
        self.print_separator("MCQ ASSESSMENT TESTS")
        self.test_mcq_easy()
        self.test_mcq_medium()
        self.test_mcq_hard()
        
        # Coding Tests
        self.print_separator("CODING CHALLENGE TESTS")
        self.test_coding_easy()
        self.test_coding_medium()
        self.test_coding_hard()
        
        # Case Study Tests
        self.print_separator("CASE STUDY TESTS")
        self.test_case_study_easy()
        self.test_case_study_medium()
        self.test_case_study_hard()
        
        # Scoring Tests
        self.print_separator("ASSESSMENT SCORING TESTS")
        self.test_scoring_mcq()
        self.test_scoring_coding()
        self.test_scoring_case_study()
        
        # Learning Plan Tests
        self.print_separator("LEARNING PLAN GENERATION TESTS")
        self.test_learning_plan_mba()
        self.test_learning_plan_bca()
        
        # Print summary
        self.print_summary()
        
        return self.failed == 0


def main():
    """Main test execution."""
    runner = TestRunner()
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
