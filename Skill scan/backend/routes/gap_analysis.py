"""
Gap Analysis Routes Blueprint
Flask blueprint for skill gap analysis endpoints with authorization and error handling.
"""

import logging
from typing import Dict, Tuple, Any
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import and_
from models import Student, SkillsTaxonomy, SkillScore, db
from utils.auth import token_required
from utils.gap_analyzer import GapAnalyzer

gap_analysis_bp = Blueprint('gap_analysis', __name__)
logger = logging.getLogger(__name__)

# Initialize gap analyzer
gap_analyzer = GapAnalyzer()


def _get_current_user_from_token(current_user: Dict[str, Any]) -> Student:
    """
    Extract and validate current user from token payload.
    
    Args:
        current_user (Dict): Token payload with user_id
    
    Returns:
        Student: Student object
    
    Raises:
        ValueError: If user not found
    """
    user_id = current_user.get('user_id')
    user = Student.query.get(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")
    return user


def _validate_skill_exists(skill_id: int) -> SkillsTaxonomy:
    """
    Validate that skill exists in database.
    
    Args:
        skill_id (int): Skill ID to validate
    
    Returns:
        SkillsTaxonomy: Skill object
    
    Raises:
        ValueError: If skill not found
    """
    skill = SkillsTaxonomy.query.get(skill_id)
    if not skill:
        raise ValueError(f"Skill {skill_id} not found")
    return skill


@gap_analysis_bp.route('/<int:skill_id>', methods=['GET'])
@token_required
def get_gap_analysis(current_user: Dict[str, Any], skill_id: int) -> Tuple[Dict, int]:
    """
    Get gap analysis for a specific skill.
    
    Endpoint: GET /gap-analysis/<skill_id>
    
    Authorization: Requires valid JWT token
    
    Args:
        current_user (Dict): Token payload
        skill_id (int): Skill ID to analyze
    
    Returns:
        Tuple[Dict, int]: Response JSON and HTTP status code
        
        Success (200):
        {
            'status': 'success',
            'skill_id': int,
            'skill_name': str,
            'current_score': float,
            'benchmark': {
                'industry_avg': float,
                'percentile': int
            },
            'gaps_identified': List[Dict],
            'priority_gaps': List[Dict],
            'gap_status': str
        }
        
        Error responses:
        - 404: Skill not found
        - 403: Unauthorized access
        - 500: Server error
    """
    try:
        user = _get_current_user_from_token(current_user)
        skill = _validate_skill_exists(skill_id)
        
        logger.info(f"User {user.id} requesting gap analysis for skill {skill_id}")
        
        # Generate gap report
        report = gap_analyzer.generate_gap_report(user.id, skill_id)
        
        if 'error' in report:
            if report.get('status') == 404:
                logger.warning(f"Skill {skill_id} not found")
                return jsonify({
                    'status': 'error',
                    'code': 404,
                    'message': f'Skill {skill_id} not found'
                }), 404
            else:
                logger.error(f"Error generating report: {report['error']}")
                return jsonify({
                    'status': 'error',
                    'code': 500,
                    'message': 'Error generating gap analysis'
                }), 500
        
        # Extract priority gaps (top 3)
        priority_gaps = []
        if report.get('gaps_identified'):
            priority_gaps = sorted(
                report['gaps_identified'],
                key=lambda x: x.get('priority', 0),
                reverse=True
            )[:3]
            priority_gaps = [
                {
                    'name': gap['name'],
                    'priority': gap['priority'],
                    'action': f"Focus on {gap['name']} - appears in {gap['frequency_percentage']:.0f}% of assessments"
                }
                for gap in priority_gaps
            ]
        
        response = {
            'status': 'success',
            'code': 200,
            'skill_id': report['skill_id'],
            'skill_name': report['skill_name'],
            'skill_category': report.get('skill_category'),
            'current_score': report['current_score'],
            'gap_status': report.get('gap_status'),
            'benchmark': {
                'industry_avg': report['benchmark_score'],
                'percentile': report['percentile']
            },
            'gaps_identified': report['gaps_identified'],
            'priority_gaps': priority_gaps,
            'improvement_potential': report['improvement_potential']
        }
        
        logger.info(f"Gap analysis completed for user {user.id}, skill {skill_id}")
        return jsonify(response), 200
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        if "not found" in str(e).lower():
            return jsonify({
                'status': 'error',
                'code': 404,
                'message': str(e)
            }), 404
        return jsonify({
            'status': 'error',
            'code': 403,
            'message': str(e)
        }), 403
    
    except Exception as e:
        logger.error(f"Unexpected error in get_gap_analysis: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500


@gap_analysis_bp.route('/report', methods=['GET'])
@token_required
def get_gap_report(current_user: Dict[str, Any]) -> Tuple[Dict, int]:
    """
    Get comprehensive gap report for all skills.
    
    Endpoint: GET /gap-analysis/report
    
    Authorization: Requires valid JWT token
    
    Args:
        current_user (Dict): Token payload
    
    Returns:
        Tuple[Dict, int]: Response JSON and HTTP status code
        
        Success (200):
        {
            'status': 'success',
            'summary': {
                'total_gaps': int,
                'avg_score': float,
                'weakest_skill': str,
                'skills_analyzed': int
            },
            'by_skill': [
                {
                    'skill_id': int,
                    'skill_name': str,
                    'score': float,
                    'gap_status': str,
                    'gaps': int,
                    'priority': float
                },
                ...
            ]
        }
    """
    try:
        user = _get_current_user_from_token(current_user)
        logger.info(f"User {user.id} requesting comprehensive gap report")
        
        # Get all skills with scores for this user
        user_skill_scores = db.session.query(
            SkillScore.skill_id,
            db.func.max(SkillScore.score).label('best_score'),
            db.func.count(SkillScore.id).label('assessment_count')
        ).filter(
            SkillScore.student_id == user.id
        ).group_by(
            SkillScore.skill_id
        ).all()
        
        if not user_skill_scores:
            logger.info(f"No assessment history for user {user.id}")
            return jsonify({
                'status': 'success',
                'code': 200,
                'message': 'No assessment history',
                'summary': {
                    'total_gaps': 0,
                    'avg_score': 0,
                    'weakest_skill': None,
                    'skills_analyzed': 0
                },
                'by_skill': []
            }), 200
        
        # Analyze each skill
        skill_reports = []
        all_gaps_count = 0
        all_scores = []
        
        for skill_score in user_skill_scores:
            skill_id = skill_score.skill_id
            skill = SkillsTaxonomy.query.get(skill_id)
            if not skill:
                continue
            
            # Generate report for this skill
            report = gap_analyzer.generate_gap_report(user.id, skill_id)
            
            if 'error' in report:
                continue
            
            gaps_count = len(report.get('gaps_identified', []))
            all_gaps_count += gaps_count
            all_scores.append(report['current_score'])
            
            skill_report = {
                'skill_id': skill_id,
                'skill_name': report['skill_name'],
                'category': report.get('skill_category'),
                'score': report['current_score'],
                'benchmark': report['benchmark_score'],
                'gap_status': report.get('gap_status'),
                'gaps': gaps_count,
                'percentile': report['percentile'],
                'priority': report['gaps_identified'][0]['priority'] if report['gaps_identified'] else 0
            }
            skill_reports.append(skill_report)
        
        # Sort by priority (gaps first)
        skill_reports.sort(key=lambda x: (x['gaps'] > 0, x['priority']), reverse=True)
        
        # Calculate summary
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        weakest_skill = skill_reports[0]['skill_name'] if skill_reports else None
        
        response = {
            'status': 'success',
            'code': 200,
            'summary': {
                'total_gaps': all_gaps_count,
                'avg_score': avg_score,
                'weakest_skill': weakest_skill,
                'skills_analyzed': len(skill_reports)
            },
            'by_skill': skill_reports
        }
        
        logger.info(f"Generated comprehensive report for user {user.id}: {len(skill_reports)} skills, {all_gaps_count} gaps")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error generating gap report: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Error generating report'
        }), 500


