"""
Assessment Scoring & Feedback Generation Module

Handles assessment submission validation, AI-powered scoring,
gap identification, and feedback generation for SkillScan MVP.

Author: SkillScan Team
Date: 2026-04-15
"""

import logging
import json
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from backend.utils.model_client import GeminiClient
from backend.models import (
    Assessment, AssessmentResponse, SkillScore, 
    StudentSkills, Skills
)
from backend.database import db

logger = logging.getLogger(__name__)


@dataclass
class ScoringResult:
    """Data class for assessment scoring results"""
    score: int
    feedback: str
    gaps_identified: List[str]
    badge: str
    confidence: float
    detailed_feedback: Dict[str, Any]
    recommendations: List[Dict[str, str]]


class AssessmentScorer:
    """Handles assessment submission and AI-powered scoring"""
    
    # Score to badge mapping
    BADGE_MAPPING = {
        'Excellent': (90, 100),
        'Good': (80, 89),
        'Fair': (70, 79),
        'Needs Work': (0, 69)
    }
    
    # Passing score threshold
    PASSING_SCORE = 70
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        """
        Initialize scorer with Gemini client
        
        Args:
            gemini_client: GeminiClient instance for AI scoring
        """
        self.gemini_client = gemini_client or GeminiClient()
        logger.info("AssessmentScorer initialized")
    
    def validate_submission(
        self, 
        assessment_id: int,
        responses: Dict[str, Any],
        student_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate assessment submission
        
        Args:
            assessment_id: ID of assessment being submitted
            responses: User's responses/answers
            student_id: ID of student submitting
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check assessment exists
            assessment = Assessment.query.get(assessment_id)
            if not assessment:
                error = f"Assessment {assessment_id} not found"
                logger.warning(f"Validation failed: {error}")
                return False, error
            
            # Check responses provided
            if not responses or len(responses) == 0:
                error = "No responses provided"
                logger.warning(f"Validation failed: {error}")
                return False, error
            
            # Check response format based on assessment type
            assessment_type = assessment.assessment_type
            
            if assessment_type == 'mcq':
                # MCQ: should have selected_options dict
                if 'selected_options' not in responses:
                    return False, "Missing selected_options in responses"
                if not isinstance(responses['selected_options'], dict):
                    return False, "selected_options must be a dictionary"
            
            elif assessment_type == 'coding':
                # Coding: should have solutions list
                if 'solutions' not in responses:
                    return False, "Missing solutions in responses"
                if not isinstance(responses['solutions'], list):
                    return False, "solutions must be a list"
            
            elif assessment_type == 'casestudy':
                # Case Study: should have answers dict
                if 'answers' not in responses:
                    return False, "Missing answers in responses"
                if not isinstance(responses['answers'], dict):
                    return False, "answers must be a dictionary"
            
            logger.info(f"Validation passed for assessment {assessment_id}")
            return True, None
            
        except Exception as e:
            error = f"Validation error: {str(e)}"
            logger.error(f"Validation failed: {error}")
            return False, error
    
    def score_assessment(
        self,
        assessment: Assessment,
        responses: Dict[str, Any]
    ) -> ScoringResult:
        """
        Score assessment using Gemini AI
        
        Args:
            assessment: Assessment object with questions
            responses: User's responses
            
        Returns:
            ScoringResult with score, feedback, gaps, badge
        """
        try:
            logger.info(f"Starting assessment scoring for assessment {assessment.id}")
            
            # Call Gemini to score assessment
            questions_data = json.loads(assessment.questions) if isinstance(assessment.questions, str) else assessment.questions
            
            scoring_response = self.gemini_client.score_assessment(
                assessment_type=assessment.assessment_type,
                difficulty=assessment.difficulty,
                skill_id=assessment.skill_id,
                questions=questions_data,
                responses=responses
            )
            
            logger.info(f"Gemini scoring response received: {scoring_response}")
            
            # Parse Gemini response
            score = int(scoring_response.get('score', 0))
            feedback = scoring_response.get('feedback', 'Assessment completed.')
            gaps = scoring_response.get('gaps_identified', [])
            confidence = float(scoring_response.get('confidence', 0.8))
            detailed_feedback = scoring_response.get('detailed_feedback', {})
            
            # Determine badge
            badge = self._get_badge(score)
            
            # Generate recommendations based on gaps
            recommendations = self._generate_recommendations(
                gaps=gaps,
                skill_id=assessment.skill_id,
                difficulty=assessment.difficulty
            )
            
            logger.info(f"Assessment scored: {score}%, badge: {badge}, gaps: {len(gaps)}")
            
            return ScoringResult(
                score=score,
                feedback=feedback,
                gaps_identified=gaps,
                badge=badge,
                confidence=confidence,
                detailed_feedback=detailed_feedback,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error scoring assessment: {str(e)}")
            # Return default failing score
            return ScoringResult(
                score=0,
                feedback=f"Error scoring assessment: {str(e)}",
                gaps_identified=["Unable to evaluate - please retry"],
                badge="Needs Work",
                confidence=0.0,
                detailed_feedback={},
                recommendations=[]
            )
    
    def _get_badge(self, score: int) -> str:
        """
        Get badge based on score
        
        Args:
            score: Score (0-100)
            
        Returns:
            Badge name
        """
        for badge, (min_score, max_score) in self.BADGE_MAPPING.items():
            if min_score <= score <= max_score:
                return badge
        return "Needs Work"
    
    def _generate_recommendations(
        self,
        gaps: List[str],
        skill_id: int,
        difficulty: str
    ) -> List[Dict[str, str]]:
        """
        Generate learning recommendations based on gaps
        
        Args:
            gaps: List of identified gap areas
            skill_id: ID of skill being assessed
            difficulty: Difficulty level
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            
            # Get skill name
            skill = Skills.query.get(skill_id)
            skill_name = skill.skill_name if skill else "Unknown"
            
            # For each gap, generate recommendations
            for i, gap in enumerate(gaps[:3]):  # Top 3 gaps
                rec = {
                    "gap": gap,
                    "resource_type": ["Online Course", "YouTube Tutorial", "Book", "Project"][i % 4],
                    "priority": ["High", "Medium", "Low"][i % 3],
                    "estimated_time": ["2-3 weeks", "1-2 weeks", "3-5 days"][i % 3]
                }
                recommendations.append(rec)
            
            logger.info(f"Generated {len(recommendations)} recommendations for gaps")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    def save_assessment_response(
        self,
        student_id: int,
        assessment_id: int,
        responses: Dict[str, Any],
        scoring_result: ScoringResult
    ) -> Optional[AssessmentResponse]:
        """
        Save assessment response and score to database
        
        Args:
            student_id: Student ID
            assessment_id: Assessment ID
            responses: User responses
            scoring_result: Scoring result
            
        Returns:
            AssessmentResponse object or None if failed
        """
        try:
            # Create assessment response record
            assessment_response = AssessmentResponse(
                student_id=student_id,
                assessment_id=assessment_id,
                responses=json.dumps(responses),
                score=scoring_result.score,
                feedback=scoring_result.feedback,
                gaps=json.dumps(scoring_result.gaps_identified),
                badge=scoring_result.badge,
                submitted_at=datetime.utcnow()
            )
            
            db.session.add(assessment_response)
            
            # Update skill score record
            assessment = Assessment.query.get(assessment_id)
            skill_score = SkillScore.query.filter_by(
                student_id=student_id,
                skill_id=assessment.skill_id
            ).first()
            
            if skill_score:
                # Update existing score
                skill_score.score = max(skill_score.score, scoring_result.score)
                skill_score.last_assessed = datetime.utcnow()
                skill_score.proficiency = self._calculate_proficiency(scoring_result.score)
            else:
                # Create new score record
                skill_score = SkillScore(
                    student_id=student_id,
                    skill_id=assessment.skill_id,
                    score=scoring_result.score,
                    proficiency=self._calculate_proficiency(scoring_result.score),
                    last_assessed=datetime.utcnow()
                )
                db.session.add(skill_score)
            
            db.session.commit()
            logger.info(f"Assessment response saved: {assessment_response.id}")
            return assessment_response
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving assessment response: {str(e)}")
            return None
    
    def _calculate_proficiency(self, score: int) -> str:
        """
        Calculate proficiency level from score
        
        Args:
            score: Score (0-100)
            
        Returns:
            Proficiency level string
        """
        if score >= 90:
            return "Expert"
        elif score >= 80:
            return "Advanced"
        elif score >= 70:
            return "Intermediate"
        elif score >= 50:
            return "Beginner"
        else:
            return "Novice"
    
    def check_unlock_progression(
        self,
        student_id: int,
        skill_id: int,
        current_difficulty: str,
        score: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if score unlocks next difficulty level
        
        Args:
            student_id: Student ID
            skill_id: Skill ID
            current_difficulty: Current difficulty level
            score: Assessment score
            
        Returns:
            Tuple of (unlocked, next_difficulty)
        """
        try:
            # Define difficulty progression
            difficulty_order = ['easy', 'medium', 'hard']
            
            if current_difficulty not in difficulty_order:
                return False, None
            
            # Check if score passes threshold
            if score < self.PASSING_SCORE:
                logger.info(f"Score {score} below threshold {self.PASSING_SCORE} - no unlock")
                return False, None
            
            # Check if there's a next difficulty
            current_index = difficulty_order.index(current_difficulty)
            if current_index >= len(difficulty_order) - 1:
                logger.info(f"Already at highest difficulty: {current_difficulty}")
                return False, None
            
            next_difficulty = difficulty_order[current_index + 1]
            logger.info(f"Progression unlock: {current_difficulty} → {next_difficulty}")
            
            return True, next_difficulty
            
        except Exception as e:
            logger.error(f"Error checking unlock progression: {str(e)}")
            return False, None
    
    def get_assessment_history(
        self,
        student_id: int,
        skill_id: int,
        limit: int = 10
    ) -> List[AssessmentResponse]:
        """
        Get assessment history for student and skill
        
        Args:
            student_id: Student ID
            skill_id: Skill ID
            limit: Maximum records to return
            
        Returns:
            List of AssessmentResponse objects
        """
        try:
            history = AssessmentResponse.query.join(Assessment).filter(
                AssessmentResponse.student_id == student_id,
                Assessment.skill_id == skill_id
            ).order_by(AssessmentResponse.submitted_at.desc()).limit(limit).all()
            
            logger.info(f"Retrieved {len(history)} assessment records for student {student_id}, skill {skill_id}")
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving assessment history: {str(e)}")
            return []
    
    def get_best_score(self, student_id: int, skill_id: int) -> Optional[int]:
        """
        Get best score for student and skill
        
        Args:
            student_id: Student ID
            skill_id: Skill ID
            
        Returns:
            Best score or None
        """
        try:
            score_record = SkillScore.query.filter_by(
                student_id=student_id,
                skill_id=skill_id
            ).first()
            
            if score_record:
                return score_record.score
            return None
            
        except Exception as e:
            logger.error(f"Error getting best score: {str(e)}")
            return None
