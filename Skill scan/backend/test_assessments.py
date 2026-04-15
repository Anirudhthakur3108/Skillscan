"""
SkillScan MVP - Assessment Routes Tests
Comprehensive test suite for assessment generation, submission, and progress tracking
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from backend.app import create_app
from backend.database import get_db, init_db
from backend.models import (
    Student, SkillsTaxonomy, Assessment, AssessmentResponse,
    SkillScore, StudentSkill, Base
)
from backend.utils.auth import generate_jwt_token
from backend.utils.model_client import GeminiClient


@pytest.fixture
def app():
    """Create test application"""
    app = create_app('testing')
    
    with app.app_context():
        init_db()
        yield app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Create database session for tests"""
    db = get_db()
    yield db


@pytest.fixture
def test_student(db_session):
    """Create test student"""
    student = Student(
        email='test@example.com',
        password_hash='hashed_password',
        full_name='Test Student',
        user_type='MBA'
    )
    db_session.add(student)
    db_session.commit()
    return student


@pytest.fixture
def test_skills(db_session):
    """Create test skills"""
    skills = [
        SkillsTaxonomy(
            name='Data Analysis',
            category='Analytics',
            description='Data analysis and interpretation',
            industry_benchmark=7,
            target_users=['MBA', 'BCA']
        ),
        SkillsTaxonomy(
            name='Python Programming',
            category='Programming',
            description='Python programming fundamentals',
            industry_benchmark=8,
            target_users=['BCA']
        ),
        SkillsTaxonomy(
            name='Business Strategy',
            category='Strategy',
            description='Strategic business planning',
            industry_benchmark=6,
            target_users=['MBA']
        ),
    ]
    db_session.add_all(skills)
    db_session.commit()
    return skills


@pytest.fixture
def auth_token(test_student):
    """Generate authentication token for test student"""
    return generate_jwt_token(test_student.id, test_student.email)


@pytest.fixture
def mock_gemini_client():
    """Mock GeminiClient for assessment generation"""
    with patch('backend.routes.assessments.GeminiClient') as mock_client:
        instance = MagicMock()
        mock_client.return_value = instance
        
        # Mock generate_assessment
        instance.generate_assessment.return_value = {
            'questions': [
                {
                    'id': 1,
                    'question': 'What is data analysis?',
                    'options': ['A) Collection of data', 'B) Interpretation of data', 'C) Storage of data', 'D) Transmission of data'],
                    'correct_answer': 'B',
                    'explanation': 'Data analysis is the process of interpreting data'
                },
                {
                    'id': 2,
                    'question': 'Which tool is best for data visualization?',
                    'options': ['A) Excel', 'B) Tableau', 'C) Python', 'D) SQL'],
                    'correct_answer': 'B',
                    'explanation': 'Tableau is specialized for data visualization'
                }
            ]
        }
        
        # Mock score_assessment
        instance.score_assessment.return_value = {
            'score': 85,
            'feedback': 'Good understanding of concepts',
            'gaps_identified': [
                {'area': 'Advanced analytics', 'recommendation': 'Study regression models'}
            ],
            'confidence': 0.92
        }
        
        yield instance


