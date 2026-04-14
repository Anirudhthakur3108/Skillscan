"""
Skills management routes blueprint.
Handles skill catalog operations, skill verification, and resume parsing.
"""

import os
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy import and_
from datetime import datetime
from functools import wraps

from models import db, Student, SkillsTaxonomy, StudentSkill
from utils.resume_parser import ResumeParser
from utils.auth import token_required

logger = logging.getLogger(__name__)

skills_bp = Blueprint('skills', __name__, url_prefix='/students')

# Initialize resume parser with default skills
SKILL_MATCHER_INSTANCE = None


def get_skill_list():
    """Get list of all skills from database"""
    try:
        skills = db.session.query(SkillsTaxonomy.name).all()
        return [skill[0] for skill in skills]
    except Exception as e:
        logger.error(f"Error fetching skills from database: {str(e)}")
        return ResumeParser._get_default_skills()


def get_parser():
    """Get or create ResumeParser instance"""
    global SKILL_MATCHER_INSTANCE
    if SKILL_MATCHER_INSTANCE is None:
        skill_list = get_skill_list()
        SKILL_MATCHER_INSTANCE = ResumeParser(skill_list)
    return SKILL_MATCHER_INSTANCE


# ============================================================================
# RESUME UPLOAD & PARSING ENDPOINT
# ============================================================================


@skills_bp.route('/<int:student_id>/skills/upload', methods=['POST'])
@token_required
def upload_resume(current_user, student_id):
    """
    Upload and parse resume to extract skills

    Endpoint: POST /students/<student_id>/skills/upload
    
    Parameters:
        student_id: Student ID from URL
        file: PDF file (in request.files['file'])
    
    Returns:
        {
            "status": "success",
            "extracted_skills": [
                {
                    "skill_name": "Python",
                    "confidence": 1.0,
                    "match_type": "exact"
                }
            ],
            "stats": {
                "total_matches": int,
                "exact_matches": int,
                "fuzzy_matches": int,
                "average_confidence": float
            }
        }
    
    Error Responses:
        400: Invalid request (no file, wrong format)
        413: File too large (>5MB)
        403: Unauthorized (not your profile)
        404: Student not found
        500: Server error (PDF parsing failed)
    """
    try:
        # Validate authorization
        if current_user.get('user_id') != student_id:
            logger.warning(
                f"Unauthorized resume upload attempt: user {current_user.get('user_id')} "
                f"tried to upload for student {student_id}"
            )
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': 'You can only upload resume for your own profile'
            }), 403

        # Validate student exists
        student = db.session.query(Student).filter_by(id=student_id).first()
        if not student:
            logger.warning(f"Resume upload attempt for non-existent student: {student_id}")
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': 'Student not found'
            }), 404

        # Check if file in request
        if 'file' not in request.files:
            logger.warning(f"Resume upload missing file for student {student_id}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'No file provided'
            }), 400

        file = request.files['file']

        # Validate filename
        if file.filename == '':
            logger.warning(f"Resume upload empty filename for student {student_id}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'No file selected'
            }), 400

        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(
                f"Invalid file type for student {student_id}: {file.filename}"
            )
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Only PDF files are accepted'
            }), 400

        # Check file size (before parsing)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > 5 * 1024 * 1024:  # 5 MB
            logger.warning(f"File too large for student {student_id}: {file_size} bytes")
            return jsonify({
                'status': 'error',
                'code': 413,
                'message': f"File too large (max 5MB), received {file_size / 1024 / 1024:.1f}MB"
            }), 413

        # Parse resume
        try:
            parser = get_parser()
            result = parser.parse_resume(file)

            logger.info(
                f"Resume parsed successfully for student {student_id}: "
                f"{result['stats']['total_matches']} skills extracted"
            )

            return jsonify({
                'status': 'success',
                'code': 200,
                'extracted_skills': result.get('extracted_skills', []),
                'stats': result.get('stats', {}),
                'message': f"Successfully extracted {result['stats']['total_matches']} skills from resume"
            }), 200

        except ValueError as ve:
            logger.error(f"PDF parsing error for student {student_id}: {str(ve)}")
            error_msg = str(ve)

            if "password" in error_msg.lower():
                return jsonify({
                    'status': 'error',
                    'code': 400,
                    'message': 'PDF is password protected. Please provide unencrypted PDF.'
                }), 400
            elif "too large" in error_msg.lower():
                return jsonify({
                    'status': 'error',
                    'code': 413,
                    'message': error_msg
                }), 413
            else:
                return jsonify({
                    'status': 'error',
                    'code': 400,
                    'message': 'Failed to parse PDF. Please ensure it\'s a valid PDF file.'
                }), 400

    except Exception as e:
        logger.error(f"Unexpected error in resume upload for student {student_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error during resume processing'
        }), 500