@gap_analysis_bp.route('/<int:skill_id>/benchmarks', methods=['GET'])
@token_required
def get_benchmarks(current_user: Dict[str, Any], skill_id: int) -> Tuple[Dict, int]:
    """
    Get benchmark comparison for a skill.
    
    Endpoint: GET /gap-analysis/<skill_id>/benchmarks
    
    Authorization: Requires valid JWT token
    
    Args:
        current_user (Dict): Token payload
        skill_id (int): Skill ID
    
    Returns:
        Tuple[Dict, int]: Response JSON and HTTP status code
        
        Success (200):
        {
            'status': 'success',
            'skill_id': int,
            'skill_name': str,
            'benchmarks': {
                'industry_average': float,
                'expert_level': float (90%),
                'good_level': float (80%),
                'fair_level': float (60%),
                'beginner_level': float (0%)
            },
            'student_performance': {
                'score': float,
                'rank': str,
                'percentile': int
            }
        }
    """
    try:
        user = _get_current_user_from_token(current_user)
        skill = _validate_skill_exists(skill_id)
        
        logger.info(f"User {user.id} requesting benchmarks for skill {skill_id}")
        
        # Get current score
        best_score = db.session.query(
            db.func.max(SkillScore.score)
        ).filter(
            and_(
                SkillScore.student_id == user.id,
                SkillScore.skill_id == skill_id
            )
        ).scalar()
        
        current_score = (best_score * 10) if best_score else 0
        
        # Get benchmarks
        industry_avg = gap_analyzer.get_industry_benchmark(skill_id)
        percentile = gap_analyzer.calculate_percentile(user.id, skill_id, best_score or 0)
        
        # Determine rank
        if current_score >= 90:
            rank = 'Expert'
        elif current_score >= 80:
            rank = 'Good'
        elif current_score >= 60:
            rank = 'Fair'
        else:
            rank = 'Beginner'
        
        response = {
            'status': 'success',
            'code': 200,
            'skill_id': skill_id,
            'skill_name': skill.name,
            'benchmarks': {
                'industry_average': industry_avg,
                'expert_level': 90,
                'good_level': 80,
                'fair_level': 60,
                'beginner_level': 0
            },
            'student_performance': {
                'score': current_score,
                'rank': rank,
                'percentile': percentile
            }
        }
        
        logger.info(f"Benchmark comparison completed for user {user.id}, skill {skill_id}")
        return jsonify(response), 200
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 404,
            'message': str(e)
        }), 404
    
    except Exception as e:
        logger.error(f"Error getting benchmarks: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500


@gap_analysis_bp.route('/trends', methods=['GET'])
@token_required
def get_trends(current_user: Dict[str, Any]) -> Tuple[Dict, int]:
    """
    Get historical gap progression trends for all skills.
    
    Endpoint: GET /gap-analysis/trends
    
    Authorization: Requires valid JWT token
    
    Args:
        current_user (Dict): Token payload
    
    Returns:
        Tuple[Dict, int]: Response JSON and HTTP status code
        
        Success (200):
        {
            'status': 'success',
            'trends': [
                {
                    'skill_id': int,
                    'skill_name': str,
                    'trend': str ('improving', 'stable', 'worsening'),
                    'change': float,
                    'progression': List[{score, date}]
                },
                ...
            ]
        }
    """
    try:
        user = _get_current_user_from_token(current_user)
        logger.info(f"User {user.id} requesting gap progression trends")
        
        # Get all skills with history for this user
        user_skills = db.session.query(
            SkillScore.skill_id
        ).filter(
            SkillScore.student_id == user.id
        ).distinct().all()
        
        if not user_skills:
            logger.info(f"No skill history for user {user.id}")
            return jsonify({
                'status': 'success',
                'code': 200,
                'trends': []
            }), 200
        
        # Track progression for each skill
        trends = []
        for (skill_id,) in user_skills:
            skill = SkillsTaxonomy.query.get(skill_id)
            if not skill:
                continue
            
            progression = gap_analyzer.track_gap_progression(user.id, skill_id)
            
            if progression.get('trend') != 'error':
                trend_data = {
                    'skill_id': skill_id,
                    'skill_name': skill.name,
                    'trend': progression.get('trend'),
                    'change': progression.get('change', 0),
                    'assessments': progression.get('assessments', 0),
                    'first_score': progression.get('first_score', 0),
                    'latest_score': progression.get('latest_score', 0)
                }
                
                # Only include progression if we have data
                if progression.get('progression'):
                    trend_data['progression'] = progression['progression']
                
                trends.append(trend_data)
        
        # Sort by most improved
        trends.sort(key=lambda x: x['change'], reverse=True)
        
        response = {
            'status': 'success',
            'code': 200,
            'summary': {
                'total_skills_tracked': len(trends),
                'improving': sum(1 for t in trends if t['trend'] == 'improving'),
                'stable': sum(1 for t in trends if t['trend'] == 'stable'),
                'worsening': sum(1 for t in trends if t['trend'] == 'worsening')
            },
            'trends': trends
        }
        
        logger.info(f"Trends report generated for user {user.id}: {len(trends)} skills tracked")
        return jsonify(response), 200
    
    except Exception as e:
        logger.error(f"Error getting trends: {str(e)}")
        return jsonify({
            'status': 'error',
            'code': 500,
            'message': 'Internal server error'
        }), 500


@gap_analysis_bp.errorhandler(404)
def not_found_error(error) -> Tuple[Dict, int]:
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'code': 404,
        'message': 'Endpoint not found'
    }), 404


@gap_analysis_bp.errorhandler(500)
def internal_error(error) -> Tuple[Dict, int]:
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'status': 'error',
        'code': 500,
        'message': 'Internal server error'
    }), 500
