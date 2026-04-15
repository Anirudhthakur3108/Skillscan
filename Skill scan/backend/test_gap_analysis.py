"""
Gap Analysis Unit Tests
Comprehensive test suite for gap analyzer and gap analysis routes.
"""

import unittest
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from models import (
    Student, SkillsTaxonomy, SkillScore, Assessment, 
    AssessmentResponse, db, Base
)
from utils.gap_analyzer import GapAnalyzer, GAP_LOWER_THRESHOLD, GAP_UPPER_THRESHOLD
from utils.auth import generate_jwt_token


class GapAnalyzerTestCase(unittest.TestCase):
    """Test cases for GapAnalyzer class"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database and fixtures"""
        from app import app
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with cls.app.app_context():
            db.create_all()
            cls._seed_test_data()
    
    @classmethod
    def _seed_test_data(cls):
        """Seed test database with sample data"""
        # Create test student
        student = Student(
            email='test@example.com',
            password_hash='hashed_password',
            full_name='Test Student',
            user_type='MBA'
        )
        db.session.add(student)
        db.session.flush()
        
        # Create test skill
        skill = SkillsTaxonomy(
            name='Python Programming',
            category='Technical',
            description='Python fundamentals and advanced concepts',
            industry_benchmark=8,
            target_users=['MBA', 'BCA']
        )
        db.session.add(skill)
        db.session.flush()
        
        # Create test assessment
        assessment = Assessment(
            student_id=student.id,
            skill_id=skill.id,
            assessment_type='mcq',
            difficulty_level='medium',
            questions=[{'q1': 'question1'}, {'q2': 'question2'}],
            status='completed'
        )
        db.session.add(assessment)
        db.session.flush()
        
        # Create skill scores with gaps (60-79% = 6-7.9 on 1-10 scale)
        gap_scores = [6, 7, 6.5, 8, 5]  # 60%, 70%, 65%, 80%, 50%
        
        for score in gap_scores:
            skill_score = SkillScore(
                student_id=student.id,
                skill_id=skill.id,
                assessment_id=assessment.id,
                score=score,
                gaps_identified=['gap1', 'gap2'],
                reasoning='Test reasoning',
                ai_confidence=Decimal('0.85')
            )
            db.session.add(skill_score)
        
        db.session.commit()
        cls.student_id = student.id
        cls.skill_id = skill.id
    
    def setUp(self):
        """Set up test client and gap analyzer"""
        self.client = self.app.test_client()
        self.gap_analyzer = GapAnalyzer()
        self.app.app_context().push()
    
    def tearDown(self):
        """Clean up after tests"""
        self.app.app_context().pop()
    
    def test_gap_identification(self):
        """Test that gaps in 60-79% range are correctly identified"""
        gaps = self.gap_analyzer.analyze_gaps(self.student_id, self.skill_id)
        
        self.assertIsNotNone(gaps)
        self.assertGreater(len(gaps), 0)
        
        # Check that gap is in expected format
        gap = gaps[0]
        self.assertIn('gap_id', gap)
        self.assertIn('priority', gap)
        self.assertIn('frequency', gap)
        self.assertIn('impact', gap)
    
    def test_gap_priority_calculation(self):
        """Test priority calculation formula"""
        # Test normal calculation
        priority = self.gap_analyzer.calculate_gap_priority('test_gap', 60.0, 20.0)
        
        # Expected: (60 × 0.6) + (20 × 0.4) = 36 + 8 = 44
        expected = 44.0
        self.assertEqual(priority, expected)
    
    def test_gap_priority_with_extreme_values(self):
        """Test priority calculation with edge cases"""
        # All frequency
        priority1 = self.gap_analyzer.calculate_gap_priority('test', 100.0, 0.0)
        self.assertEqual(priority1, 60.0)  # 100 × 0.6 + 0 × 0.4
        
        # All impact
        priority2 = self.gap_analyzer.calculate_gap_priority('test', 0.0, 100.0)
        self.assertEqual(priority2, 40.0)  # 0 × 0.6 + 100 × 0.4
        
        # Both zero
        priority3 = self.gap_analyzer.calculate_gap_priority('test', 0.0, 0.0)
        self.assertEqual(priority3, 0.0)
    
    def test_benchmark_retrieval(self):
        """Test industry benchmark retrieval"""
        benchmark = self.gap_analyzer.get_industry_benchmark(self.skill_id)
        
        # Skill has industry_benchmark = 8 (1-10 scale) → 80%
        self.assertEqual(benchmark, 80)
    
    def test_percentile_calculation(self):
        """Test percentile ranking calculation"""
        percentile = self.gap_analyzer.calculate_percentile(self.student_id, self.skill_id, 7.0)
        
        # Valid percentile should be 0-100
        self.assertGreaterEqual(percentile, 0)
        self.assertLessEqual(percentile, 100)
        self.assertIsInstance(percentile, int)
    
    def test_best_and_worst_assessments(self):
        """Test identification of best and worst assessment scores"""
        result = self.gap_analyzer.get_best_and_worst_assessments(self.student_id, self.skill_id)
        
        self.assertIn('best', result)
        self.assertIn('worst', result)
        
        # Best should have higher score than worst
        best_score = result['best']['score']
        worst_score = result['worst']['score']
        self.assertGreater(best_score, worst_score)
    
    def test_gap_progression_tracking(self):
        """Test historical gap progression tracking"""
        progression = self.gap_analyzer.track_gap_progression(self.student_id, self.skill_id)
        
        self.assertIn('trend', progression)
        self.assertIn('progression', progression)
        self.assertIn('assessments', progression)
        
        # Trend should be one of valid values
        self.assertIn(progression['trend'], ['improving', 'stable', 'worsening', 'insufficient_data'])
    
    def test_gap_report_generation(self):
        """Test comprehensive gap report generation"""
        report = self.gap_analyzer.generate_gap_report(self.student_id, self.skill_id)
        
        self.assertNotIn('error', report)
        self.assertIn('skill_id', report)
        self.assertIn('skill_name', report)
        self.assertIn('current_score', report)
        self.assertIn('benchmark_score', report)
        self.assertIn('percentile', report)
        self.assertIn('gaps_identified', report)
        self.assertIn('weak_areas', report)
        self.assertIn('improvement_potential', report)
        self.assertIn('recommended_focus_areas', report)
    
    def test_weak_area_identification(self):
        """Test weak area clustering and grouping"""
        gaps = self.gap_analyzer.analyze_gaps(self.student_id, self.skill_id)
        weak_areas = self.gap_analyzer.identify_weak_areas(self.student_id, self.skill_id, gaps)
        
        self.assertIsNotNone(weak_areas)
        self.assertIsInstance(weak_areas, list)
        
        if weak_areas:
            weak_area = weak_areas[0]
            self.assertIn('theme', weak_area)
            self.assertIn('priority', weak_area)
            self.assertIn('gap_count', weak_area)
    
    def test_no_assessment_history(self):
        """Test behavior when student has no assessment history"""
        non_existent_student_id = 99999
        gaps = self.gap_analyzer.analyze_gaps(non_existent_student_id, self.skill_id)
        
        self.assertEqual(gaps, [])
    
    def test_gap_status_classification(self):
        """Test gap status classification"""
        # Test helper method
        status_expert = self.gap_analyzer._get_gap_status(95)
        status_good = self.gap_analyzer._get_gap_status(85)
        status_fair = self.gap_analyzer._get_gap_status(70)
        status_fundamental = self.gap_analyzer._get_gap_status(40)
        
        self.assertEqual(status_expert, 'expert')
        self.assertEqual(status_good, 'good')
        self.assertEqual(status_fair, 'fair')
        self.assertEqual(status_fundamental, 'fundamental')


