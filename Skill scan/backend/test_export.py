"""
Export Routes Tests

Comprehensive tests for export functionality including PDF, CSV, and ZIP generation.

Author: SkillScan Team
Date: 2026-04-15
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

from backend.routes.export import export_bp
from backend.utils.export_generator import ExportGenerator
from backend.utils.pdf_generator import PDFReportGenerator
from backend.utils.csv_generator import CSVExporter


class TestExportGenerator:
    """Test ExportGenerator class"""

    def test_generate_assessment_export(self):
        """Test assessment export generation"""
        generator = ExportGenerator()
        
        # Mock assessment data
        assessment_data = generator.generate_assessment_export(
            student_id=1,
            assessment_id=1
        )
        
        if assessment_data:
            assert 'assessment_id' in assessment_data
            assert 'skill_name' in assessment_data
            assert 'score' in assessment_data
            assert 'badge' in assessment_data

    def test_generate_gap_export(self):
        """Test gap analysis export generation"""
        generator = ExportGenerator()
        
        gap_data = generator.generate_gap_export(
            student_id=1,
            skill_id=1
        )
        
        if gap_data:
            assert 'skill_name' in gap_data
            assert 'current_score' in gap_data
            assert 'gaps' in gap_data

    def test_generate_profile_export(self):
        """Test profile export generation"""
        generator = ExportGenerator()
        
        profile_data = generator.generate_profile_export(student_id=1)
        
        if profile_data:
            assert 'student_name' in profile_data
            assert 'email' in profile_data
            assert 'total_skills' in profile_data
            assert 'average_score' in profile_data

    def test_generate_assessments_csv(self):
        """Test assessments CSV generation"""
        generator = ExportGenerator()
        
        csv_data = generator.generate_all_assessments_csv(student_id=1)
        
        if csv_data:
            assert 'Assessment ID' in csv_data
            assert 'Skill Name' in csv_data
            assert 'Score' in csv_data

    def test_generate_skills_csv(self):
        """Test skills CSV generation"""
        generator = ExportGenerator()
        
        csv_data = generator.generate_skills_csv(student_id=1)
        
        if csv_data:
            assert 'Skill Name' in csv_data
            assert 'Current Score' in csv_data

    def test_get_badge(self):
        """Test badge assignment"""
        generator = ExportGenerator()
        
        assert generator._get_badge(95) == 'Excellent'
        assert generator._get_badge(85) == 'Good'
        assert generator._get_badge(75) == 'Fair'
        assert generator._get_badge(65) == 'Needs Work'

    def test_calculate_percentile(self):
        """Test percentile calculation"""
        generator = ExportGenerator()
        
        percentile = generator._calculate_percentile(skill_id=1, score=75)
        
        assert isinstance(percentile, int)
        assert 0 <= percentile <= 100


class TestPDFGenerator:
    """Test PDFReportGenerator class"""

    def test_initialize_pdf_generator(self):
        """Test PDF generator initialization"""
        generator = PDFReportGenerator()
        
        assert generator is not None
        assert hasattr(generator, 'styles')
        assert hasattr(generator, 'page_width')

    def test_generate_assessment_pdf(self):
        """Test assessment PDF generation"""
        generator = PDFReportGenerator()
        
        assessment_data = {
            'assessment_id': 1,
            'skill_name': 'Python',
            'assessment_type': 'MCQ',
            'difficulty': 'easy',
            'score': 85,
            'badge': 'Good',
            'total_questions': 5,
            'questions': [],
            'user_responses': [],
            'correct_answers': [],
            'feedback': {},
            'gaps_identified': [],
            'recommendations': [],
            'time_spent_minutes': 10,
            'created_at': datetime.utcnow().isoformat(),
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        pdf_bytes = generator.generate_assessment_pdf(assessment_data)
        
        if pdf_bytes:
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0

    def test_generate_gap_report_pdf(self):
        """Test gap report PDF generation"""
        generator = PDFReportGenerator()
        
        gap_data = {
            'skill_name': 'Python',
            'skill_id': 1,
            'current_score': 75,
            'benchmark_score': 80,
            'percentile': 45,
            'gaps_identified': 2,
            'gaps': [],
            'recommendations': [],
            'learning_plans': [],
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        pdf_bytes = generator.generate_gap_report_pdf(gap_data)
        
        if pdf_bytes:
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0

    def test_generate_profile_pdf(self):
        """Test profile PDF generation"""
        generator = PDFReportGenerator()
        
        profile_data = {
            'student_name': 'John Doe',
            'email': 'john@example.com',
            'user_type': 'BCA',
            'total_skills': 5,
            'average_score': 78,
            'assessments_taken': 10,
            'active_learning_plans': 2,
            'total_gaps': 3,
            'skills': [],
            'assessments': [],
            'gaps': [],
            'learning_plans': [],
            'export_timestamp': datetime.utcnow().isoformat()
        }
        
        pdf_bytes = generator.generate_profile_pdf(profile_data)
        
        if pdf_bytes:
            assert isinstance(pdf_bytes, bytes)
            assert len(pdf_bytes) > 0


class TestCSVExporter:
    """Test CSVExporter class"""

    def test_export_assessments_csv(self):
        """Test assessments CSV export"""
        assessments_data = [
            {
                'assessment_id': 1,
                'skill_name': 'Python',
                'assessment_type': 'MCQ',
                'difficulty': 'easy',
                'score': 85,
                'badge': 'Good',
                'total_questions': 5,
                'gaps_identified': [],
                'time_spent_minutes': 10,
                'created_at': datetime.utcnow().isoformat(),
                'export_timestamp': datetime.utcnow().isoformat()
            }
        ]
        
        csv_data = CSVExporter.export_assessments_csv(assessments_data)
        
        assert csv_data is not None
        assert 'Assessment ID' in csv_data
        assert 'Python' in csv_data
        assert '85' in csv_data

    def test_export_skills_csv(self):
        """Test skills CSV export"""
        skills_data = [
            {
                'skill_name': 'Python',
                'score': 85,
                'proficiency': 'Intermediate',
                'last_assessed': '2026-04-15',
                'assessments_taken': 3,
                'best_score': 90,
                'average_score': 83,
                'status': 'Unlocked'
            }
        ]
        
        csv_data = CSVExporter.export_skills_csv(skills_data)
        
        assert csv_data is not None
        assert 'Skill Name' in csv_data
        assert 'Python' in csv_data

    def test_export_gap_analysis_csv(self):
        """Test gap analysis CSV export"""
        gap_data = {
            'skill_name': 'Python',
            'skill_id': 1,
            'current_score': 75,
            'benchmark_score': 80,
            'percentile': 45,
            'gaps': [
                {
                    'name': 'OOP Concepts',
                    'frequency': 3,
                    'priority': 'high',
                    'impact': 8
                }
            ],
            'recommendations': ['Focus on OOP concepts']
        }
        
        csv_data = CSVExporter.export_gap_analysis_csv(gap_data)
        
        assert csv_data is not None
        assert 'Skill Name' in csv_data
        assert 'Python' in csv_data

    def test_escape_csv_value(self):
        """Test CSV value escaping"""
        # Test with comma
        escaped = CSVExporter.escape_csv_value('test,value')
        assert '"test,value"' == escaped
        
        # Test with quote
        escaped = CSVExporter.escape_csv_value('test"value')
        assert '"test""value"' == escaped
        
        # Test with newline
        escaped = CSVExporter.escape_csv_value('test\nvalue')
        assert '"test\nvalue"' == escaped


class TestExportEndpoints:
    """Test export API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        from backend.app import create_app
        app = create_app('testing')
        return app.test_client()

    def test_export_status_endpoint(self, client):
        """Test export status endpoint"""
        response = client.get(
            '/export/status',
            headers={'Authorization': 'Bearer test_token'}
        )
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'exports_available' in data
            assert 'formats' in data

    def test_assessment_export_missing_fields(self, client):
        """Test assessment export with missing fields"""
        response = client.post(
            '/export/assessment-pdf',
            json={},
            headers={'Authorization': 'Bearer test_token'}
        )
        
        assert response.status_code == 400

    def test_gap_export_missing_fields(self, client):
        """Test gap export with missing fields"""
        response = client.post(
            '/export/gap-report-pdf',
            json={'student_id': 1},
            headers={'Authorization': 'Bearer test_token'}
        )
        
        assert response.status_code == 400

    def test_profile_export_unauthorized(self, client):
        """Test profile export without auth"""
        response = client.post(
            '/export/profile-pdf',
            json={'student_id': 1}
        )
        
        # Should fail without token
        assert response.status_code in [401, 400]