class TestGenerateAssessment:
    """Test cases for POST /assessments/generate"""
    
    def test_generate_mcq_assessment_easy(self, client, test_student, test_skills, auth_token, mock_gemini_client):
        """Test MCQ assessment generation at easy level"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'assessment_id' in data
        assert data['assessment_type'] == 'mcq'
        assert data['difficulty'] == 'easy'
        assert data['timer_seconds'] == 360
        assert 'questions' in data
        assert len(data['questions']) > 0
    
    def test_generate_coding_assessment_medium(self, client, test_student, test_skills, auth_token, mock_gemini_client):
        """Test coding assessment generation at medium level"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[1].id,
                'difficulty': 'medium',
                'assessment_type': 'coding'
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['assessment_type'] == 'coding'
        assert data['difficulty'] == 'medium'
        assert data['timer_seconds'] == 3600
    
    def test_generate_case_study_assessment_hard(self, client, test_student, test_skills, auth_token, mock_gemini_client):
        """Test case study assessment generation at hard level"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[2].id,
                'difficulty': 'hard',
                'assessment_type': 'case_study'
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['assessment_type'] == 'case_study'
        assert data['difficulty'] == 'hard'
        assert data['timer_seconds'] == 1800
    
    def test_generate_assessment_missing_skill_id(self, client, auth_token):
        """Test generation fails without skill_id"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_generate_assessment_invalid_skill_id(self, client, auth_token, mock_gemini_client):
        """Test generation fails with non-existent skill"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': 999,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
    
    def test_generate_assessment_invalid_difficulty(self, client, test_skills, auth_token):
        """Test generation fails with invalid difficulty"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'impossible',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid difficulty' in data['error']
    
    def test_generate_assessment_invalid_type(self, client, test_skills, auth_token):
        """Test generation fails with invalid assessment type"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'easy',
                'assessment_type': 'invalid'
            },
            headers=headers
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid assessment_type' in data['error']
    
    def test_generate_assessment_unauthorized(self, client, test_skills):
        """Test generation fails without authentication"""
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            }
        )
        
        assert response.status_code == 401
    
    def test_generate_assessment_medium_requires_easy_pass(self, client, test_student, test_skills, auth_token, db_session):
        """Test medium difficulty is locked until easy is passed"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Attempt medium without passing easy
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'medium',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'Must score' in data['error']
    
    def test_generate_assessment_after_easy_unlock(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test medium becomes available after passing easy"""
        # Create passing easy assessment
        easy_assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='completed'
        )
        skill_score = SkillScore(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_id=None,
            score=8,  # 80%
            gaps_identified=[],
            reasoning='Good',
            ai_confidence=0.9
        )
        
        db_session.add(easy_assessment)
        db_session.flush()
        
        skill_score.assessment_id = easy_assessment.id
        db_session.add(skill_score)
        db_session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Now medium should be available
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'medium',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['difficulty'] == 'medium'


class TestSubmitAssessment:
    """Test cases for POST /assessments/{id}/submit"""
    
    def test_submit_assessment_perfect_score(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test submitting assessment with perfect score"""
        # Create assessment
        assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='generated'
        )
        db_session.add(assessment)
        db_session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            f'/assessments/{assessment.id}/submit',
            json={
                'responses': [
                    {'question_id': 1, 'answer': 'A'},
                    {'question_id': 2, 'answer': 'B'}
                ]
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['score'] == 85  # From mock
        assert data['badge'] == 'good'
        assert data['passed'] == True
    
    def test_submit_assessment_failing_score(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test submitting assessment with failing score"""
        assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='generated'
        )
        db_session.add(assessment)
        db_session.commit()
        
        # Mock failing score
        mock_gemini_client.score_assessment.return_value = {
            'score': 55,
            'feedback': 'Need more study',
            'gaps_identified': [
                {'area': 'Basics', 'recommendation': 'Review fundamentals'}
            ],
            'confidence': 0.85
        }
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            f'/assessments/{assessment.id}/submit',
            json={
                'responses': [
                    {'question_id': 1, 'answer': 'D'},
                    {'question_id': 2, 'answer': 'D'}
                ]
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['score'] == 55
        assert data['badge'] == 'needs_work'
        assert data['passed'] == False
    
    def test_submit_assessment_excellent_score(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test submitting assessment with excellent score"""
        assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='generated'
        )
        db_session.add(assessment)
        db_session.commit()
        
        # Mock excellent score
        mock_gemini_client.score_assessment.return_value = {
            'score': 95,
            'feedback': 'Excellent performance',
            'gaps_identified': [],
            'confidence': 0.98
        }
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            f'/assessments/{assessment.id}/submit',
            json={
                'responses': [
                    {'question_id': 1, 'answer': 'A'},
                    {'question_id': 2, 'answer': 'B'}
                ]
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['score'] == 95
        assert data['badge'] == 'excellent'
        assert data['passed'] == True
    
    def test_submit_assessment_missing_assessment_id(self, client, auth_token):
        """Test submission fails with non-existent assessment"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/999/submit',
            json={
                'responses': [
                    {'question_id': 1, 'answer': 'A'}
                ]
            },
            headers=headers
        )
        
        assert response.status_code == 404
    
    def test_submit_assessment_no_responses(self, client, test_student, test_skills, auth_token, db_session):
        """Test submission fails without responses"""
        assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='generated'
        )
        db_session.add(assessment)
        db_session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            f'/assessments/{assessment.id}/submit',
            json={'responses': []},
            headers=headers
        )
        
        assert response.status_code == 400
    
    def test_submit_assessment_unauthorized_user(self, client, test_student, test_skills, auth_token, db_session):
        """Test submission fails for other user's assessment"""
        # Create another student
        other_student = Student(
            email='other@example.com',
            password_hash='hashed_password',
            full_name='Other Student',
            user_type='MBA'
        )
        db_session.add(other_student)
        db_session.commit()
        
        # Create assessment for other student
        assessment = Assessment(
            student_id=other_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='generated'
        )
        db_session.add(assessment)
        db_session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            f'/assessments/{assessment.id}/submit',
            json={
                'responses': [
                    {'question_id': 1, 'answer': 'A'}
                ]
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_submit_assessment_unlocks_next_difficulty(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test that passing easy unlocks medium"""
        assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='generated'
        )
        db_session.add(assessment)
        db_session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            f'/assessments/{assessment.id}/submit',
            json={
                'responses': [
                    {'question_id': 1, 'answer': 'A'}
                ]
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['passed'] == True
        assert data['unlocked_next_difficulty'] == True
        assert data['next_difficulty'] == 'medium'


class TestGetProgress:
    """Test cases for GET /assessments/{skill_id}/progress"""
    
    def test_get_progress_no_attempts(self, client, test_student, test_skills, auth_token):
        """Test progress when no assessments attempted"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get(
            f'/assessments/{test_skills[0].id}/progress',
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['skill_id'] == test_skills[0].id
        assert 'progress' in data
        assert 'easy' in data['progress']
        assert 'medium' in data['progress']
        assert 'hard' in data['progress']
        
        # All should be locked except easy
        assert data['progress']['easy']['status'] in ['unlocked', 'completed']
        assert data['progress']['medium']['status'] == 'locked'
        assert data['progress']['hard']['status'] == 'locked'
    
    def test_get_progress_with_completion(self, client, test_student, test_skills, auth_token, db_session):
        """Test progress after completing assessments"""
        # Complete easy
        easy_assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='completed'
        )
        db_session.add(easy_assessment)
        db_session.flush()
        
        easy_score = SkillScore(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_id=easy_assessment.id,
            score=8,  # 80%
            gaps_identified=[],
            reasoning='Good',
            ai_confidence=0.9
        )
        db_session.add(easy_score)
        db_session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get(
            f'/assessments/{test_skills[0].id}/progress',
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['progress']['easy']['status'] == 'completed'
        assert data['progress']['easy']['best_score'] == 80
        assert data['progress']['easy']['attempts'] == 1
        assert data['progress']['medium']['status'] == 'unlocked'
    
    def test_get_progress_invalid_skill(self, client, auth_token):
        """Test progress fails for non-existent skill"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get(
            '/assessments/999/progress',
            headers=headers
        )
        
        assert response.status_code == 404
    
    def test_get_progress_unauthorized(self, client, test_skills):
        """Test progress fails without authentication"""
        response = client.get(
            f'/assessments/{test_skills[0].id}/progress'
        )
        
        assert response.status_code == 401


class TestGetAvailableSkills:
    """Test cases for GET /assessments/available"""
    
    def test_get_available_skills(self, client, test_student, test_skills, auth_token):
        """Test retrieving list of available skills"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get(
            '/assessments/available',
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'skills' in data
        assert 'total' in data
        assert data['total'] == 3
        
        # Check skill structure
        skill = data['skills'][0]
        assert 'id' in skill
        assert 'name' in skill
        assert 'category' in skill
        assert 'description' in skill
        assert 'industry_benchmark' in skill
    
    def test_get_available_skills_correct_fields(self, client, auth_token, test_skills):
        """Test all required fields are present"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get(
            '/assessments/available',
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Find Data Analysis skill
        data_analysis = next(s for s in data['skills'] if s['name'] == 'Data Analysis')
        assert data_analysis['category'] == 'Analytics'
        assert data_analysis['industry_benchmark'] == 7
    
    def test_get_available_skills_unauthorized(self, client):
        """Test fails without authentication"""
        response = client.get('/assessments/available')
        assert response.status_code == 401


class TestDifficultyProgression:
    """Test cases for difficulty progression and unlock logic"""
    
    def test_easy_always_available(self, client, test_student, test_skills, auth_token, mock_gemini_client):
        """Test easy difficulty is always available"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 201
    
    def test_score_below_threshold_blocks_unlock(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test score below 70% does not unlock next difficulty"""
        # Complete easy with 65%
        easy_assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='completed'
        )
        db_session.add(easy_assessment)
        db_session.flush()
        
        easy_score = SkillScore(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_id=easy_assessment.id,
            score=6,  # 60% on 1-10 scale
            gaps_identified=[],
            reasoning='Below threshold',
            ai_confidence=0.85
        )
        db_session.add(easy_score)
        db_session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Attempt medium should fail
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'medium',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        
        assert response.status_code == 403
    
    def test_full_progression_easy_to_medium_to_hard(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test complete progression through all difficulties"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        # Easy available
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        assert response.status_code == 201
        
        # Create passing score for easy
        easy_assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='completed'
        )
        db_session.add(easy_assessment)
        db_session.flush()
        
        easy_score = SkillScore(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_id=easy_assessment.id,
            score=8,  # 80%
            gaps_identified=[],
            reasoning='Good',
            ai_confidence=0.9
        )
        db_session.add(easy_score)
        db_session.commit()
        
        # Medium now available
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'medium',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        assert response.status_code == 201
        
        # Create passing score for medium
        medium_assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='medium',
            questions={'q': 1},
            status='completed'
        )
        db_session.add(medium_assessment)
        db_session.flush()
        
        medium_score = SkillScore(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_id=medium_assessment.id,
            score=9,  # 90%
            gaps_identified=[],
            reasoning='Excellent',
            ai_confidence=0.95
        )
        db_session.add(medium_score)
        db_session.commit()
        
        # Hard now available
        response = client.post(
            '/assessments/generate',
            json={
                'skill_id': test_skills[0].id,
                'difficulty': 'hard',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        assert response.status_code == 201


class TestRetakes:
    """Test cases for assessment retake functionality"""
    
    def test_unlimited_retakes_allowed(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client):
        """Test student can retake assessment unlimited times"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        skill_id = test_skills[0].id
        
        # First attempt
        response1 = client.post(
            '/assessments/generate',
            json={
                'skill_id': skill_id,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        assert response1.status_code == 201
        assessment1_id = response1.get_json()['assessment_id']
        
        # Submit first attempt
        response_submit1 = client.post(
            f'/assessments/{assessment1_id}/submit',
            json={'responses': [{'question_id': 1, 'answer': 'A'}]},
            headers=headers
        )
        assert response_submit1.status_code == 200
        
        # Second attempt (retake)
        response2 = client.post(
            '/assessments/generate',
            json={
                'skill_id': skill_id,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        assert response2.status_code == 201
        assert response2.get_json()['assessment_id'] != assessment1_id
        
        # Third attempt (second retake)
        response3 = client.post(
            '/assessments/generate',
            json={
                'skill_id': skill_id,
                'difficulty': 'easy',
                'assessment_type': 'mcq'
            },
            headers=headers
        )
        assert response3.status_code == 201
        assert response3.get_json()['assessment_id'] != assessment1_id


class TestBadgeMapping:
    """Test cases for score to badge conversion"""
    
    @pytest.mark.parametrize('score,expected_badge', [
        (95, 'excellent'),
        (90, 'excellent'),
        (89, 'good'),
        (80, 'good'),
        (79, 'fair'),
        (70, 'fair'),
        (69, 'needs_work'),
        (50, 'needs_work'),
        (0, 'needs_work'),
    ])
    def test_badge_mapping(self, client, test_student, test_skills, auth_token, db_session, mock_gemini_client, score, expected_badge):
        """Test correct badge mapping for various scores"""
        assessment = Assessment(
            student_id=test_student.id,
            skill_id=test_skills[0].id,
            assessment_type='mcq',
            difficulty_level='easy',
            questions={'q': 1},
            status='generated'
        )
        db_session.add(assessment)
        db_session.commit()
        
        # Mock specific score
        mock_gemini_client.score_assessment.return_value = {
            'score': score,
            'feedback': f'Score: {score}',
            'gaps_identified': [],
            'confidence': 0.85
        }
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(
            f'/assessments/{assessment.id}/submit',
            json={'responses': [{'question_id': 1, 'answer': 'A'}]},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['badge'] == expected_badge


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