class GapAnalysisRouteTestCase(unittest.TestCase):
    """Test cases for Gap Analysis Flask routes"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test application and database"""
        from app import app
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with cls.app.app_context():
            db.create_all()
            cls._seed_test_data()
    
    @classmethod
    def _seed_test_data(cls):
        """Seed test database"""
        # Create test student
        student = Student(
            email='test@example.com',
            password_hash='hashed_password',
            full_name='Test Student',
            user_type='MBA'
        )
        db.session.add(student)
        db.session.flush()
        
        # Create test skill
        skill = SkillsTaxonomy(
            name='Data Analysis',
            category='Analytics',
            description='Data analysis skills',
            industry_benchmark=7,
            target_users=['MBA']
        )
        db.session.add(skill)
        db.session.flush()
        
        # Create assessment
        assessment = Assessment(
            student_id=student.id,
            skill_id=skill.id,
            assessment_type='mcq',
            difficulty_level='medium',
            questions=[],
            status='completed'
        )
        db.session.add(assessment)
        db.session.flush()
        
        # Create skill scores
        for score in [6.5, 7.0, 5.5]:  # Scores in gap range
            skill_score = SkillScore(
                student_id=student.id,
                skill_id=skill.id,
                assessment_id=assessment.id,
                score=score,
                gaps_identified=[],
                ai_confidence=Decimal('0.8')
            )
            db.session.add(skill_score)
        
        db.session.commit()
        cls.student_id = student.id
        cls.skill_id = skill.id
        cls.token = generate_jwt_token(student.id, student.email)
    
    def setUp(self):
        """Set up test client"""
        self.client = self.app.test_client()
        self.app.app_context().push()
    
    def tearDown(self):
        """Clean up"""
        self.app.app_context().pop()
    
    def _get_headers(self):
        """Get authorization headers"""
        return {'Authorization': f'Bearer {self.token}'}
    
    def test_get_gap_analysis_endpoint(self):
        """Test GET /gap-analysis/<skill_id> endpoint"""
        response = self.client.get(
            f'/gap-analysis/{self.skill_id}',
            headers=self._get_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('skill_id', data)
        self.assertIn('skill_name', data)
        self.assertIn('current_score', data)
        self.assertIn('benchmark', data)
        self.assertIn('gaps_identified', data)
    
    def test_gap_analysis_unauthorized(self):
        """Test GET /gap-analysis/<skill_id> without authorization"""
        response = self.client.get(f'/gap-analysis/{self.skill_id}')
        
        # Should fail without token
        self.assertIn(response.status_code, [401, 403])
    
    def test_gap_analysis_invalid_skill(self):
        """Test GET /gap-analysis/<skill_id> with invalid skill"""
        response = self.client.get(
            '/gap-analysis/99999',
            headers=self._get_headers()
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_get_gap_report_endpoint(self):
        """Test GET /gap-analysis/report endpoint"""
        response = self.client.get(
            '/gap-analysis/report',
            headers=self._get_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('summary', data)
        self.assertIn('by_skill', data)
    
    def test_get_benchmarks_endpoint(self):
        """Test GET /gap-analysis/<skill_id>/benchmarks endpoint"""
        response = self.client.get(
            f'/gap-analysis/{self.skill_id}/benchmarks',
            headers=self._get_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('benchmarks', data)
        self.assertIn('student_performance', data)
    
    def test_get_trends_endpoint(self):
        """Test GET /gap-analysis/trends endpoint"""
        response = self.client.get(
            '/gap-analysis/trends',
            headers=self._get_headers()
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'success')
        self.assertIn('trends', data)


if __name__ == '__main__':
    unittest.main()
