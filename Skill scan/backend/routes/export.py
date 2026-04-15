"""
Export Routes

API endpoints for exporting assessments, gaps, and profiles in PDF/CSV/ZIP formats.

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import os
from functools import wraps
from datetime import datetime

from flask import Blueprint, request, jsonify, send_file
from werkzeug.exceptions import BadRequest

from backend.utils.auth import token_required, get_current_user
from backend.utils.export_generator import ExportGenerator
from backend.utils.pdf_generator import PDFReportGenerator
from backend.utils.csv_generator import CSVExporter
from backend.models import Student, Assessment, AssessmentResponse, SkillScore, LearningPlan

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__, url_prefix='/export')

# Initialize exporters
export_gen = ExportGenerator()
pdf_gen = PDFReportGenerator()
csv_exp = CSVExporter()


# ==================== Helper Functions ====================

def _validate_student(student_id: int) -> tuple:
    """Validate student exists and user has access"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return None, {'error': 'Student not found'}, 404
        
        current_user_id = get_current_user()
        if current_user_id != student_id:
            return None, {'error': 'Unauthorized access'}, 403
        
        return student, None, None
    except Exception as e:
        logger.error(f"Error validating student: {str(e)}")
        return None, {'error': 'Validation error'}, 500


def _get_safe_filename(filename: str) -> str:
    """Generate safe filename with timestamp"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    return f"{timestamp}_{filename}"


# ==================== Assessment Export Endpoints ====================

@export_bp.route('/assessment-pdf', methods=['POST'])
@token_required
def export_assessment_pdf():
    """
    Export single assessment as PDF
    
    POST /export/assessment-pdf
    {
        "assessment_id": 123,  (required)
        "student_id": 1       (required)
    }
    
    Returns: PDF file download
    """
    try:
        logger.info("Export assessment PDF requested")
        
        data = request.get_json()
        student_id = data.get('student_id')
        assessment_id = data.get('assessment_id')
        
        if not student_id or not assessment_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate student
        student, error_resp, status_code = _validate_student(student_id)
        if error_resp:
            return jsonify(error_resp), status_code
        
        # Verify assessment belongs to student
        assessment_response = AssessmentResponse.query.filter_by(
            id=assessment_id,
            student_id=student_id
        ).first()
        
        if not assessment_response:
            return jsonify({'error': 'Assessment not found'}), 404
        
        # Generate export data
        assessment_data = export_gen.generate_assessment_export(
            student_id,
            assessment_id
        )
        
        if not assessment_data:
            return jsonify({'error': 'Failed to generate assessment data'}), 500
        
        # Generate PDF
        pdf_bytes = pdf_gen.generate_assessment_pdf(assessment_data)
        
        if not pdf_bytes:
            return jsonify({'error': 'Failed to generate PDF'}), 500
        
        filename = _get_safe_filename('assessment_report.pdf')
        
        logger.info(f"Assessment PDF exported successfully: {filename}")
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting assessment PDF: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


@export_bp.route('/assessments-csv', methods=['POST'])
@token_required
def export_assessments_csv():
    """
    Export all assessments as CSV
    
    POST /export/assessments-csv
    {
        "student_id": 1,      (required)
        "skill_id": 5         (optional)
    }
    
    Returns: CSV file download
    """
    try:
        logger.info("Export assessments CSV requested")
        
        data = request.get_json()
        student_id = data.get('student_id')
        skill_id = data.get('skill_id')
        
        if not student_id:
            return jsonify({'error': 'Missing student_id'}), 400
        
        # Validate student
        student, error_resp, status_code = _validate_student(student_id)
        if error_resp:
            return jsonify(error_resp), status_code
        
        # Get assessments
        query = AssessmentResponse.query.filter_by(student_id=student_id)
        if skill_id:
            query = query.join(Assessment).filter(Assessment.skill_id == skill_id)
        
        assessments = query.all()
        
        if not assessments:
            return jsonify({'error': 'No assessments found'}), 404
        
        # Generate export data
        assessments_data = []
        for assessment in assessments:
            data = export_gen.generate_assessment_export(student_id, assessment.id)
            if data:
                assessments_data.append(data)
        
        # Generate CSV
        csv_data = CSVExporter.export_assessments_csv(assessments_data)
        
        if not csv_data:
            return jsonify({'error': 'Failed to generate CSV'}), 500
        
        filename = _get_safe_filename('assessments.csv')
        
        logger.info(f"Assessments CSV exported: {filename}")
        
        return send_file(
            io.BytesIO(csv_data.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting assessments CSV: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


# ==================== Gap Analysis Export Endpoints ====================

@export_bp.route('/gap-report-pdf', methods=['POST'])
@token_required
def export_gap_report_pdf():
    """
    Export gap analysis report as PDF
    
    POST /export/gap-report-pdf
    {
        "student_id": 1,      (required)
        "skill_id": 5         (required)
    }
    
    Returns: PDF file download
    """
    try:
        logger.info("Export gap report PDF requested")
        
        data = request.get_json()
        student_id = data.get('student_id')
        skill_id = data.get('skill_id')
        
        if not student_id or not skill_id:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate student
        student, error_resp, status_code = _validate_student(student_id)
        if error_resp:
            return jsonify(error_resp), status_code
        
        # Generate export data
        gap_data = export_gen.generate_gap_export(student_id, skill_id)
        
        if not gap_data:
            return jsonify({'error': 'Failed to generate gap data'}), 500
        
        # Generate PDF
        pdf_bytes = pdf_gen.generate_gap_report_pdf(gap_data)
        
        if not pdf_bytes:
            return jsonify({'error': 'Failed to generate PDF'}), 500
        
        filename = _get_safe_filename('gap_report.pdf')
        
        logger.info(f"Gap report PDF exported: {filename}")
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting gap report PDF: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


# ==================== Profile Export Endpoints ====================

@export_bp.route('/profile-pdf', methods=['POST'])
@token_required
def export_profile_pdf():
    """
    Export complete profile as PDF
    
    POST /export/profile-pdf
    {
        "student_id": 1       (required)
    }
    
    Returns: PDF file download
    """
    try:
        logger.info("Export profile PDF requested")
        
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Missing student_id'}), 400
        
        # Validate student
        student, error_resp, status_code = _validate_student(student_id)
        if error_resp:
            return jsonify(error_resp), status_code
        
        # Generate export data
        profile_data = export_gen.generate_profile_export(student_id)
        
        if not profile_data:
            return jsonify({'error': 'Failed to generate profile data'}), 500
        
        # Generate PDF
        pdf_bytes = pdf_gen.generate_profile_pdf(profile_data)
        
        if not pdf_bytes:
            return jsonify({'error': 'Failed to generate PDF'}), 500
        
        filename = _get_safe_filename('profile_complete.pdf')
        
        logger.info(f"Profile PDF exported: {filename}")
        
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting profile PDF: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


@export_bp.route('/skills-csv', methods=['POST'])
@token_required
def export_skills_csv():
    """
    Export all skills as CSV
    
    POST /export/skills-csv
    {
        "student_id": 1       (required)
    }
    
    Returns: CSV file download
    """
    try:
        logger.info("Export skills CSV requested")
        
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'error': 'Missing student_id'}), 400
        
        # Validate student
        student, error_resp, status_code = _validate_student(student_id)
        if error_resp:
            return jsonify(error_resp), status_code
        
        # Generate export data
        csv_data = export_gen.generate_skills_csv(student_id)
        
        if not csv_data:
            return jsonify({'error': 'Failed to generate CSV'}), 500
        
        filename = _get_safe_filename('skills.csv')
        
        logger.info(f"Skills CSV exported: {filename}")
        
        return send_file(
            io.BytesIO(csv_data.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting skills CSV: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


# ==================== Bulk Export Endpoints ====================

@export_bp.route('/all', methods=['POST'])
@token_required
def export_all():
    """
    Export all data as ZIP
    
    POST /export/all
    {
        "student_id": 1,       (required)
        "format": "zip"        (pdf/csv/zip)
    }
    
    Returns: ZIP file download with all exports
    """
    try:
        logger.info("Export all data requested")
        
        data = request.get_json()
        student_id = data.get('student_id')
        export_format = data.get('format', 'zip')
        
        if not student_id:
            return jsonify({'error': 'Missing student_id'}), 400
        
        # Validate student
        student, error_resp, status_code = _validate_student(student_id)
        if error_resp:
            return jsonify(error_resp), status_code
        
        # Generate profile data
        profile_data = export_gen.generate_profile_export(student_id)
        if not profile_data:
            return jsonify({'error': 'Failed to generate data'}), 500
        
        pdf_files = {}
        csv_files = {}
        
        # Generate profile PDF
        profile_pdf = pdf_gen.generate_profile_pdf(profile_data)
        if profile_pdf:
            pdf_files['profile_complete.pdf'] = profile_pdf
        
        # Generate skills CSV
        skills_csv = export_gen.generate_skills_csv(student_id)
        if skills_csv:
            csv_files['skills.csv'] = skills_csv
        
        # Generate assessments CSV
        assessments_csv = export_gen.generate_all_assessments_csv(student_id)
        if assessments_csv:
            csv_files['assessments.csv'] = assessments_csv
        
        # Create ZIP
        zip_bytes = export_gen.generate_zip_export(student_id, pdf_files, csv_files)
        
        if not zip_bytes:
            return jsonify({'error': 'Failed to create ZIP'}), 500
        
        filename = _get_safe_filename('skillscan_export_all.zip')
        
        logger.info(f"All data exported as ZIP: {filename}")
        
        return send_file(
            io.BytesIO(zip_bytes),
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting all data: {str(e)}")
        return jsonify({'error': 'Export failed'}), 500


# ==================== Export Status Endpoints ====================

@export_bp.route('/status', methods=['GET'])
@token_required
def export_status():
    """
    Get export status and available options
    
    GET /export/status
    
    Returns: Available export options
    """
    try:
        logger.info("Export status requested")
        
        status = {
            'exports_available': True,
            'formats': ['pdf', 'csv', 'zip'],
            'export_types': [
                'assessment',
                'gap_report',
                'profile',
                'skills',
                'assessments',
                'all'
            ],
            'frequency_limit': 'unlimited',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting export status: {str(e)}")
        return jsonify({'error': 'Status check failed'}), 500


# ==================== Error Handlers ====================

@export_bp.errorhandler(BadRequest)
def handle_bad_request(e):
    """Handle bad request errors"""
    logger.error(f"Bad request: {str(e)}")
    return jsonify({'error': 'Bad request'}), 400


@export_bp.errorhandler(404)
def handle_not_found(e):
    """Handle not found errors"""
    logger.error(f"Not found: {str(e)}")
    return jsonify({'error': 'Resource not found'}), 404


@export_bp.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500


# ==================== Blueprint Registration ====================

def register_export_routes(app):
    """Register export routes with Flask app"""
    app.register_blueprint(export_bp)
    logger.info("Export routes registered")
