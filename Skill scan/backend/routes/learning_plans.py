"""
Learning Plans API Routes

Handles generation, retrieval, and progress tracking of learning plans.

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import json
from typing import Dict, Any, Tuple, Optional
from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

from backend.utils.auth import token_required, decode_jwt_token
from backend.utils.learning_plan_generator import LearningPlanGenerator
from backend.models import LearningPlan, Student, Skills, Assessment, AssessmentResponse
from backend.database import db

logger = logging.getLogger(__name__)

# Create blueprint
learning_plans_bp = Blueprint('learning_plans', __name__, url_prefix='/learning-plans')
plan_generator = LearningPlanGenerator()


def get_current_user(token: Optional[str] = None) -> Optional[int]:
    """
    Extract user ID from JWT token
    
    Args:
        token: JWT token from request header
        
    Returns:
        User ID if valid, None otherwise
    """
    if not token:
        return None
    decoded = decode_jwt_token(token)
    return decoded.get('user_id') if decoded else None


def extract_token_from_request() -> Optional[str]:
    """Extract JWT token from Authorization header"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


@learning_plans_bp.route('/generate', methods=['POST'])
@token_required
def generate_learning_plan():
    """
    Generate a personalized learning plan
    
    Request JSON:
    {
        "skill_id": 1,
        "gaps": ["Gap 1", "Gap 2"],
        "assessment_score": 72,
        "duration_weeks": 4  # Optional, uses recommendation if not provided
    }
    
    Returns:
        {
            "id": 1,
            "skill_id": 1,
            "skill_name": "Python",
            "duration_weeks": 4,
            "recommended_duration": 4,
            "recommendation_reason": "...",
            "milestones": [...],
            "resources": [...],
            "created_at": "..."
        }
    """
    try:
        token = extract_token_from_request()
        student_id = get_current_user(token)
        
        if not student_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data or 'skill_id' not in data:
            return jsonify({'error': 'Missing skill_id'}), 400
        
        if 'gaps' not in data or not isinstance(data['gaps'], list):
            return jsonify({'error': 'Missing or invalid gaps'}), 400
        
        if 'assessment_score' not in data:
            return jsonify({'error': 'Missing assessment_score'}), 400
        
        skill_id = data['skill_id']
        gaps = data['gaps']
        assessment_score = int(data['assessment_score'])
        user_duration_weeks = data.get('duration_weeks')
        
        # Validate skill exists
        skill = Skills.query.get(skill_id)
        if not skill:
            return jsonify({'error': f'Skill {skill_id} not found'}), 404
        
        # Validate score range
        if not (0 <= assessment_score <= 100):
            return jsonify({'error': 'assessment_score must be between 0 and 100'}), 400
        
        # Validate duration if provided
        if user_duration_weeks and user_duration_weeks not in [2, 3, 4, 6]:
            return jsonify({'error': 'duration_weeks must be 2, 3, 4, or 6'}), 400
        
        logger.info(f"Generating learning plan for student {student_id}, skill {skill_id}")
        
        # Generate plan
        plan_data = plan_generator.generate_learning_plan(
            student_id=student_id,
            skill_id=skill_id,
            gaps=gaps,
            assessment_score=assessment_score,
            user_duration_weeks=user_duration_weeks
        )
        
        if not plan_data:
            return jsonify({'error': 'Failed to generate learning plan'}), 500
        
        # Save to database
        saved_plan = plan_generator.save_learning_plan(student_id, plan_data)
        
        if not saved_plan:
            return jsonify({'error': 'Failed to save learning plan'}), 500
        
        logger.info(f"Learning plan generated and saved: {saved_plan.get('id')}")
        
        return jsonify({
            'status': 'success',
            'message': 'Learning plan generated successfully',
            'data': saved_plan
        }), 201
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error generating learning plan: {str(e)}")
        return jsonify({'error': str(e)}), 500