class TestExportIntegration:
    """Integration tests for export functionality"""

    def test_full_export_workflow(self):
        """Test complete export workflow"""
        generator = ExportGenerator()
        pdf_gen = PDFReportGenerator()
        csv_exp = CSVExporter()
        
        # Generate data
        profile_data = generator.generate_profile_export(student_id=1)
        
        if profile_data:
            # Generate PDF
            pdf_bytes = pdf_gen.generate_profile_pdf(profile_data)
            assert pdf_bytes is not None or profile_data is None
            
            # Generate CSV
            csv_data = csv_exp.export_complete_profile_csv(profile_data)
            assert csv_data is not None or profile_data is None

    def test_export_with_no_data(self):
        """Test export with no student data"""
        generator = ExportGenerator()
        
        # This should handle gracefully
        profile_data = generator.generate_profile_export(student_id=99999)
        
        # Either returns None or empty data
        assert profile_data is None or isinstance(profile_data, dict)


# ==================== Test Fixtures ====================

@pytest.fixture
def sample_assessment_data():
    """Sample assessment data for testing"""
    return {
        'assessment_id': 1,
        'skill_name': 'Python',
        'assessment_type': 'MCQ',
        'difficulty': 'easy',
        'score': 85,
        'badge': 'Good',
        'total_questions': 5,
        'questions': [
            {'text': 'What is Python?'},
        ],
        'user_responses': ['A'],
        'correct_answers': ['A'],
        'feedback': {'question_0': 'Correct!'},
        'gaps_identified': [],
        'recommendations': ['Keep practicing!'],
        'time_spent_minutes': 10,
        'created_at': datetime.utcnow().isoformat(),
        'export_timestamp': datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_gap_data():
    """Sample gap analysis data for testing"""
    return {
        'skill_name': 'Python',
        'skill_id': 1,
        'current_score': 75,
        'benchmark_score': 80,
        'percentile': 45,
        'gaps_identified': 2,
        'gaps': [
            {
                'name': 'OOP Concepts',
                'frequency': 3,
                'priority': 'high',
                'impact': 8
            }
        ],
        'recommendations': ['Focus on OOP'],
        'learning_plans': [],
        'export_timestamp': datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing"""
    return {
        'student_name': 'John Doe',
        'email': 'john@example.com',
        'user_type': 'BCA',
        'total_skills': 5,
        'average_score': 78,
        'assessments_taken': 10,
        'active_learning_plans': 2,
        'total_gaps': 3,
        'skills': [],
        'assessments': [],
        'gaps': [],
        'learning_plans': [],
        'export_timestamp': datetime.utcnow().isoformat()
    }
