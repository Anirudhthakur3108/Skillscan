"""
SkillScan MVP - Assessment Routes
Handles assessment generation, submission, and progress tracking
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from functools import wraps

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.database import get_db
from backend.models import (
    Assessment, AssessmentResponse, SkillScore, SkillsTaxonomy,
    Student, StudentSkill
)
from backend.utils.auth import token_required, decode_jwt_token
from backend.utils.model_client import GeminiClient

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint
assessments_bp = Blueprint('assessments', __name__, url_prefix='/assessments')


def _get_config(key: str, default: Any = None) -> Any:
    """Get configuration value from current app config"""
    try:
        return current_app.config.get(key, default)
    except RuntimeError:
        # Outside app context, use defaults
        return default


def _get_assessment_config() -> Dict[str, Dict[str, int]]:
    """Get assessment configuration"""
    return _get_config('ASSESSMENT_CONFIG', {
        'mcq': {'duration': 360, 'questions': 5},
        'coding': {'duration': 3600, 'questions': 2},
        'case_study': {'duration': 1800, 'questions': 1}
    })


def _get_passing_score() -> int:
    """Get passing score threshold"""
    return _get_config('ASSESSMENT_PASSING_SCORE', 70)


def _get_unlock_threshold() -> int:
    """Get unlock threshold"""
    return _get_config('ASSESSMENT_UNLOCK_THRESHOLD', 70)


def _get_badge_mapping() -> Dict[str, Tuple[int, int]]:
    """Get badge score mapping"""
    return _get_config('ASSESSMENT_BADGE_MAPPING', {
        'excellent': (90, 100),
        'good': (80, 89),
        'fair': (70, 79),
        'needs_work': (0, 69)
    })


def _get_difficulty_levels() -> List[str]:
    """Get allowed difficulty levels"""
    return _get_config('ASSESSMENT_DIFFICULTIES', ['easy', 'medium', 'hard'])


def _get_assessment_types() -> List[str]:
    """Get allowed assessment types"""
    return _get_config('ASSESSMENT_TYPES', ['mcq', 'coding', 'case_study'])


def get_current_user(token: Optional[str]) -> Optional[int]:
    """
    Extract user_id from JWT token
    
    Args:
        token: JWT token from request
        
    Returns:
        User ID if valid token, None otherwise
    """
    if not token:
        return None
    decoded = decode_jwt_token(token)
    return decoded.get('user_id') if decoded else None


def get_score_badge(score: int) -> str:
    """
    Determine badge based on score
    
    Args:
        score: Assessment score (0-100)
        
    Returns:
        Badge name (excellent, good, fair, needs_work)
    """
    badge_mapping = _get_badge_mapping()
    for badge, (min_score, max_score) in badge_mapping.items():
        if min_score <= score <= max_score:
            return badge
    return 'needs_work'


def validate_difficulty(difficulty: str) -> bool:
    """Validate difficulty level"""
    return difficulty in _get_difficulty_levels()


def validate_assessment_type(assessment_type: str) -> bool:
    """Validate assessment type"""
    config = _get_assessment_config()
    return assessment_type in config


def check_difficulty_unlock(
    db: Session,
    student_id: int,
    skill_id: int,
    target_difficulty: str
) -> Tuple[bool, Optional[str]]:
    """
    Check if student can attempt target difficulty level
    
    Args:
        db: Database session
        student_id: Student ID
        skill_id: Skill ID
        target_difficulty: Target difficulty level
        
    Returns:
        Tuple of (is_unlocked, reason_if_locked)
    """
    if target_difficulty == 'easy':
        return True, None
    
    # Get previous difficulty requirement
    prev_difficulties = {
        'medium': 'easy',
        'hard': 'medium'
    }
    
    prev_difficulty = prev_difficulties.get(target_difficulty)
    if not prev_difficulty:
        return False, "Invalid difficulty level"
    
    # Check if student has completed previous difficulty with ≥70%
    best_score = (
        db.query(SkillScore)
        .join(Assessment)
        .filter(
            SkillScore.student_id == student_id,
            SkillScore.skill_id == skill_id,
            Assessment.difficulty_level == prev_difficulty
        )
        .order_by(SkillScore.score.desc())
        .first()
    )
    
    if not best_score or best_score.score < UNLOCK_THRESHOLD:
        return False, f"Must score ≥{UNLOCK_THRESHOLD}% in {prev_difficulty} before attempting {target_difficulty}"
    
    return True, None


@assessments_bp.route('/generate', methods=['POST'])
@token_required
def generate_assessment() -> Tuple[Dict[str, Any], int]:
    """
    Generate a new assessment for a skill at specified difficulty
    
    Request JSON:
    {
        "skill_id": int,
        "difficulty": "easy|medium|hard",
        "assessment_type": "mcq|coding|case_study"
    }
    
    Response:
    {
        "assessment_id": int,
        "skill_id": int,
        "assessment_type": str,
        "difficulty": str,
        "questions": [...],
        "timer_seconds": int,
        "message": "Assessment generated successfully"
    }
    """
    try:
        db = get_db()
        token = request.headers.get('Authorization', '').split(' ')[-1]
        student_id = get_current_user(token)
        
        if not student_id:
            logger.warning("Unauthorized assessment generation attempt")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body required'}), 400
        
        skill_id = data.get('skill_id')
        difficulty = data.get('difficulty', 'easy').lower()
        assessment_type = data.get('assessment_type', 'mcq').lower()
        
        # Validate inputs
        if not skill_id:
            return jsonify({'error': 'skill_id is required'}), 400
        
        if not validate_difficulty(difficulty):
            return jsonify({
                'error': f'Invalid difficulty. Must be one of: {", ".join(DIFFICULTY_LEVELS)}'
            }), 400
        
        if not validate_assessment_type(assessment_type):
            return jsonify({
                'error': f'Invalid assessment_type. Must be one of: {", ".join(ASSESSMENT_CONFIG.keys())}'
            }), 400
        
        # Verify skill exists
        skill = db.query(SkillsTaxonomy).filter(SkillsTaxonomy.id == skill_id).first()
        if not skill:
            logger.warning(f"Assessment generation attempted for non-existent skill_id: {skill_id}")
            return jsonify({'error': 'Skill not found'}), 404
        
        # Check difficulty unlock status
        is_unlocked, reason = check_difficulty_unlock(db, student_id, skill_id, difficulty)
        if not is_unlocked:
            logger.info(
                f"User {student_id} attempted locked difficulty: skill={skill_id}, "
                f"difficulty={difficulty}, reason={reason}"
            )
            return jsonify({'error': reason}), 403
        
        # Get student proficiency for this skill
        student_skill = (
            db.query(StudentSkill)
            .filter(
                StudentSkill.student_id == student_id,
                StudentSkill.skill_id == skill_id
            )
            .first()
        )
        proficiency = student_skill.proficiency_claimed if student_skill else 5
        
        # Generate assessment questions using GeminiClient
        logger.info(
            f"Generating assessment - student={student_id}, skill={skill_id}, "
            f"difficulty={difficulty}, type={assessment_type}"
        )
        
        try:
            gemini_client = GeminiClient()
            questions_data = gemini_client.generate_assessment(
                assessment_type=assessment_type,
                skill=skill.name,
                difficulty=difficulty,
                proficiency=proficiency
            )
        except Exception as e:
            logger.error(f"Gemini API error during assessment generation: {str(e)}")
            return jsonify({
                'error': 'Failed to generate assessment. Please try again.',
                'details': str(e)
            }), 503
        
        # Create assessment record
        assessment = Assessment(
            student_id=student_id,
            skill_id=skill_id,
            assessment_type=assessment_type,
            difficulty_level=difficulty,
            questions=questions_data,
            status='generated'
        )
        
        try:
            db.add(assessment)
            db.commit()
            assessment_id = assessment.id
            logger.info(f"Assessment created: id={assessment_id}, student={student_id}")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating assessment: {str(e)}")
            return jsonify({'error': 'Failed to save assessment'}), 500
        
        # Calculate timer duration
        timer_seconds = ASSESSMENT_CONFIG[assessment_type]['duration']
        
        return jsonify({
            'assessment_id': assessment_id,
            'skill_id': skill_id,
            'skill_name': skill.name,
            'assessment_type': assessment_type,
            'difficulty': difficulty,
            'questions': questions_data,
            'timer_seconds': timer_seconds,
            'message': 'Assessment generated successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Unexpected error in generate_assessment: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@assessments_bp.route('/<int:assessment_id>/submit', methods=['POST'])
@token_required
def submit_assessment(assessment_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Submit completed assessment and get scoring/feedback
    
    Request JSON:
    {
        "responses": [
            {"question_id": 1, "answer": "A"},
            {"question_id": 2, "answer": "B"},
            ...
        ],
        "time_taken_seconds": int (optional, for analytics)
    }
    
    Response:
    {
        "score": int (0-100),
        "badge": str (excellent|good|fair|needs_work),
        "passed": bool (score >= 70),
        "feedback": str,
        "gaps_identified": [
            {"area": "string", "recommendation": "string"},
            ...
        ],
        "unlocked_next_difficulty": bool,
        "message": "Assessment submitted and scored"
    }
    """
    try:
        db = get_db()
        token = request.headers.get('Authorization', '').split(' ')[-1]
        student_id = get_current_user(token)
        
        if not student_id:
            logger.warning("Unauthorized assessment submission attempt")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Verify assessment exists and belongs to user
        assessment = (
            db.query(Assessment)
            .filter(Assessment.id == assessment_id)
            .first()
        )
        
        if not assessment:
            logger.warning(f"Submission attempted for non-existent assessment: {assessment_id}")
            return jsonify({'error': 'Assessment not found'}), 404
        
        if assessment.student_id != student_id:
            logger.warning(
                f"Unauthorized submission attempt - user {student_id} attempted "
                f"assessment {assessment_id} belonging to {assessment.student_id}"
            )
            return jsonify({'error': 'Forbidden'}), 403
        
        # Validate request data
        data = request.get_json()
        if not data or 'responses' not in data:
            return jsonify({'error': 'responses array is required'}), 400
        
        responses = data.get('responses', [])
        if not isinstance(responses, list):
            return jsonify({'error': 'responses must be an array'}), 400
        
        if len(responses) == 0:
            return jsonify({'error': 'At least one response is required'}), 400
        
        # Get skill info for Gemini
        skill = (
            db.query(SkillsTaxonomy)
            .filter(SkillsTaxonomy.id == assessment.skill_id)
            .first()
        )
        
        # Score assessment using GeminiClient
        logger.info(
            f"Scoring assessment - assessment_id={assessment_id}, "
            f"student={student_id}, type={assessment.assessment_type}"
        )
        
        try:
            gemini_client = GeminiClient()
            scoring_result = gemini_client.score_assessment(
                assessment_data=assessment.questions,
                user_responses=responses,
                assessment_type=assessment.assessment_type,
                skill=skill.name,
                difficulty=assessment.difficulty_level,
                student_id=student_id,
                proficiency=5  # Could be fetched from StudentSkill
            )
        except Exception as e:
            logger.error(f"Gemini API error during assessment scoring: {str(e)}")
            return jsonify({
                'error': 'Failed to score assessment. Please try again.',
                'details': str(e)
            }), 503
        
        # Extract and validate scoring data
        score = scoring_result.get('score', 0)
        feedback = scoring_result.get('feedback', '')
        gaps = scoring_result.get('gaps_identified', [])
        confidence = scoring_result.get('confidence', 0.5)
        
        # Ensure score is in 0-100 range
        score = max(0, min(100, int(score)))
        
        # Create assessment response record
        response_record = AssessmentResponse(
            assessment_id=assessment_id,
            student_id=student_id,
            responses=responses
        )
        
        # Create skill score record
        skill_score = SkillScore(
            student_id=student_id,
            skill_id=assessment.skill_id,
            assessment_id=assessment_id,
            score=score // 10 if score > 0 else 1,  # Convert to 1-10 scale
            gaps_identified=gaps,
            reasoning=feedback,
            ai_confidence=min(1.0, max(0.0, confidence))
        )
        
        # Update assessment status
        assessment.status = 'completed'
        
        try:
            db.add(response_record)
            db.add(skill_score)
            db.commit()
            logger.info(
                f"Assessment scored - assessment_id={assessment_id}, "
                f"score={score}, passed={'yes' if score >= PASSING_SCORE else 'no'}"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error saving assessment response: {str(e)}")
            return jsonify({'error': 'Failed to save assessment response'}), 500
        
        # Check if next difficulty should be unlocked
        badge = get_score_badge(score)
        passed = score >= PASSING_SCORE
        unlocked_next = False
        next_difficulty = None
        
        if passed:
            next_difficulty_map = {
                'easy': 'medium',
                'medium': 'hard',
                'hard': None
            }
            next_difficulty = next_difficulty_map.get(assessment.difficulty_level)
            
            if next_difficulty:
                # Verify next difficulty was previously locked
                is_unlocked, _ = check_difficulty_unlock(
                    db, student_id, assessment.skill_id, next_difficulty
                )
                unlocked_next = not is_unlocked  # If it was locked, now it's unlocked
        
        logger.info(
            f"Assessment complete - student={student_id}, skill={assessment.skill_id}, "
            f"difficulty={assessment.difficulty_level}, score={score}, "
            f"badge={badge}, passed={passed}, unlocked_next={unlocked_next}"
        )
        
        return jsonify({
            'assessment_id': assessment_id,
            'score': score,
            'badge': badge,
            'passed': passed,
            'feedback': feedback,
            'gaps_identified': gaps,
            'unlocked_next_difficulty': unlocked_next,
            'next_difficulty': next_difficulty,
            'message': 'Assessment submitted and scored successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in submit_assessment: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@assessments_bp.route('/<int:skill_id>/progress', methods=['GET'])
@token_required
def get_progress(skill_id: int) -> Tuple[Dict[str, Any], int]:
    """
    Get student's progress on a specific skill across all difficulty levels
    
    Response:
    {
        "skill_id": int,
        "skill_name": str,
        "progress": {
            "easy": {
                "status": "completed|unlocked|locked",
                "best_score": int (0-100),
                "best_badge": str,
                "attempts": int,
                "last_attempt": "ISO datetime"
            },
            "medium": {...},
            "hard": {...}
        }
    }
    """
    try:
        db = get_db()
        token = request.headers.get('Authorization', '').split(' ')[-1]
        student_id = get_current_user(token)
        
        if not student_id:
            logger.warning("Unauthorized progress check attempt")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Verify skill exists
        skill = (
            db.query(SkillsTaxonomy)
            .filter(SkillsTaxonomy.id == skill_id)
            .first()
        )
        
        if not skill:
            logger.warning(f"Progress check for non-existent skill: {skill_id}")
            return jsonify({'error': 'Skill not found'}), 404
        
        # Get all assessments for this skill grouped by difficulty
        progress = {}
        
        for difficulty in DIFFICULTY_LEVELS:
            # Check unlock status
            is_unlocked, _ = check_difficulty_unlock(db, student_id, skill_id, difficulty)
            
            if not is_unlocked and difficulty != 'easy':
                status = 'locked'
                best_score = None
                best_badge = None
                attempts = 0
                last_attempt = None
            else:
                status = 'unlocked'
                
                # Get best score for this difficulty
                best_score_record = (
                    db.query(SkillScore)
                    .join(Assessment)
                    .filter(
                        SkillScore.student_id == student_id,
                        SkillScore.skill_id == skill_id,
                        Assessment.difficulty_level == difficulty
                    )
                    .order_by(SkillScore.score.desc())
                    .first()
                )
                
                if best_score_record:
                    status = 'completed'
                    best_score = best_score_record.score * 10  # Convert back to 0-100
                    best_badge = get_score_badge(best_score)
                    last_attempt = best_score_record.scored_at.isoformat()
                else:
                    best_score = None
                    best_badge = None
                    last_attempt = None
                
                # Count attempts
                attempts = (
                    db.query(Assessment)
                    .filter(
                        Assessment.student_id == student_id,
                        Assessment.skill_id == skill_id,
                        Assessment.difficulty_level == difficulty,
                        Assessment.status == 'completed'
                    )
                    .count()
                )
            
            progress[difficulty] = {
                'status': status,
                'best_score': best_score,
                'best_badge': best_badge,
                'attempts': attempts,
                'last_attempt': last_attempt
            }
        
        logger.info(f"Progress retrieved - student={student_id}, skill={skill_id}")
        
        return jsonify({
            'skill_id': skill_id,
            'skill_name': skill.name,
            'progress': progress
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_progress: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@assessments_bp.route('/available', methods=['GET'])
@token_required
def get_available_skills() -> Tuple[Dict[str, Any], int]:
    """
    Get list of all available skills for assessment
    
    Response:
    {
        "skills": [
            {
                "id": int,
                "name": str,
                "category": str,
                "description": str,
                "industry_benchmark": int
            },
            ...
        ],
        "total": int
    }
    """
    try:
        db = get_db()
        token = request.headers.get('Authorization', '').split(' ')[-1]
        student_id = get_current_user(token)
        
        if not student_id:
            logger.warning("Unauthorized available skills request")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Get all skills
        skills = (
            db.query(SkillsTaxonomy)
            .order_by(SkillsTaxonomy.category, SkillsTaxonomy.name)
            .all()
        )
        
        skills_data = [
            {
                'id': skill.id,
                'name': skill.name,
                'category': skill.category,
                'description': skill.description,
                'industry_benchmark': skill.industry_benchmark
            }
            for skill in skills
        ]
        
        logger.info(f"Available skills retrieved - student={student_id}, count={len(skills_data)}")
        
        return jsonify({
            'skills': skills_data,
            'total': len(skills_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in get_available_skills: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