@learning_plans_bp.route('/<int:plan_id>', methods=['GET'])
@token_required
def get_learning_plan(plan_id: int):
    """
    Get learning plan details
    
    Returns:
        {
            "id": 1,
            "skill_id": 1,
            "skill_name": "Python",
            "duration_weeks": 4,
            "progress": 25,
            "milestones": [...],
            "resources": [...],
            "created_at": "..."
        }
    """
    try:
        token = extract_token_from_request()
        student_id = get_current_user(token)
        
        if not student_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        plan = LearningPlan.query.filter_by(id=plan_id, student_id=student_id).first()
        
        if not plan:
            return jsonify({'error': f'Learning plan {plan_id} not found'}), 404
        
        skill = Skills.query.get(plan.skill_id)
        
        response_data = {
            'id': plan.id,
            'skill_id': plan.skill_id,
            'skill_name': skill.skill_name if skill else 'Unknown',
            'duration_weeks': plan.duration_weeks,
            'recommended_duration': plan.recommended_duration,
            'recommendation_reason': plan.recommendation_reason,
            'progress': plan.progress,
            'gaps_addressed': json.loads(plan.gaps_addressed) if isinstance(plan.gaps_addressed, str) else plan.gaps_addressed,
            'milestones': json.loads(plan.milestones) if isinstance(plan.milestones, str) else plan.milestones,
            'resources': json.loads(plan.resources) if isinstance(plan.resources, str) else plan.resources,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'start_date': plan.start_date.isoformat() if plan.start_date else None,
            'end_date': plan.end_date.isoformat() if plan.end_date else None,
            'status': plan.status
        }
        
        logger.info(f"Retrieved learning plan {plan_id}")
        
        return jsonify({
            'status': 'success',
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving learning plan: {str(e)}")
        return jsonify({'error': str(e)}), 500


@learning_plans_bp.route('/<int:plan_id>/progress', methods=['PUT'])
@token_required
def update_learning_plan_progress(plan_id: int):
    """
    Update learning plan progress
    
    Request JSON:
    {
        "completed_milestones": 2
    }
    
    Returns:
        {
            "plan_id": 1,
            "progress": 50,
            "message": "Progress updated successfully"
        }
    """
    try:
        token = extract_token_from_request()
        student_id = get_current_user(token)
        
        if not student_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        if not data or 'completed_milestones' not in data:
            return jsonify({'error': 'Missing completed_milestones'}), 400
        
        # Verify ownership
        plan = LearningPlan.query.filter_by(id=plan_id, student_id=student_id).first()
        if not plan:
            return jsonify({'error': f'Learning plan {plan_id} not found'}), 404
        
        completed = int(data['completed_milestones'])
        progress = plan_generator.update_plan_progress(plan_id, completed)
        
        if progress is None:
            return jsonify({'error': 'Failed to update progress'}), 500
        
        logger.info(f"Updated plan {plan_id} progress to {progress}%")
        
        return jsonify({
            'status': 'success',
            'message': 'Progress updated successfully',
            'plan_id': plan_id,
            'progress': progress
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Invalid input: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Error updating progress: {str(e)}")
        return jsonify({'error': str(e)}), 500


@learning_plans_bp.route('/active', methods=['GET'])
@token_required
def get_active_learning_plans():
    """
    Get all active learning plans for user
    
    Returns:
        {
            "count": 2,
            "plans": [
                {
                    "id": 1,
                    "skill_id": 1,
                    "skill_name": "Python",
                    "duration_weeks": 4,
                    "progress": 25,
                    "created_at": "...",
                    "end_date": "..."
                }
            ]
        }
    """
    try:
        token = extract_token_from_request()
        student_id = get_current_user(token)
        
        if not student_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        plans = plan_generator.get_active_plans(student_id)
        
        logger.info(f"Retrieved {len(plans)} active plans for student {student_id}")
        
        return jsonify({
            'status': 'success',
            'count': len(plans),
            'plans': plans
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving active plans: {str(e)}")
        return jsonify({'error': str(e)}), 500


@learning_plans_bp.route('/<int:plan_id>/complete', methods=['PUT'])
@token_required
def mark_plan_complete(plan_id: int):
    """
    Mark a learning plan as completed
    
    Returns:
        {
            "plan_id": 1,
            "status": "completed",
            "message": "Learning plan marked as complete"
        }
    """
    try:
        token = extract_token_from_request()
        student_id = get_current_user(token)
        
        if not student_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        plan = LearningPlan.query.filter_by(id=plan_id, student_id=student_id).first()
        
        if not plan:
            return jsonify({'error': f'Learning plan {plan_id} not found'}), 404
        
        plan.status = 'completed'
        plan.progress = 100
        
        db.session.commit()
        
        logger.info(f"Marked plan {plan_id} as completed")
        
        return jsonify({
            'status': 'success',
            'message': 'Learning plan marked as complete',
            'plan_id': plan_id,
            'plan_status': plan.status
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error marking plan complete: {str(e)}")
        return jsonify({'error': str(e)}), 500