# ============================================================================
# MANUAL SKILL ADDITION ENDPOINT
# ============================================================================


@skills_bp.route('/<int:student_id>/skills/add-manual', methods=['POST'])
@token_required
def add_manual_skill(current_user, student_id):
    """
    Manually add a skill to student profile

    Endpoint: POST /students/<student_id>/skills/add-manual
    
    Body:
    {
        "skill_name": "Python",
        "proficiency_claimed": 7
    }
    
    Returns:
        {
            "status": "success",
            "skill_id": int,
            "skill_name": str,
            "proficiency_claimed": int,
            "added_at": datetime
        }
    """
    try:
        # Validate authorization
        if current_user.get('user_id') != student_id:
            logger.warning(
                f"Unauthorized skill addition attempt: user {current_user.get('user_id')} "
                f"tried to add for student {student_id}"
            )
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': 'You can only add skills to your own profile'
            }), 403

        # Validate student exists
        student = db.session.query(Student).filter_by(id=student_id).first()
        if not student:
            logger.warning(f"Skill addition attempt for non-existent student: {student_id}")
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': 'Student not found'
            }), 404

        data = request.get_json()

        # Validate required fields
        if not data or 'skill_name' not in data or 'proficiency_claimed' not in data:
            logger.warning(f"Missing required fields for student {student_id}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Missing required fields: skill_name, proficiency_claimed'
            }), 400

        skill_name = data.get('skill_name', '').strip()
        proficiency = data.get('proficiency_claimed')

        # Validate skill name
        if not skill_name or len(skill_name) < 2:
            logger.warning(f"Invalid skill name for student {student_id}: {skill_name}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Skill name must be at least 2 characters'
            }), 400

        # Validate proficiency
        try:
            proficiency = int(proficiency)
            if proficiency < 1 or proficiency > 10:
                raise ValueError("Out of range")
        except (TypeError, ValueError):
            logger.warning(f"Invalid proficiency for student {student_id}: {proficiency}")
            return jsonify({
                'status': 'error',
                'code': 400,
                'message': 'Proficiency must be an integer between 1 and 10'
            }), 400

        # Find skill in taxonomy (case-insensitive)
        skill = db.session.query(SkillsTaxonomy).filter(
            SkillsTaxonomy.name.ilike(skill_name)
        ).first()

        if not skill:
            logger.warning(f"Skill '{skill_name}' not found in taxonomy for student {student_id}")
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': f'Skill "{skill_name}" not found in taxonomy. Please select from available skills or contact support.'
            }), 404

        # Check if student already has this skill
        existing_skill = db.session.query(StudentSkill).filter(
            and_(
                StudentSkill.student_id == student_id,
                StudentSkill.skill_id == skill.id
            )
        ).first()

        if existing_skill:
            # Update proficiency
            existing_skill.proficiency_claimed = proficiency
            existing_skill.updated_at = datetime.utcnow()
            logger.info(f"Updated skill '{skill_name}' proficiency for student {student_id}")
        else:
            # Add new skill
            student_skill = StudentSkill(
                student_id=student_id,
                skill_id=skill.id,
                proficiency_claimed=proficiency,
                source='manual'
            )
            db.session.add(student_skill)
            logger.info(f"Added manual skill '{skill_name}' to student {student_id}")

        db.session.commit()

        return jsonify({
            'status': 'success',
            'code': 201,
            'message': f'Skill "{skill_name}" added successfully',
            'skill_id': skill.id,
            'skill_name': skill.name,
            'proficiency_claimed': proficiency
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding manual skill for student {student_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500


# ============================================================================
# GET STUDENT SKILLS ENDPOINT
# ============================================================================


@skills_bp.route('/<int:student_id>/skills', methods=['GET'])
@token_required
def get_student_skills(current_user, student_id):
    """
    Get all skills for a student

    Endpoint: GET /students/<student_id>/skills
    
    Returns:
        {
            "status": "success",
            "skills": [
                {
                    "id": int,
                    "name": str,
                    "proficiency_claimed": int,
                    "source": str,
                    "category": str
                }
            ]
        }
    """
    try:
        # Validate authorization
        if current_user.get('user_id') != student_id:
            logger.warning(
                f"Unauthorized skills retrieval attempt: user {current_user.get('user_id')} "
                f"tried to access skills for student {student_id}"
            )
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': 'You can only view skills from your own profile'
            }), 403

        # Validate student exists
        student = db.session.query(Student).filter_by(id=student_id).first()
        if not student:
            logger.warning(f"Skills retrieval attempt for non-existent student: {student_id}")
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': 'Student not found'
            }), 404

        # Get skills
        skills = db.session.query(
            StudentSkill.id,
            SkillsTaxonomy.name,
            StudentSkill.proficiency_claimed,
            StudentSkill.source,
            SkillsTaxonomy.category
        ).join(
            SkillsTaxonomy, StudentSkill.skill_id == SkillsTaxonomy.id
        ).filter(
            StudentSkill.student_id == student_id
        ).all()

        skills_data = [
            {
                'id': skill[0],
                'name': skill[1],
                'proficiency_claimed': skill[2],
                'source': skill[3],
                'category': skill[4]
            }
            for skill in skills
        ]

        logger.info(f"Retrieved {len(skills_data)} skills for student {student_id}")

        return jsonify({
            'status': 'success',
            'code': 200,
            'skills': skills_data
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving skills for student {student_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500


# ============================================================================
# DELETE SKILL ENDPOINT
# ============================================================================


@skills_bp.route('/<int:student_id>/skills/<int:skill_id>', methods=['DELETE'])
@token_required
def delete_skill(current_user, student_id, skill_id):
    """
    Remove a skill from student profile

    Endpoint: DELETE /students/<student_id>/skills/<skill_id>
    
    Returns:
        {
            "status": "success",
            "message": "Skill removed successfully"
        }
    """
    try:
        # Validate authorization
        if current_user.get('user_id') != student_id:
            logger.warning(
                f"Unauthorized skill deletion attempt: user {current_user.get('user_id')} "
                f"tried to delete for student {student_id}"
            )
            return jsonify({
                'status': 'error',
                'code': 403,
                'message': 'You can only remove skills from your own profile'
            }), 403

        # Validate student exists
        student = db.session.query(Student).filter_by(id=student_id).first()
        if not student:
            logger.warning(f"Skill deletion attempt for non-existent student: {student_id}")
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': 'Student not found'
            }), 404

        # Find and delete skill
        student_skill = db.session.query(StudentSkill).filter(
            and_(
                StudentSkill.id == skill_id,
                StudentSkill.student_id == student_id
            )
        ).first()

        if not student_skill:
            logger.warning(f"Skill {skill_id} not found for student {student_id}")
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': 'Skill not found'
            }), 404

        # Delete
        db.session.delete(student_skill)
        db.session.commit()

        logger.info(f"Deleted skill {skill_id} for student {student_id}")

        return jsonify({
            'status': 'success',
            'code': 200,
            'message': 'Skill removed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting skill {skill_id} for student {student_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500


# ============================================================================
# GET AVAILABLE SKILLS (TAXONOMY)
# ============================================================================


@skills_bp.route('/skills/taxonomy', methods=['GET'])
def get_skills_taxonomy():
    """
    Get all available skills from taxonomy

    Endpoint: GET /students/skills/taxonomy
    
    Returns:
        {
            "status": "success",
            "skills": [
                {
                    "id": int,
                    "name": str,
                    "category": str,
                    "description": str,
                    "industry_benchmark": int
                }
            ]
        }
    """
    try:
        skills = db.session.query(
            SkillsTaxonomy.id,
            SkillsTaxonomy.name,
            SkillsTaxonomy.category,
            SkillsTaxonomy.description,
            SkillsTaxonomy.industry_benchmark
        ).all()

        skills_data = [
            {
                'id': skill[0],
                'name': skill[1],
                'category': skill[2],
                'description': skill[3],
                'industry_benchmark': skill[4]
            }
            for skill in skills
        ]

        logger.info(f"Retrieved {len(skills_data)} skills from taxonomy")

        return jsonify({
            'status': 'success',
            'code': 200,
            'skills': skills_data
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving skills taxonomy: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500
